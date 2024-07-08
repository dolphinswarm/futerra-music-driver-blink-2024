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
	# Convert input lists from strings to integers
	chord_notes = [int(note) for note in chord_notes]
	scale_mode_notes = [int(note) for note in scale_mode_notes]

	# Check each note and adjust it to the proper key / scale mode
	new_notes = chord_notes[:]
	for i, note in enumerate(new_notes):
		# If the note is not in the scale mode, subtract 1 to adjust it for the key (I think? TODO verify?)
		# Also, we don't want to adjust any 4th note in a scale (TODO maybe find a better system?)
		if note % 12 not in scale_mode_notes or i != 4:
			note = note - 1

	# Convert the result back to strings
	new_notes = [str(note) for note in new_notes]
	return new_notes

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

# TODO MORE MELODIES
def trigger_melody(melody_instruments, chord, scale_mode):
	# For each melody instrument:
	for instrument_name, instrument_props in melody_instruments.items():
		# Get the notes and the base scale
		scale_notes = scale_notes_table[scale_notes_table.findCell(scale_mode, caseSensitive=True).row, 'Notes'].val.split(',')
		chord_base_note = min([int(x) for x in chord_table[chord_table.findCell(chord, caseSensitive=True).row, 'Notes Above Root'].val.split(',')])
		base_note = instrument_props.base_note

		# Set the notes to play for the melody (I, V, VI, IV, V for now) TODO MORE MELODIES
		notes = (
			(int(base_note) + int(chord_base_note) + int(scale_notes[0]), 0.0, 1.0, 100, 0), 
			(int(base_note) + int(chord_base_note) + int(scale_notes[4]), 1.0, 1.0, 100, 0), 
			(int(base_note) + int(chord_base_note) + int(scale_notes[5]), 2.0, 1.0, 100, 0), 
			(int(base_note) + int(chord_base_note) + int(scale_notes[3]), 3.0, 1.0, 100, 0),
			(int(base_note) + int(chord_base_note) + int(scale_notes[4]), 4.0, 3.0, 100, 0), 
		)

		# Remove all existing notes
		op(instrument_name).RemoveNotes(timeStart=0, pitchStart=0, timeEnd=8, pitchEnd=127)
		# op(instrument_name).par.Stopclip.pulse()

		# Play the notes for the new melody
		op(instrument_name).SetNotes(notes=notes)
		op(instrument_name).par.Fireclip.pulse()



def generate_chord_variant(chord, chord_variation, scale_mode, grab_random_variant = False):
	# Choose a chord variant based on the specified parameter
	if grab_random_variant == True:
		# Choose a random chord variation
		new_variation_row = chord_variations_table.cell(random.randint(1, chord_variations_table.numRows - 1), 0).row
	else:
		# Grab a transition chord variation
		possible_transitions = chord_variations_table[chord_variations_table.findCell(chord_variation, caseSensitive=True).row, 'Possible Transition Variations'].val.split(',')
		new_variation_row = chord_variations_table.findCell(random.choice(possible_transitions), caseSensitive=True).row
	
	new_variation = chord_variations_table[new_variation_row, 'Chord Variation'].val
	new_variation_notes = chord_variations_table[new_variation_row, 'Notes Above Root'].val.split(',')
	
	# Adjust the notes to be in the given scale
	scale_notes = scale_notes_table[scale_notes_table.findCell(scale_mode, caseSensitive=True).row, 'Notes'].val.split(',')
	adjust_chord_to_scale_mode(chord_notes=new_variation_notes, scale_mode_notes=scale_notes)

	# Update the global storage variables
	storage.store('chord_variation', new_variation)
	chord_base_note = min(chord_table[chord_table.findCell(chord, caseSensitive=True).row, 'Notes Above Root'].val.split(','))

	# Return the new notes for the chord and the chord variation name
	new_notes = [str(int(x) + int(chord_base_note)) for x in new_variation_notes]
	return new_notes, chord_variation

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
		
		# If it's a melody, we handle that separately, so just add it back to instruments and call it a day
		elif instrument_props.instrument_role == 'melody':
			new_instruments[instrument_name] = Instrument(
				base_note=instrument_props.base_note,
				num_voices=0,
				instrument_role='melody',
				playing_notes=[]
			)
			continue

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

	# Turn off all midi melodies (TODO BETTER WAY TO DO THIS)
	melody_instruments = {key: value for key, value in instruments.items() if value.instrument_role == 'melody'}
	for instrument in melody_instruments:
		op(instrument).par.Stopclip.pulse()

	# If we should change keys...
	if key_change_driver['pulse'] == 0:
		# Reset the value of the OP
		key_change_driver.par.resetvalue = random.randint(20, 50)
		key_change_driver.par.resetpulse.pulse()

		# Grab a new key and scale mode, based on the mood and key change limitations
		current_key_row = keys_table.findCell(key, caseSensitive=True).row
		new_key = keys_table[current_key_row, 'Common Key Change Keys'].val.split(',')[random.randint(0, 3)] #TODO LOOK AT MORE KEY CHANGES
		# Update the global storage and local variables
		storage.store('key', new_key)
		key = new_key

		mood = mood_picker[0, 0].val
		scale_notes_possible_rows = scale_notes_table.findCells(mood, cols=['Mood'])
		scale_notes_row = random.choice(scale_notes_possible_rows).row # random.randint(1, 7) <- This is for entirely random scale mode picking
		new_scale_mode = scale_notes_table[scale_notes_row, 'Name'].val
		# Update the global storage and local variables
		storage.store('scale_mode', new_scale_mode)
		scale_mode = new_scale_mode

		# Grab the new notes of the I chord in the new key
		scale_notes = scale_notes_table[scale_notes_table.findCell(scale_mode, caseSensitive=True).row, 'Notes'].val.split(',')
		new_notes = [scale_notes[0], scale_notes[2], scale_notes[4]] # Always I, but intended to that way
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

		# Randomly land on a variant of the current chord
		should_do_variant = random.randint(0, 1) == 0
		if should_do_variant:
			# Grab a transition chord variation
			new_chord_variant_info = generate_chord_variant(
				chord=chord,
				chord_variation=chord_variation,
				scale_mode=scale_mode,
				grab_random_variant=True
			)
			new_notes = new_chord_variant_info[0]
			chord_variation = new_chord_variant_info[1]
		else:
			storage.store('chord_variation', 'major triad') # Technically not major for all keys but OH WHALEEEEE (also TODO look at?)
			chord_variation = 'major triad'
		
	# Else, shift to a random variation
	else:
		# Grab a transition chord variation
		new_chord_variant_info = generate_chord_variant(
			chord=chord,
			chord_variation=chord_variation,
			scale_mode=scale_mode,
		)
		new_notes = new_chord_variant_info[0]
		chord_variation = new_chord_variant_info[1]
	

	# Handle changing notes based on updated information
	change_notes(
		current_chord_notes=current_notes,
		new_chord_notes=new_notes,
		instruments=instruments
	)

	# Trigger the melody for a given chord change or whatever

	trigger_melody(
		melody_instruments=melody_instruments,
		chord=chord,
		scale_mode=scale_mode
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
	