"""Android CUA test: Calculator performs arithmetic.

Demonstrates the agent solving a real problem — computing 27 + 18,
not just verifying static UI. This shows CUA can drive multi-step interactions.
"""
from agentprobe import TestCase, run_case

case = TestCase(
    name="calculator_math",
    package="com.android.calculator2",
    instruction=(
        "The Calculator app has been launched. "
        "Your task: compute 27 + 18 using the keypad, then verify the result. "
        "Steps: "
        "1. Tap the digit 2, then 7 to enter 27. "
        "2. Tap the plus (+) operator button. "
        "3. Tap the digit 1, then 8 to enter 18. "
        "4. Tap the equals (=) button to compute. "
        "5. Verify the result 45 is displayed on screen. "
        "Taps can occasionally miss their target on a touchscreen -- this is normal. "
        "After each tap, check the display: if it shows a digit or operator you did "
        "not intend, tap DEL (or the clear/AC button) to remove the mistaken entry, "
        "then retap the correct button and continue from where you left off. "
        "Do not give up over a single misfired tap -- only report TEST_FAILED if the "
        "app crashes, shows an error dialog, or you are unable to reach the correct "
        "final result of 45 after several correction attempts. "
        "Report TEST_PASSED once 45 appears on the display as the final result."
    ),
    successCriteria=[
        "The number 45 is displayed on the calculator screen",
        "The calculation 27 + 18 was completed successfully",
    ],
    failureCriteria=[
        "App crashes or shows an error dialog",
        "The final result after pressing equals is not 45",
        "The equals button press did not trigger any calculation",
    ],
    maxSteps=25,
)

if __name__ == "__main__":
    result = run_case(case, output_dir="/tmp/agentprobe-output")
    print(f"Verdict: {result['verdict']} -- {result.get('reason', '')}")
    assert result["verdict"] == "pass", f"Test failed: {result.get('reason')}"
