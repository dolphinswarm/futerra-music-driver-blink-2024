import random
from typing import List, Dict

# me - this DAT
# 
# channel - the Channel object which has changed
# sampleIndex - the index of the changed sample
# val - the numeric value of the changed sample
# prev - the previous sample value
# 
# Make sure the corresponding toggle is enabled in the CHOP Execute DAT.

# ========= Classes
# TODO CAN THIS BE SHARED WITH THE OTHER FILE?
class Instrument:
	# Props
	base_note: int
	num_voices: int
	instrument_role: str
	playing_notes: List[int]

	# Methods
	def __init__(self, base_note: int, num_voices: int, instrument_role: str, playing_notes: List[int]):
		self.base_note = base_note
		self.num_voices = num_voices
		self.instrument_role = instrument_role
		self.playing_notes = playing_notes

# ========= Reference OPs
change_chord_driver = op('change_chord_driver')
key_change_driver = op('key_change_driver')
scale_notes_table = op('scale_notes')
keys_table = op('keys')
chord_table = op('chords')
chord_variations_table = op('chord_variations')
storage = op('storage_op')
mood_picker = op('mood_picker')

# ========= Helper Funcs
def adjust_chord_to_scale_mode(chord_notes, scale_mode_notes):
	print('hello')
	return

def find_closest_note(note, target_notes):	
    # Find the closest note in target_notes to the given note, considering both current and previous octaves
    candidates = [(tn, tn) for tn in target_notes] + [(tn - 12, tn) for tn in target_notes]
    closest_note, original = min(candidates, key=lambda x: abs(x[0] - note))
    return closest_note, original

def normalize_notes(notes):
    # Normalize notes to a single octave (pitch class)
    return [int(note) % 12 for note in notes]

def adjust_octave(note, reference):
    # Adjust note to the same octave as the reference
    while note < reference:
        note += 12
    while note - reference >= 12:
        note -= 12
    return note

def change_notes(current_chord_notes, new_chord_notes, instruments):
	# For each instrument:
	new_instruments = {}
	for instrument_name, instrument_props in instruments.items():
		# Get the MIDI notes that should play in the given key, chord, etc.
		new_chord = []

		# ===== Determine notes
		# If a bass, just switch to the root note
		if instrument_props.instrument_role == 'bass':
			new_chord = normalize_notes([min([int(note) for note in new_chord_notes])])
			print(new_chord)

		# Else, we actually care about notes
		else:
			current_notes = normalize_notes(current_chord_notes[:instrument_props.num_voices])
			target_notes = normalize_notes(new_chord_notes[:instrument_props.num_voices])
			for i, note in enumerate(current_notes):
				# While we have notes to voice-lead on:
				if target_notes:
					closest_note, original = find_closest_note(current_notes[i], target_notes)
					new_chord.append(note - (note % 12) + closest_note)
					target_notes.remove(original)  # Remove the original target note to prevent reuse
				else:
					break  # No more target notes to match
			new_chord.extend(target_notes)  # Add remaining target notes if any

		new_instrument_notes = []
		for note in new_chord:
			new_instrument_notes.append(str(instrument_props.base_note + int(note))) # For example, 60 + 5 would 65, so F

		# ===== Trigger the new MIDI messages
		current_instrument_notes = instrument_props.playing_notes
		# Find notes to turn off (in current_chord but not in new_chord)
		notes_to_off = [note for note in current_instrument_notes if note not in new_instrument_notes]
		for note in notes_to_off:
			op(instrument_name).SendMIDI('note', int(note), 0)

 		# Find notes to turn on (in new_chord but not in current_chord)
		notes_to_on = [note for note in new_instrument_notes if note not in current_instrument_notes]
		for note in notes_to_on:
			op(instrument_name).SendMIDI('note', int(note), 100)

		# Add the new instrument object
		new_instruments[instrument_name] = Instrument(
			base_note=instrument_props.base_note,
			num_voices=instrument_props.num_voices,
			instrument_role=instrument_props.instrument_role,
			playing_notes=new_instrument_notes
		)

	# Store the new values in the dictionary
	storage.store('instruments', new_instruments)
	return

# ========= Main Funcs
def onOffToOn(channel, sampleIndex, val, prev):
	# Get the current props of the song
	key = storage.fetch('key', 'C')
	scale_mode = storage.fetch('scale_mode', 'ionian')
	chord = storage.fetch('chord', 'I')
	chord_variation = storage.fetch('chord_variation', 'major triad')
	current_notes = storage.fetch('chord_notes', ['0', '4', '7'])
	new_notes = []
	instruments = storage.fetch('instruments', {})

	# If we should change keys...
	if key_change_driver['pulse'] == 0:
		# Reset the value of the OP
		key_change_driver.par.resetvalue = random.randint(20, 50)
		key_change_driver.par.resetpulse.pulse()

		# Grab a new key and scale mode, based on the mood and key change limitations
		current_key_row = keys_table.findCell(key).row
		new_key = keys_table[current_key_row, 'Common Key Change Keys'].val.split(',')[random.randint(0, 3)] #TODO LOOK AT MORE KEY CHANGES
		# Update the global storage and local variables
		storage.store('key', new_key)
		key = new_key

		mood = mood_picker[0, 0].val
		scale_notes_possible_rows = scale_notes_table.findCells(mood, cols=['Mood'])
		# scale_notes_row = random.randint(1, 7) <- This is for entirely random scale mode picking
		scale_notes_row = random.choice(scale_notes_possible_rows).row
		new_scale_mode = scale_notes_table[scale_notes_row, 'Name'].val
		# Update the global storage and local variables
		storage.store('scale_mode', new_scale_mode)
		scale_mode = new_scale_mode

		# Grab the new notes of the I chord in the new key
		scale_notes = scale_notes_table[scale_notes_table.findCell(scale_mode).row, 'Notes'].val.split(',')
		new_notes = [scale_notes[0], scale_notes[2], scale_notes[4]]
		# Update the global storage and local variables
		storage.store('chord_variation', 'major triad') # Technically not major for all keys but OH WHALEEEEE (also TODO look at?)
		chord_variation = 'major triad'
		storage.store('chord', 'I')
		chord_variation = 'I'

	# Else, check if we should change chords
	elif change_chord_driver['pulse'] == 0:
		# Reset the value
		change_chord_driver.par.resetvalue = random.randint(0, 4)
		change_chord_driver.par.resetpulse.pulse()

		# Grab a transition chord
		possible_transitions = chord_table[chord_table.findCell(chord, caseSensitive=True).row, 'Common Transitions'].val.split(',')
		new_chord_row = chord_table.findCell(random.choice(possible_transitions), caseSensitive=True).row
		new_chord = chord_table[new_chord_row, 'Chord'].val
		new_chord_notes = chord_table[new_chord_row, 'Notes Above Root'].val.split(',')

		# Update the global storage and local variables
		storage.store('chord', new_chord)
		chord = new_chord
		new_notes = new_chord_notes

		# Update the global storage and local variables
		# TODO DELETE
		storage.store('chord_variation', 'major triad') # Technically not major for all keys but OH WHALEEEEE (also TODO look at?)
		chord_variation = 'major triad'
		
		# TODO Randomly decide on a new variant
		# should_do_variant = random.randint(0, 1) == 0
		# if should_do_variant:
	
	# Else, shift to a random variation
	else:
		# Grab a transition chord variation
		possible_transitions = chord_variations_table[chord_variations_table.findCell(chord_variation).row, 'Possible Transition Variations'].val.split(',')
		new_variation_row = chord_variations_table.findCell(random.choice(possible_transitions)).row
		new_variation = chord_variations_table[new_variation_row, 'Chord Variation'].val
		new_variation_notes = chord_variations_table[new_variation_row, 'Notes Above Root'].val.split(',')

		# TODO ADJUST FOR KEY

		# Update the global storage and local variables
		storage.store('chord_variation', new_variation)
		chord_variation = new_variation
		chord_base_note = min(chord_table[chord_table.findCell(chord).row, 'Notes Above Root'].val.split(','))
		new_notes = [str(int(x) + int(chord_base_note)) for x in new_variation_notes]

	# Handle changing notes based on updated information
	change_notes(
		current_chord_notes=current_notes,
		new_chord_notes=new_notes,
		instruments=instruments
	)

	# Update the new variant + notes after the transition happens
	storage.store('current_chord_notes', new_notes)


	return

def whileOn(channel, sampleIndex, val, prev):
	return

def onOnToOff(channel, sampleIndex, val, prev):
	return

def whileOff(channel, sampleIndex, val, prev):
	return

def onValueChange(channel, sampleIndex, val, prev):
	return
	