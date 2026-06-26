# MIDI-to-Arduino-Sound
If you want to play any midi song you like, you're in the right place. This is an program I made that let's you play any song you like that's a midi file on an Arduino Uno with a buzzer or piezo. This is a work in progress and the limitations are that the midi has to be only one instrument, cannot play multiple notes together, and the timing may be off. I'm working on that
## Instructions
1. Check to make sure you have the latest version of Python
2. Download the Files on the Repository
3. Install the Python MIDI library (AKA, mido) using the command ```pip install mido```
4. Run the command ```python C:\Users\%USERPROFILE%\midi_to_arduino.py "C:\Users\%USERPROFILE%\your song.mid" C:\Users\%USERPROFILE%\song.h --max-notes 300``` or For MacOS/Linux ```python3 where the file is/midi_to_arduino.py "path your midi file is/your midi file.midi" where the file is/midi_player/song.h --max-notes 300```. Also, Please note to replace the file paths with wherever you placed the `midi_player.ino` for all of them.
