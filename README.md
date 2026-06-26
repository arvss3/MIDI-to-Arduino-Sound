# MIDI-to-Arduino-Sound
If you want to play any midi song you like, you're in the right place. This is an program I made that let's you play any song you like that's a midi file on an Arduino Uno with a buzzer or piezo. This is a work in progress and the limitations are that the midi has to be only one instrument, cannot play multiple notes together, and the timing may be off. I'm working on that and also please be mindful of the 300 note limit, if you want, you can edit it on the file.
## Instructions
1. Check to make sure you have the latest version of Python
2. Download the Files on the Repository
3. Install the Python MIDI library (AKA, mido) using the command ```pip install mido```
4. Make a folder named midi_player or use ```mkdir``` if you have to use it.
5. Run the command ```python C:\Users\%USERPROFILE%\midi_to_arduino.py "C:\Users\%USERPROFILE%\midi_player\your song.mid" C:\Users\%USERPROFILE%\midi_player\song.h --max-notes 300``` or For MacOS/Linux ```python3 midi_player/midi_to_arduino.py "midi_player/your midi file.midi" midi_player/song.h --max-notes 300```.
6. Make sure that `.ino` file is in the same folder as the header.
7. Open `Midi player.ino`
8. Make sure the positive on the Arduino board is wired to pin 8 and is connected to ground. You can edit the pins in the code if you want to.
9. Upload and enjoy your song
