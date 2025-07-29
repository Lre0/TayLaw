"""
Simple completion sound notification system for Claude Code
"""
import sys
import os

def play_completion_sound():
    """Play a completion sound using Windows built-in sounds"""
    try:
        # Try using Windows winsound module (built-in)
        import winsound
        
        # Play a simple beep - frequency 800Hz for 500ms
        winsound.Beep(800, 500)
        print("🔊 Task completed! (Beep sound played)")
        
    except ImportError:
        try:
            # Fallback: Use system bell
            print("\a🔊 Task completed! (System bell)")
            
        except:
            # Final fallback: Just print notification
            print("🔊 Task completed!")

def play_success_sound():
    """Play a success sound sequence"""
    try:
        import winsound
        
        # Play a pleasant ascending sequence
        frequencies = [523, 659, 784]  # C, E, G notes
        for freq in frequencies:
            winsound.Beep(freq, 200)
        
        print("🎉 Coding task successfully completed! (Success melody played)")
        
    except ImportError:
        # Fallback
        print("\a\a🎉 Coding task successfully completed!")

def play_error_sound():
    """Play an error sound"""
    try:
        import winsound
        
        # Play a lower error tone
        winsound.Beep(300, 800)
        print("❌ Task completed with errors (Error tone played)")
        
    except ImportError:
        print("\a❌ Task completed with errors")

if __name__ == "__main__":
    # Test the sounds
    print("Testing completion sounds...")
    
    print("\n1. Basic completion sound:")
    play_completion_sound()
    
    input("\nPress Enter to test success sound...")
    print("2. Success sound:")
    play_success_sound()
    
    input("\nPress Enter to test error sound...")
    print("3. Error sound:")
    play_error_sound()
    
    print("\nSound test completed!")