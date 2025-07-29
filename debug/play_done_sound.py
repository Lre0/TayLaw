"""
Quick script to play completion sound - run this when coding is done
"""
import winsound

try:
    # Play a nice completion melody
    notes = [
        (523, 200),  # C
        (659, 200),  # E  
        (784, 400),  # G (longer)
    ]
    
    print("Playing completion sound...")
    for frequency, duration in notes:
        winsound.Beep(frequency, duration)
    
    print("[SUCCESS] Coding task completed!")
    
except Exception as e:
    # Fallback
    print(f"\a[SUCCESS] Coding task completed! (Sound error: {e})")