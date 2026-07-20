"""Accessibility-tree (uiautomator) grounding backend.

A *free, deterministic* alternative to the Holo grounding model
(a_test.grounding) for the two-tier CUA loop. Instead of asking a remote
grounding model to localise an element, it resolves the planner's natural
language `target` description against the live uiautomator UI hierarchy and
returns the centre of the best-matching node's bounds.

Why this exists: general vision planners (GPT-4o class) are unreliable at
emitting exact tap pixel coordinates on tall phone screens -- they miss by
100-200px, tapping the wrong row. Native Android apps (including Jetpack
Compose, which exposes Text/contentDescription to the a11y tree) publish exact
element bounds via `uiautomator dump`. Matching the planner's element
description to those bounds gives pixel-perfect taps for free.

Wired into a_test.loop.run_cua_step's `grounding_fn` parameter, same contract
as make_grounding_fn (Holo): callable(image_b64, description, w, h) -> (x, y).

When no a11y node matches (e.g. an unlabelled icon button), it optionally falls
back to a focused single-element vision call using the provided planner client,
which is more accurate than inline coordinate guessing because the model only
has to localise one named element, not also plan.
"""
import json
import re
import time
import xml.etree.ElementTree as ET

from .android import ui_dump, _bounds_center

# Generic UI words that carry no disambiguating signal -- stripped from the
# target description before token matching so "the Submit button" matches a node
# whose text is just "Submit".
_STOPWORDS = {
    "the", "a", "an", "to", "on", "of", "in", "for", "and", "or", "with",
    "tap", "click", "press", "select", "choose", "open", "button", "btn",
    "icon", "link", "option", "menu", "item", "card", "tile", "field",
    "label", "text", "toggle", "switch", "checkbox", "entry", "row", "cell",
    "element", "control", "area", "screen", "view", "chevron", "arrow",
}
# Position hints -- kept out of the core token match (they describe *where*, not
# *what*) but used as a soft tie-breaker.
_POSITION = {
    "top", "bottom", "left", "right", "center", "centre", "upper", "lower",
    "corner", "header", "footer", "first", "second", "third", "last", "next",
    "above", "below", "beside", "near",
}


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", " ", (s or "").lower()).strip()


def _tokens(s: str) -> list:
    return [t for t in _norm(s).split() if t]


def _content_tokens(s: str) -> set:
    return {t for t in _tokens(s) if t not in _STOPWORDS and t not in _POSITION}


def _iter_nodes(xml: str):
    """Yield (attrib_dict) for every node element in a uiautomator dump."""
    try:
        root = ET.fromstring(xml)
    except ET.ParseError:
        return
    for node in root.iter("node"):
        yield node.attrib


def _score(target_tokens: set, node_text: str) -> float:
    """Score how well a node's text/desc matches the target description.

    Rewards two-way containment: the target naming the node ("Daily Draw" for a
    'Daily Draw' node) and the node's label appearing in the target. Uses token
    coverage so word order and extra qualifiers don't break the match.
    """
    node_tokens = _content_tokens(node_text)
    if not node_tokens or not target_tokens:
        return 0.0
    overlap = target_tokens & node_tokens
    if not overlap:
        return 0.0
    # Coverage of the node's own label by the target (did the planner name this
    # element?) and coverage of the target by the node.
    node_cov = len(overlap) / len(node_tokens)
    tgt_cov = len(overlap) / len(target_tokens)
    score = 0.6 * node_cov + 0.4 * tgt_cov
    # Exact normalised equality is the strongest signal.
    if _norm(node_text) and _norm(node_text) in " ".join(sorted(target_tokens | overlap)):
        score += 0.15
    return score


def _best_match(xml: str, description: str):
    """Return (x, y, matched_label, score) for the best a11y node, or None."""
    target_tokens = _content_tokens(description)
    if not target_tokens:
        return None
    norm_desc = _norm(description)
    desc_words = norm_desc.split()
    best = None
    for attr in _iter_nodes(xml):
        label = attr.get("text") or attr.get("content-desc") or ""
        if not label.strip():
            continue
        # Only consider the first line of long text blocks (reading bodies dump
        # their entire content into one Text node -- match its heading, not the
        # whole paragraph, and never tap a giant scroll body by accident).
        first_line = label.splitlines()[0] if label else label
        s = max(_score(target_tokens, label), _score(target_tokens, first_line))
        if s <= 0:
            continue
        center = _bounds_center(attr.get("bounds", ""))
        if center is None:
            continue
        x1y1x2y2 = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", attr.get("bounds", ""))
        area = 1
        if x1y1x2y2:
            a, b, c, d = map(int, x1y1x2y2.groups())
            area = max(1, (c - a) * (d - b))
        clickable = attr.get("clickable") == "true"
        # Earliest-mention tie-break: the primary target is usually named first
        # in the description ("the 'Scan Physical Card' card above 'Scan From
        # Gallery'"), so a label mentioned earlier beats one mentioned only as a
        # positional reference. Position in [0,1], earlier -> larger boost.
        node_tok = _content_tokens(label)
        first_pos = min((desc_words.index(t) for t in node_tok if t in desc_words),
                        default=len(desc_words))
        early_boost = 0.08 * (1 - first_pos / max(1, len(desc_words)))
        # Prefer clickable nodes and smaller, more specific targets on ties.
        adj = s + (0.05 if clickable else 0.0) + early_boost - min(area / (1080 * 2340), 0.1) * 0.2
        if best is None or adj > best[0]:
            best = (adj, s, center[0], center[1], first_line.strip()[:40])
    if best is None:
        return None
    adj, raw, x, y, label = best
    if raw < 0.34:  # too weak -- treat as no match, let the fallback decide
        return None
    return (x, y, label, raw)


def make_a11y_grounding_fn(client=None, model: str = None, min_score: float = 0.34,
                           verbose: bool = True):
    """Build a grounding_fn(image_b64, description, w, h) -> (x, y).

    Resolves taps against the live uiautomator hierarchy. If no node matches and
    a planner `client`/`model` is provided, falls back to a focused single
    element vision-localisation call. Raises ValueError when it cannot resolve a
    coordinate (the loop treats that like a skipped step, per the grounding
    contract).
    """

    def _vision_fallback(image_b64: str, description: str, w: int, h: int):
        if client is None or model is None:
            raise ValueError(f"a11y: no node matched '{description}' and no vision fallback client")
        prompt = (
            f"The screen is {w}x{h} pixels. Return ONLY JSON "
            '{"x": <int>, "y": <int>} for the pixel coordinate at the CENTER of '
            f"this element: {description}. No other text."
        )
        msg = [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}", "detail": "high"}},
            ],
        }]
        resp = client.chat.completions.create(model=model, messages=msg)
        raw = resp.choices[0].message.content.strip()
        m = re.search(r"\{[^}]*\}", raw)
        if not m:
            raise ValueError(f"a11y vision fallback returned no JSON for '{description}': {raw[:80]}")
        data = json.loads(m.group(0))
        x, y = int(data["x"]), int(data["y"])
        x = max(0, min(w - 1, x))
        y = max(0, min(h - 1, y))
        if verbose:
            print(f"  [a11y grounding] vision-fallback '{description}' -> ({x}, {y})")
        return x, y

    def _grounding_fn(image_b64: str, description: str, w: int, h: int):
        # uiautomator can momentarily fail mid-animation; retry a couple times.
        xml = ""
        for _ in range(3):
            xml = ui_dump()
            if xml:
                break
            time.sleep(0.6)
        match = _best_match(xml, description) if xml else None
        if match is not None:
            x, y, label, score = match
            if verbose:
                print(f"  [a11y grounding] '{description}' -> node '{label}' ({x}, {y}) score={score:.2f}")
            return x, y
        return _vision_fallback(image_b64, description, w, h)

    return _grounding_fn
