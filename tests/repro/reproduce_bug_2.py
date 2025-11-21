import re

def clean_chapter_title(raw_title: str) -> str:
    """Cleans the raw chapter title to extract only the relevant part (e.g., 'Capitolo X')."""
    # Regex to find "Capitolo X", "Chapter X", or "Volume X" (including decimals)
    match = re.search(r'(capitolo|chapter|volume)\s+\d+(?:\.\d+)?', raw_title, re.IGNORECASE)
    if match:
        # Standardize to "Capitolo" if it's "Chapter", otherwise keep "Volume"
        prefix = match.group(1).lower()
        number_part = match.group(0).split()[-1]
        
        if prefix == 'volume':
            return f"Volume {number_part}"
        return f"Capitolo {number_part}"
    
    # Fallback if no specific pattern is found, try to extract just numbers
    # Handle decimals correctly (e.g., 10.5)
    numbers = re.findall(r'\d+(?:\.\d+)?', raw_title)
    if numbers:
        return f"Capitolo {numbers[-1]}" # Assume the last number is the chapter number
    
    return raw_title # Return original if no pattern or number found

def test_cleaning():
    test_cases = [
        ("Mob Psycho 100 - Capitolo 1", "Capitolo 1"),
        ("Mob Psycho 100 - Capitolo 10.5", "Capitolo 10.5"),
        ("Mob Psycho 100 - 1", "Capitolo 1"),
        ("Mob Psycho 100 - 10.5", "Capitolo 10.5"), # This should fail with current logic
        ("Mob Psycho 100 100", "Capitolo 100"),
        ("Chapter 10.5", "Capitolo 10.5"), # This might fail if "Chapter" is not handled
    ]
    
    print("--- Testing clean_chapter_title ---")
    failures = 0
    for input_title, expected in test_cases:
        result = clean_chapter_title(input_title)
        print(f"Input: '{input_title}' -> Output: '{result}'")
        if result != expected:
            print(f"  FAILURE: Expected '{expected}', got '{result}'")
            failures += 1
        else:
            print(f"  SUCCESS")
            
    if failures == 0:
        print("\nALL TESTS PASSED")
    else:
        print(f"\n{failures} TESTS FAILED")

if __name__ == "__main__":
    test_cleaning()
