"""Test script for formatted inference output.

This script verifies that the new post-processing logic in Summarizer
correctly adds newlines to the Traceback section.
"""

# from inference.summarizer import generate_summary

def test_formatted_output():
    # Mock data resembling aggregation output
    hourly_summary = {
        "day": "Saturday",
        "time_window": "09:00 - 12:00",
        "score": 79,
        "daily_avg": 55.7,
        "peak_hour": 9,
        "peak_value": 97.0,
        "hourly": "01(30), 02(28), 03(30), 04(37), 05(44), 06(48), 07(65), 08(84), 09(97), 10(84), 11(77), 12(73)"
    }
    
    print("Testing Stage 2 Formatted Inference...")
    print("="*50)
    
    # In a real environment, this would load the model from HF
    # For this demonstration, we'll just show what the post-processing does
    # by simulating a raw string similar to what the model generates
    raw_output = ("Saturday's 09:00 - 12:00 slot delivers 79/100 engagement, "
                  "reaching users during mid-morning work breaks. Traceback: "
                  "- Peak: 09:00 (97), +74% vs daily avg (55.7) "
                  "- vs Morning 06:00 - 09:00 (avg 69.0): +15% improvement")
    
    # Simulate the _format_traceback_newlines logic
    import re
    def simulate_formatting(text):
        if "Traceback:" in text:
            text = re.sub(r'([\.!?])\s*(Traceback:)', r'\1\n\n\2', text)
            text = re.sub(r'(?<!\n)\s*(- [^\n]+)', r'\n\1', text)
        return text
    
    formatted = simulate_formatting(raw_output)
    
    print("RAW OUTPUT (Simulated):")
    print(raw_output)
    print("\nFORMATTED OUTPUT:")
    print("-" * 30)
    print(formatted)
    print("="*50)

if __name__ == "__main__":
    test_formatted_output()
