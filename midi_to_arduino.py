#!/usr/bin/env python3
"""
midi_to_arduino.py

Converts a MIDI (.mid) file into a C++ header file containing a
note/duration array suitable for playing on a passive buzzer with
an Arduino Uno/Nano using tone().

Usage:
    python midi_to_arduino.py input.mid output.h [--track N] [--max-notes N]

Notes:
- Only ONE track is converted (monophonic). If your MIDI has multiple
  tracks/instruments, pick the one with the melody using --track.
- Chords are flattened: if multiple notes overlap, only the highest
  note currently held is played (typical "pick the melody" behavior).
- Output uses PROGMEM arrays so it fits in flash instead of RAM,
  since Uno/Nano only have 2KB of RAM.
"""

import sys
import argparse
import mido

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def midi_note_to_freq(note):
    # MIDI note 69 = A4 = 440Hz
    return 440.0 * (2.0 ** ((note - 69) / 12.0))

def midi_note_to_name(note):
    name = NOTE_NAMES[note % 12]
    octave = note // 12 - 1
    return f"{name}{octave}"

def build_tempo_map(mid):
    """
    Collect every set_tempo event across ALL tracks (tempo is a global
    property in MIDI even though it's encoded in a track), as a sorted
    list of (abs_tick, tempo_us_per_beat). A default tempo entry at
    tick 0 is included so lookups always have something to fall back on.
    """
    changes = [(0, 500000)]  # default 120 BPM if file never specifies one
    for track in mid.tracks:
        abs_tick = 0
        for msg in track:
            abs_tick += msg.time
            if msg.type == "set_tempo":
                changes.append((abs_tick, msg.tempo))
    changes.sort(key=lambda c: c[0])
    return changes

def ticks_to_ms_with_tempo_map(start_tick, end_tick, tempo_map, ticks_per_beat):
    """
    Convert a tick span to milliseconds, correctly accounting for any
    tempo changes that occur *within* the span (e.g. the song speeds up
    partway through a note or rest). Splits the span at each tempo
    boundary and sums the ms for each piece under its own tempo.
    """
    if end_tick <= start_tick:
        return 0.0

    # tempo in effect at start_tick
    current_tempo = 500000
    for tick, tempo in tempo_map:
        if tick <= start_tick:
            current_tempo = tempo
        else:
            break

    boundaries = [t for t, _ in tempo_map if start_tick < t < end_tick]
    points = [start_tick] + boundaries + [end_tick]

    total_ms = 0.0
    tempo_idx = 0
    tempo_at = current_tempo
    for i in range(len(points) - 1):
        seg_start, seg_end = points[i], points[i + 1]
        # find tempo active at seg_start
        active_tempo = 500000
        for tick, tempo in tempo_map:
            if tick <= seg_start:
                active_tempo = tempo
            else:
                break
        seg_ticks = seg_end - seg_start
        total_ms += seg_ticks * (active_tempo / ticks_per_beat) / 1000.0

    return total_ms

def extract_melody(mid, track_index=None):
    """
    Extract a monophonic melody (freq_hz, duration_ms, note_name) list.
    If track_index is None, picks the track with the most note events.

    Rests (silences between notes) are preserved as explicit freq=0
    entries instead of being dropped, so playback timing/rhythm matches
    the original file rather than compressing when notes are released.

    Tempo changes anywhere in the file are accounted for, including
    tempo changes that occur in the middle of a held note or rest.
    """
    ticks_per_beat = mid.ticks_per_beat
    tempo_map = build_tempo_map(mid)  # list of (abs_tick, tempo) covering whole song

    # choose track
    if track_index is None:
        best_idx, best_count = 0, -1
        for i, track in enumerate(mid.tracks):
            count = sum(1 for msg in track if msg.type == "note_on" and msg.velocity > 0)
            if count > best_count:
                best_count, best_idx = count, i
        track_index = best_idx
        print(f"Auto-selected track {track_index} ({best_count} note events)")

    track = mid.tracks[track_index]

    events = []  # (abs_tick, type, note)
    abs_tick = 0
    for msg in track:
        abs_tick += msg.time
        if msg.type == "note_on" and msg.velocity > 0:
            events.append((abs_tick, "on", msg.note))
        elif msg.type == "note_off" or (msg.type == "note_on" and msg.velocity == 0):
            events.append((abs_tick, "off", msg.note))

    events.sort(key=lambda e: e[0])

    # Flatten to monophonic: track currently-held notes, always play highest.
    # Unlike before, a "None" (rest) span IS kept as a melody entry instead
    # of being silently skipped, so silence in the source is preserved.
    held = set()
    melody = []  # (start_tick, end_tick, note_or_None)
    current_note = None
    current_start = 0

    for tick, ev_type, note in events:
        if ev_type == "on":
            held.add(note)
        else:
            held.discard(note)

        new_top = max(held) if held else None

        if new_top != current_note:
            if tick > current_start:
                melody.append((current_start, tick, current_note))  # current_note may be None = rest
            current_note = new_top
            current_start = tick

    notes = []
    for start, end, note in melody:
        dur_ms = ticks_to_ms_with_tempo_map(start, end, tempo_map, ticks_per_beat)
        if dur_ms <= 0:
            continue
        if note is None:
            notes.append((0, int(round(dur_ms)), "REST"))
        else:
            freq = round(midi_note_to_freq(note), 2)
            notes.append((int(round(freq)), int(round(dur_ms)), midi_note_to_name(note)))

    return notes

def write_header(notes, out_path, var_prefix="song"):
    with open(out_path, "w") as f:
        f.write("// Auto-generated by midi_to_arduino.py\n")
        f.write("// Note/duration array for Arduino tone() playback on a passive buzzer\n")
        f.write("#pragma once\n#include <avr/pgmspace.h>\n\n")
        f.write(f"const uint16_t {var_prefix}_freq[] PROGMEM = {{\n")
        for i in range(0, len(notes), 10):
            chunk = notes[i:i+10]
            f.write("  " + ", ".join(str(n[0]) for n in chunk) + ",\n")
        f.write("};\n\n")

        f.write(f"const uint16_t {var_prefix}_dur[] PROGMEM = {{\n")
        for i in range(0, len(notes), 10):
            chunk = notes[i:i+10]
            f.write("  " + ", ".join(str(n[1]) for n in chunk) + ",\n")
        f.write("};\n\n")

        f.write(f"const uint16_t {var_prefix}_length = {len(notes)};\n")

    print(f"Wrote {len(notes)} notes to {out_path}")
    if notes:
        print("First few notes (freq Hz, duration ms, note name):")
        for n in notes[:8]:
            print(f"  {n[0]:>5} Hz  {n[1]:>5} ms  {n[2]}")

def main():
    parser = argparse.ArgumentParser(description="Convert a MIDI file to an Arduino-ready note array")
    parser.add_argument("input", help="Input .mid file")
    parser.add_argument("output", help="Output .h file")
    parser.add_argument("--track", type=int, default=None, help="Track index to use (default: auto-pick melody track)")
    parser.add_argument("--max-notes", type=int, default=None, help="Truncate to this many notes (Uno flash is limited)")
    parser.add_argument("--var-prefix", default="song", help="Variable name prefix in generated C++ (default: song)")
    args = parser.parse_args()

    mid = mido.MidiFile(args.input)
    print(f"Loaded {args.input}: {len(mid.tracks)} tracks, ticks_per_beat={mid.ticks_per_beat}")

    notes = extract_melody(mid, args.track)

    if args.max_notes and len(notes) > args.max_notes:
        print(f"Truncating from {len(notes)} to {args.max_notes} notes")
        notes = notes[:args.max_notes]

    write_header(notes, args.output, args.var_prefix)

if __name__ == "__main__":
    main()
