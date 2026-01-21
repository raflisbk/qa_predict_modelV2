"""Test script to verify post-processing fixes calculation errors.

This script tests the updated summarizer with the same input that
previously produced incorrect calculations.
"""

import sys
sys.path.insert(0, 'd:/Subek/project/Draft/UKI/DIGIMAR/Best time post v2/Summarization/inference')

from summarizer import Summarizer

# Test data from user's training output
test_input = {
    "day": "Saturday",
    "time_window": "09:00 - 12:00",
    "score": 79,
    "daily_avg": 55.7,
    "peak_hour": 9,
    "peak_value": 97,
    "hourly": "01(30), 01(37), 02(28), 02(32), 03(30), 03(35), 04(37), 04(33), 05(44), 05(50), 06(48), 06(59), 07(65), 07(69), 08(84), 08(89), 09(97), 09(80), 10(84), 10(71), 11(77), 11(66), 12(73), 12(57), 13(77), 13(63), 14(74), 14(65), 15(59), 15(71), 16(63), 16(58), 17(59), 17(53), 18(50), 18(55), 19(54), 19(46), 20(50), 20(43), 21(50), 21(44), 22(43), 22(38), 23(34), 23(38)",
    "window_avg": 79  # Average for 09:00-12:00 window
}

print("=" * 70)
print("POST-PROCESSING VERIFICATION TEST")
print("=" * 70)

print("\n📊 INPUT DATA:")
print(f"  Day: {test_input['day']}")
print(f"  Time Window: {test_input['time_window']}")
print(f"  Score: {test_input['score']}")
print(f"  Peak: {test_input['peak_hour']:02d}:00 ({test_input['peak_value']})")
print(f"  Daily Avg: {test_input['daily_avg']}")

print("\n🧮 EXPECTED CALCULATIONS:")
peak_pct = ((test_input['peak_value'] - test_input['daily_avg']) / test_input['daily_avg']) * 100
print(f"  Peak vs Daily Avg: +{peak_pct:.0f}%")
print(f"  (Calculation: ({test_input['peak_value']} - {test_input['daily_avg']}) / {test_input['daily_avg']} × 100)")

print("\n🤖 GENERATING SUMMARY WITH POST-PROCESSING...")
print("-" * 70)

try:
    summarizer = Summarizer()
    generated = summarizer.generate(test_input)
    
    print("\n✅ GENERATED OUTPUT:")
    print(generated)
    
    print("\n" + "=" * 70)
    print("VERIFICATION CHECKLIST:")
    print("=" * 70)
    
    # Check if peak percentage is correct
    if "+74%" in generated or "+73%" in generated:
        print("✅ Peak percentage: CORRECT (+74%)")
    elif "+27%" in generated:
        print("❌ Peak percentage: STILL WRONG (+27%)")
    else:
        print("⚠️  Peak percentage: Could not verify")
    
    # Check if comparison values are not all 55.7
    if generated.count("55.7") <= 2:  # Should appear max 2 times (daily avg mentions)
        print("✅ Comparison values: FIXED (not all 55.7)")
    else:
        print("❌ Comparison values: STILL HALLUCINATING (all 55.7)")
    
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
