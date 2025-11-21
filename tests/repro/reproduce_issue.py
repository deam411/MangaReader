import re

def extract_number(file_path: str) -> tuple:
    """Extract the number of the images by path name and file name, handling decimals."""
    # Find all sequences of digits, optionally followed by a decimal and more digits
    nums = re.findall(r"(\d+(?:\.\d+)?)", file_path)
    # Convert to float for proper numerical sorting, then to tuple
    return tuple(float(n) for n in nums) if nums else (0,)

def test_sorting():
    # Case 1: Mob Psycho 100 chapters
    # The issue is likely that "100" in the title is being picked up as a number
    chapters = [
        "Mob Psycho 100 - Chapter 1",
        "Mob Psycho 100 - Chapter 2",
        "Mob Psycho 100 - Chapter 10",
        "Mob Psycho 100 - Chapter 100", # This might be tricky if 100 is seen as the first number
        "Mob Psycho 100 - Chapter 99",
    ]
    
    print("--- Original Sorting Logic ---")
    sorted_chapters = sorted(chapters, key=extract_number)
    for c in sorted_chapters:
        print(f"{c} -> {extract_number(c)}")
        
    # Expected order: 1, 2, 10, 99, 100
    # If "100" from title is picked up, they might all start with 100.0
    
    # Check if the order is correct
    expected = [
        "Mob Psycho 100 - Chapter 1",
        "Mob Psycho 100 - Chapter 2",
        "Mob Psycho 100 - Chapter 10",
        "Mob Psycho 100 - Chapter 99",
        "Mob Psycho 100 - Chapter 100",
    ]
    
    if sorted_chapters == expected:
        print("\nSUCCESS: Sorting works as expected.")
    else:
        print("\nFAILURE: Sorting is incorrect.")
        print("Expected:", expected)
        print("Actual:  ", sorted_chapters)

if __name__ == "__main__":
    test_sorting()
