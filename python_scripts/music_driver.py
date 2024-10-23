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

# region Classes

class Instrument:
	# Props
	base_note: int # NOTE: For melody instruments, the base note is treated as the minumum note an instrument can play; this is to avoid weirdness with the ranges of instruments when shifted up/down in a key or chord
	num_voices: int
	instrument_role: str # Possible roles: bass, chords, effects, melody, percussion, sfx (used to have event, but removed in favor of just using the params from TDAbleton + MIDI)
	scene: str
	playing_notes: List[int]

	# Methods
	def __init__(self, base_note: int, num_voices: int, instrument_role: str, scene: str, playing_notes: List[int]):
		self.base_note = base_note
		self.num_voices = num_voices
		self.instrument_role = instrument_role
		self.scene = scene
		self.playing_notes = playing_notes

# endregion

# region Reference OPs

change_chord_driver = op('change_chord_driver')
key_change_driver = op('key_change_driver')
scale_notes_table = op('scale_notes')
keys_table = op('keys')
chord_table = op('chords')
chord_variations_table = op('chord_variations')
storage = op('storage_op')
time_of_day = op('time_of_day')
scene_transition_driver = op('scene_transition_driver')
chord_history = op('chord_history')
volumes = op('volumes')

# endregion

# region Helper Functions

def kill_instruments(instruments, current_scene, next_scene):
	"""Stops all the instruments from a provided list.

	Args:
		instruments (dictionary of Instruments): A dictionary of Instruments to stop playing.
		current_scene (str): The current scene playing.
		next_scene (str): The upcoming scene.
	"""
	for scene_name, scene_instruments in instruments.items():
		# Make an empty object for killing off instruments
		empty_instruments = {}

		# If the scene is the current scene or the volume is audible (i.e., the previous scene), send notes to it
		if scene_name == current_scene or scene_name == next_scene or volumes[scene_name] > 0.35:
			continue

		for instrument_name, instrument_props in scene_instruments.items():
			# If a melody, reset its clip
			if instrument_props.instrument_role == 'melody':
				# Remove all existing notes
				op(instrument_name).RemoveNotes(timeStart=0, pitchStart=0, timeEnd=16, pitchEnd=127)
				op(instrument_name).par.Stopclip.pulse()

			# If it's SFX, reset the clip without doing anything MIDI-wise
			elif instrument_props.instrument_role == 'sfx':
				op(instrument_name).par.Stopclip.pulse()

			# Else, it's MIDI, so reset it
			else:
				op(instrument_name).SendMIDI('flush')
				op(instrument_name).par.Clearchop.pulse()

			# Also kill off its playing MIDI notes from state
			# Add the new instrument object
			new_instrument_props = instrument_props
			new_instrument_props.playing_notes = []
			empty_instruments[instrument_name] = Instrument(**vars(new_instrument_props))


		base_instruments = storage.fetch('instruments', {}) # We need to get the updated values from other scenes, so we have to directly fetch this from storage instead of passing in as a prop
		storage.store('instruments', base_instruments | {
			scene_name: empty_instruments
		})


def adjust_to_chord_in_scale_mode(notes, scale_mode_notes, chord_base_note, chord_notes, mode, ignore_notes=[], override_scale_mode_notes=False):
	"""Changes a given set of notes to a specific chord (i.e., IV) in a given scale mode (i.e., dorian).

	Args:
		notes (list[str]): An array of string numbers, indicating their position above the root of the chord (0).
		scale_mode_notes (list[str]): An array of string numbers, which indicate all notes in a scale mode based on their position above the root (0).
		chord_base_note (str): The base note of the chord, represented by a position above the root (0).
		chord_notes (list[str]): An array of string numbers, which indicate all notes in a chord variation based on their position above the root (0).
		mode (str): "chord" mode (which ignores specific chord notes) or "melody" mode (which ignores notes specified in ignore_notes)
		ignore_notes (list[int], optional): A list of note positions that we should not adjust to a given mode. Defaults to [].
		override_scale_mode_notes (bool, optional): Should we override the scale mode notes? Defaults to False.

	Returns:
		str[]: A string array of notes, adjusted to the above parameters.
	"""

	# Convert input lists from strings to integers
	notes = [(int(note) + int(chord_base_note)) for note in notes]
	scale_mode_notes = [int(note) % 12 for note in scale_mode_notes]
	chord_notes = [(int(note) + int(chord_base_note)) % 12 for note in chord_notes]  # Modulo 12 for chromatic scale

	# Check each note and adjust it to the proper key / scale mode / chord
	new_notes = notes[:]
	for i, note in enumerate(new_notes):
		note_in_scale = note % 12 in scale_mode_notes
		note_in_chord = note % 12 in chord_notes
		if ((mode == "chord" and i != 4) or (mode == "melody" and note % 12 not in ignore_notes)):
			# Adjust all items NOT in the scale mode OR chord, depending on the override
			if (not override_scale_mode_notes and not note_in_scale) or (override_scale_mode_notes and not note_in_chord):
				note = note - 1  # Adjust down chromatically until it fits
					
		# Assign the adjusted note to the output list
		new_notes[i] = note

	# Convert the result back to strings
	new_notes = [str(note) for note in new_notes]
	return new_notes

def find_closest_note(note, target_notes):
	"""Finds the closest note in a list of target notes.

	Args:
		note (int): The current note, in a position above the root (0) of a chord.
		target_notes (list[int]): A list of target notes, in positions above the root (0) of a chord.

	Returns:
		ints:
			- int: The new closest note
			- int: The original note
	"""
	# Find the closest note in target_notes to the given note, considering both current and previous octaves
	candidates = [(tn, tn) for tn in target_notes] + [(tn - 12, tn) for tn in target_notes]
	closest_note, original = min(candidates, key=lambda x: abs(x[0] - note))
	return closest_note, original

def normalize_notes(notes):
	"""Normalizes notes to a single octave.

	Args:
		notes (list[str]): A list of string notes, each a position above a root (0).

	Returns:
		list[int]: A list of notes normalized to one octave.
	"""
	return [int(note) % 12 for note in notes]

def adjust_octave(note, reference):
	"""Adjusts the octave of a note to be within the same as a reference note.

	Args:
		note (int): A note position above a root (0).
		reference (int): A base note to adjust the octave to.

	Returns:
		int: A note adjusted to fit near the reference note
	"""
	while note < reference:
		note += 12
	while note - reference >= 12:
		note -= 12
	return note

def trigger_percussion(percussion_instruments):
	"""Triggers all percussion instruments.

	Args:
		percussion_instruments (Dictionary of Instruments): A dictionary of percussion instruments.
	"""
	should_trigger_percussion = random.randint(0, 1) == 1
	if should_trigger_percussion:
		for instrument_name, instrument_props in percussion_instruments.items():
			op(instrument_name).SendMIDI('note', int(instrument_props.base_note), 0)
			op(instrument_name).SendMIDI('note', int(instrument_props.base_note), 100)

def adjust_melody_to_proper_octave(notes, base_note, scale_mode_notes, chord_base_note, chord_notes, override_scale_mode_notes, key_offset, ignore_notes=[]):
	"""Adjusts a melody to a proper scale mode and octave.

	Args:
		notes (list[str]): An array of string numbers, indicating their position above the root of the chord (0).
		base_note (str): The "base" (lowest) note for a given melody instrument.
		scale_mode_notes (list[str]): An array of string numbers, which indicate all notes in a scale mode based on their position above the root (0).
		chord_base_note (str): The base note of the chord, represented by a position above the root (0).
		chord_notes (list[str]): An array of string numbers, which indicate all notes in a chord variation based on their position above the root (0).
		override_scale_mode_notes (bool): Should we override the scale mode notes?
		key_offset (str): The pitch offset for a given key.
		ignore_notes (list[int], optional): A list of note positions that we should not adjust to a given mode. Defaults to [].

	Returns:
		list[int]: A list of melody notes adjusted to a given octave/key/scale mode.
	"""
	# Get the adjusted notes, then shift them to the proper octave for the instrument
	melody_notes = adjust_to_chord_in_scale_mode(
		notes=notes,
		scale_mode_notes=scale_mode_notes,
		chord_base_note=chord_base_note,
		chord_notes=chord_notes,
		mode="melody",
		override_scale_mode_notes=override_scale_mode_notes,
		ignore_notes=ignore_notes
	)
	instrument_melody_notes = [(int(note) + int(key_offset)) for note in melody_notes]
	while min(instrument_melody_notes) < int(base_note):
		instrument_melody_notes = [note + 12 for note in instrument_melody_notes]

	return instrument_melody_notes


def trigger_melody(melody_instruments, chord, chord_variation, key, scale_mode, scene):
	"""Triggers a melody for all applicable melody instruments.

	Args:
		melody_instruments (Dictionary of Instruments): A dictionary of all melody instruments to trigger.
		chord (str): A given chord to play (ii, VI, etc.)
		chord_variation (str): A chord variation to play (sus2, dim, etc.)
		key (str): The current key of the song.
		scale_mode (str): The current scale mode of the song (dorian, lydian, etc.)
		scene (str): The current scene (day, evening, etc.)
	"""
	# Clear out the currently-playing melody
	storage.store('active_melody', 'none')

	# Get the notes and the base scale for the melody
	scale_notes = scale_notes_table[scale_notes_table.findCell(scale_mode, caseSensitive=True).row, 'Notes'].val.split(',')
	chord_base_note = min(int(note) for note in chord_table[chord_table.findCell(chord, caseSensitive=True).row, 'Notes Above Root'].val.split(','))
	chord_variation_notes = chord_variations_table[chord_variations_table.findCell(chord_variation, caseSensitive=True).row, 'Notes Above Root'].val.split(',')
	chord_type = chord_table[chord_table.findCell(chord, caseSensitive=True).row, 'Type'].val
	new_variation_type = chord_variations_table[chord_variations_table.findCell(chord_variation, caseSensitive=True).row, 'Type'].val
	override_scale_mode_notes = new_variation_type != 'major' and new_variation_type != 'suspended' and new_variation_type != 'dominant' and chord_type not in ['II', 'III', 'VI', 'VII']
	key_offset = keys_table[keys_table.findCell(key, caseSensitive=True).row, 'Offset'].val

	# Get the melody we should use
	is_transitioning_scenes = volumes[scene] < 0.65 # Not quite full volume but the other scene should be quiet enough at this point
	melody_number = random.randint(0, 3 if is_transitioning_scenes else 7) # If transitioning, limit to intersection scenes
	
	# If the scene is NOT transitioning, then allow pulling from the next melody group in the bank
	match scene:
		# 0-4, 12-15
		case 'morning':
			melody_number -= 4
			if melody_number < 0:
				melody_number += 16
		# 0-8
		case 'day':
			melody_number += 0
		# 4-11
		case 'evening':
			melody_number += 4
		# 8-15
		case 'night':
			melody_number += 8
		# Whatevs
		case _:
			melody_number += 0


	should_trigger_melody = random.randint(0, 1) == 1

	# For each melody instrument:
	for instrument_name, instrument_props in melody_instruments.items():
		# Get the instrument's base note
		base_note = instrument_props.base_note

		# Remove all existing notes from the thing
		op(instrument_name).RemoveNotes(timeStart=0, pitchStart=0, timeEnd=16, pitchEnd=127)
		# op(instrument_name).par.Stopclip.pulse()

		# If we should trigger a melody, choose an available melody from the bank
		# Some notes:
		# Melodies 3, 7, 11, and 15 are all the same, they're considered the "main" melody and are included in every possible "bank"
		if should_trigger_melody:
			storage.store('active_melody', str(melody_number))

			match melody_number:
				# night and morning
				case 0:
					# Main theme variant
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['0', '7', '5', '4'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset,
						ignore_notes=[4, 10]
					)
					notes = (
						(instrument_melody_notes[0], 2.0, 1.0, 100, 0), 
						(instrument_melody_notes[1], 3.0, 1.0, 100, 0), 
						(instrument_melody_notes[2], 4.0, 3.0, 100, 0), 
						(instrument_melody_notes[3], 7.0, 3.0, 100, 0),
					)
				case 1:
					# Discount Clair de Lune (sorry Debussy)
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['7', '7', '4', '2', '4', '2'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset
					)
					notes = (
						(instrument_melody_notes[0] - 12, 0.0, 2.0, 100, 0), 
						(instrument_melody_notes[1], 2.0, 3.0, 100, 0), 
						(instrument_melody_notes[2], 5.0, 3.0, 100, 0), 
						(instrument_melody_notes[3], 8.0, 0.5, 100, 0),
						(instrument_melody_notes[4], 8.5, 0.5, 100, 0),
						(instrument_melody_notes[5], 9.0, 3.0, 100, 0), 
					)
				case 2:
					# Like Real People Do riff (sorry Hozier)
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['9', '7', '4', '2', '4'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset
					)
					notes = (
						(instrument_melody_notes[0], 1.0, 1.0, 100, 0), 
						(instrument_melody_notes[1], 2.0, 1.0, 100, 0), 
						(instrument_melody_notes[2], 3.0, 1.0, 100, 0), 
						(instrument_melody_notes[3], 4.0, 3.0, 100, 0),
						(instrument_melody_notes[4], 7.0, 3.0, 100, 0),
					)
				case 3:
					# Main theme
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['0', '5', '7', '12', '10', '7', '5', '7'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset,
						ignore_notes=[10]
					)
					notes = (
						(instrument_melody_notes[0], 0.0, 1.0, 100, 0), 
						(instrument_melody_notes[1], 1.0, 1.0, 100, 0), 
						(instrument_melody_notes[2], 2.0, 1.0, 100, 0), 
						(instrument_melody_notes[3], 3.0, 1.0, 100, 0), # Always want the flat 7
						(instrument_melody_notes[4], 4.0, 1.0, 100, 0),
						(instrument_melody_notes[5], 5.0, 2.0, 100, 0),
						(instrument_melody_notes[6], 7.0, 1.0, 100, 0),
						(instrument_melody_notes[7], 8.0, 3.0, 100, 0),
					)
				# morning and day
				case 4:
					# Discount Ranz des Vaches (sorry Rossini)
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['12', '14', '7', '12', '16', '7'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset,
					)
					notes = (
						(instrument_melody_notes[0], 0.0, 1.0, 100, 0), 
						(instrument_melody_notes[1], 1.0, 2.0, 100, 0), 
						(instrument_melody_notes[2], 3.0, 1.0, 100, 0), 
						(instrument_melody_notes[3], 4.0, 1.0, 100, 0),
						(instrument_melody_notes[4], 5.0, 2.0, 100, 0),
						(instrument_melody_notes[5], 7.0, 3.0, 100, 0),
					)
				case 5:
					# Variant of main theme
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['0', '7', '9', '5', '7'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset,
						ignore_notes=[10]
					)
					notes = (
						(instrument_melody_notes[0], 0.0, 1.0, 100, 0), 
						(instrument_melody_notes[1], 1.0, 1.0, 100, 0), 
						(instrument_melody_notes[2], 2.0, 1.0, 100, 0), 
						(instrument_melody_notes[3], 3.0, 1.0, 100, 0),
						(instrument_melody_notes[4], 4.0, 3.0, 100, 0), 
					)
				case 6:
					# OMG an original! A little woodwind run riff
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['0', '5', '7', '12', '14', '12'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset
					)
					notes = (
						(instrument_melody_notes[0], 0.0, 0.25, 100, 0), 
						(instrument_melody_notes[1], 0.25, 0.25, 100, 0), 
						(instrument_melody_notes[2], 0.5, 0.25, 100, 0), 
						(instrument_melody_notes[3], 0.75, 0.25, 100, 0),
						(instrument_melody_notes[4], 1.0, 3.0, 100, 0),
						(instrument_melody_notes[5], 4.0, 3.0, 100, 0),
					)
				case 7:
					# Main theme
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['0', '5', '7', '12', '10', '7', '5', '7'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset,
						ignore_notes=[10]
					)
					notes = (
						(instrument_melody_notes[0], 0.0, 1.0, 100, 0), 
						(instrument_melody_notes[1], 1.0, 1.0, 100, 0), 
						(instrument_melody_notes[2], 2.0, 1.0, 100, 0), 
						(instrument_melody_notes[3], 3.0, 1.0, 100, 0), # Always want the flat 7
						(instrument_melody_notes[4], 4.0, 1.0, 100, 0),
						(instrument_melody_notes[5], 5.0, 2.0, 100, 0),
						(instrument_melody_notes[6], 7.0, 1.0, 100, 0),
						(instrument_melody_notes[7], 8.0, 3.0, 100, 0),
					)
				# day and evening
				case 8:
					# Discount Hyrule Field from OOT (the intro)
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['2', '10', '7', '2', '10', '7'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset,
						ignore_notes=[10] # Always want the flat 7
					)
					notes = (
						(instrument_melody_notes[0], 1.0, 0.5, 100, 0), 
						(instrument_melody_notes[1] - 12, 1.5, 0.5, 100, 0), 
						(instrument_melody_notes[2], 2.5, 1.0, 100, 0), 
						(instrument_melody_notes[3], 3.0, 0.5, 100, 0), 
						(instrument_melody_notes[4] - 12 , 3.5, 0.5, 100, 0), 
						(instrument_melody_notes[5], 4.0, 1.0, 100, 0),
					)
				case 9:
					# Seikilos epitaph (measure #1)
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['0', '7', '7', '9', '7'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset
					)
					notes = (
						(instrument_melody_notes[0], 0.0, 2.0, 100, 0), 
						(instrument_melody_notes[1], 2.0, 3.0, 100, 0), 
						(instrument_melody_notes[2], 5.0, 0.125, 100, 0), 
						(instrument_melody_notes[3], 5.125, 0.125, 100, 0),
						(instrument_melody_notes[4], 5.25, 3.0, 100, 0),
					)
				case 10:
					# Some original smthn, a bit of a trumpet riff
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['2', '4', '7', '4'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset
					)
					notes = (
						(instrument_melody_notes[0], 0.0, 0.166, 100, 0), 
						(instrument_melody_notes[1], 0.166, 0.166, 100, 0), 
						(instrument_melody_notes[2], 0.333, 0.166, 100, 0), 
						(instrument_melody_notes[3], 0.5, 3, 100, 0),
					)
				case 11:
					# Main theme
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['0', '5', '7', '12', '10', '7', '5', '7'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset,
						ignore_notes=[10]
					)
					notes = (
						(instrument_melody_notes[0], 0.0, 1.0, 100, 0), 
						(instrument_melody_notes[1], 1.0, 1.0, 100, 0), 
						(instrument_melody_notes[2], 2.0, 1.0, 100, 0), 
						(instrument_melody_notes[3], 3.0, 1.0, 100, 0), # Always want the flat 7
						(instrument_melody_notes[4], 4.0, 1.0, 100, 0),
						(instrument_melody_notes[5], 5.0, 2.0, 100, 0),
						(instrument_melody_notes[6], 7.0, 1.0, 100, 0),
						(instrument_melody_notes[7], 8.0, 3.0, 100, 0),
					)
				# evening and night
				case 12:
					# Discount Hyrule Field from OOT (main riff)
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['0', '7', '0', '12', '10', '9', '7'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset,
						ignore_notes=[10] # Always want the flat 7
					)
					notes = (
						(instrument_melody_notes[0], 0.0, 1.0, 100, 0), 
						(instrument_melody_notes[1] - 12, 1.0, 1.0, 100, 0), 
						(instrument_melody_notes[2], 2.0, 1.0, 100, 0), 
						(instrument_melody_notes[3], 3.0, 1.0, 100, 0), 
						(instrument_melody_notes[4], 4.0, 2.0, 100, 0), # Always want the flat 7
						(instrument_melody_notes[5], 6.0, 2.0, 100, 0),
						(instrument_melody_notes[6], 8.0, 4.0, 100, 0),
					)
				case 13:
					# Main theme variant
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['0', '7', '7', '7', '4'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset
					)
					notes = (
						(instrument_melody_notes[0], 0.0, 1.0, 100, 0), 
						(instrument_melody_notes[1], 1.0, 1.0, 100, 0), 
						(instrument_melody_notes[2], 2.0, 1.0, 100, 0), 
						(instrument_melody_notes[3], 3.0, 1.0, 100, 0), 
						(instrument_melody_notes[4], 4.0, 3.0, 100, 0), 
					)
				case 14:
					# Seikilos epitaph (measure #5)
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['0', '4', '7', '5', '4', '5', '4'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset
					)
					notes = (
						(instrument_melody_notes[0], 1.0, 1.0, 100, 0), 
						(instrument_melody_notes[1], 2.0, 1.0, 100, 0), 
						(instrument_melody_notes[2], 3.0, 1.0, 100, 0), 
						(instrument_melody_notes[3], 4.0, 1.0, 100, 0),
						(instrument_melody_notes[4], 5.0, 1.0, 100, 0),
						(instrument_melody_notes[5], 6.0, 1.0, 100, 0),
						(instrument_melody_notes[6], 7.0, 3.0, 100, 0),
					)
				case 15:
					# Main theme
					instrument_melody_notes = adjust_melody_to_proper_octave(
						notes=['0', '5', '7', '12', '10', '7', '5', '7'],
						base_note=base_note,
						scale_mode_notes=scale_notes,
						chord_base_note=chord_base_note,
						chord_notes=chord_variation_notes,
						override_scale_mode_notes=override_scale_mode_notes,
						key_offset=key_offset,
						ignore_notes=[10]
					)
					notes = (
						(instrument_melody_notes[0], 0.0, 1.0, 100, 0), 
						(instrument_melody_notes[1], 1.0, 1.0, 100, 0), 
						(instrument_melody_notes[2], 2.0, 1.0, 100, 0), 
						(instrument_melody_notes[3], 3.0, 1.0, 100, 0), # Always want the flat 7
						(instrument_melody_notes[4], 4.0, 1.0, 100, 0),
						(instrument_melody_notes[5], 5.0, 2.0, 100, 0),
						(instrument_melody_notes[6], 7.0, 1.0, 100, 0),
						(instrument_melody_notes[7], 8.0, 3.0, 100, 0),
					)

			# Add the melody's notes and play them
			op(instrument_name).SetNotes(notes=notes)
			op(instrument_name).par.Fireclip.pulse()

def generate_chord_variant(chord, chord_variation, scale_mode, grab_random_variant = False):
	"""Generates the notes for a new chord variant, based on a given chord and scale mode.

	Args:
		chord (str): A given chord to play (ii, VI, etc.)
		chord_variation (str): A chord variation to play (sus2, dim, etc.)
		scale_mode (str): The current scale mode of the song (dorian, lydian, etc.)
		grab_random_variant (bool, optional): Should we grab a random variation, or should we follow the transitional variants? Defaults to False.

	Returns:
		multiple:
			- list[int]: The notes of the chord variant, above a given root (0)
			- str: the name of the new variation
	"""
	# Choose a chord variant based on the specified parameter
	if grab_random_variant == True:
		# Choose a random chord variation
		new_variation_row = chord_variations_table.cell(random.randint(1, chord_variations_table.numRows - 1), 0).row
	else:
		# Grab a transition chord variation
		possible_transitions = chord_variations_table[chord_variations_table.findCell(chord_variation, caseSensitive=True).row, 'Possible Transition Variations'].val.split(',')
		new_variation_row = chord_variations_table.findCell(random.choice(possible_transitions), caseSensitive=True).row
	
	# Get the new variation and update its note in it
	new_variation = chord_variations_table[new_variation_row, 'Chord Variation'].val
	new_variation_notes = chord_variations_table[new_variation_row, 'Notes Above Root'].val.split(',')
	new_variation_notes = chord_variations_table[new_variation_row, 'Notes Above Root'].val.split(',')
	new_variation_type = chord_variations_table[new_variation_row, 'Type'].val
	storage.store('chord_variation', new_variation)
	
	# Get the necessary props for adjusting the chord to a given scale
	scale_notes = scale_notes_table[scale_notes_table.findCell(scale_mode, caseSensitive=True).row, 'Notes'].val.split(',')
	chord_base_note = min(int(note) for note in chord_table[chord_table.findCell(chord, caseSensitive=True).row, 'Notes Above Root'].val.split(','))
	chord_type = chord_table[chord_table.findCell(chord, caseSensitive=True).row, 'Type'].val
	chord_variation_notes = chord_variations_table[chord_variations_table.findCell(chord_variation, caseSensitive=True).row, 'Notes Above Root'].val.split(',')

	# Adjust the notes of the chord to the given scale mode and/or chord
	override_scale_mode_notes = new_variation_type != 'major' and new_variation_type != 'suspended' and new_variation_type != 'dominant' and chord_type not in ['II', 'III', 'VI', 'VII']
	new_notes = adjust_to_chord_in_scale_mode(
		notes=new_variation_notes,
		scale_mode_notes=scale_notes,
		chord_base_note=chord_base_note,
		chord_notes=chord_variation_notes,
		mode="chord",
		override_scale_mode_notes=override_scale_mode_notes
	)

	return new_notes, new_variation

def change_notes_for_scene(current_chord_notes, new_chord_notes, key, instruments, scene):
	"""Changes the notes of a set of instruments to match the chord's notes. Has code for smooth transitions of notes.

	Args:
		current_chord_notes (list[str]): The old (previous) notes that were played in a chord, in positions above a root (0).
		new_chord_notes (list[str]): The new notes that were played in a chord, in positions above a root (0).
		key (str): The current key of the song.
		instruments (Dictionary of Instruments): A Dictionary of Instruments for a given scene.
		scene (str): The current scene (day, evening, etc.)
	"""
	# Get the offset for the key
	key_offset = keys_table[keys_table.findCell(key, caseSensitive=True).row, 'Offset']

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
			new_instrument_props = instrument_props
			new_instrument_props.num_voices = 0 # Should be 0 on item already, but force to 0 for safely
			new_instruments[instrument_name] = Instrument(**vars(new_instrument_props))
			continue

		# If it's percussion, we also handle it separately
		elif instrument_props.instrument_role == 'percussion':
			new_instrument_props = instrument_props
			new_instruments[instrument_name] = Instrument(**vars(new_instrument_props))
			continue

		# If it's SFX, just make sure it's playing if it's not
		elif instrument_props.instrument_role == 'sfx':
			new_instrument_props = instrument_props
			new_instruments[instrument_name] = Instrument(**vars(new_instrument_props))

			# Only play the clip if it's not currently playing (via a hacky way of getting if the clip is playing LOL)
			if op(instrument_name + '/out1')['song/_' + instrument_name.replace("_", " ").title().replace(" ", "_") + '/__clip__/0/playing_position'] <= 0:
				# If it's a randomly-triggered clip (manually set bc I'm lazy), then do a chance before kicking it off
				if instrument_name == 'owl_hoots' and random.randint(0, 2) == 0:
					op(instrument_name).par.Fireclip.pulse()
				elif instrument_name != 'owl_hoots':
					op(instrument_name).par.Fireclip.pulse()

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
			new_instrument_notes.append(str(instrument_props.base_note + int(note) + int(key_offset))) # For example, 60 + 5 would 65, so F

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
		new_instrument_props = instrument_props
		new_instrument_props.playing_notes = new_instrument_notes
		new_instruments[instrument_name] = Instrument(**vars(new_instrument_props))
	
	# Store the new values in the dictionary
	base_instruments = storage.fetch('instruments', {}) # We need to get the updated values from other scenes, so we have to directly fetch this from storage instead of passing in as a prop
	storage.store('instruments', base_instruments | {
		scene: new_instruments
	})

# endregion

# region Main Functions

def onOffToOn(channel, sampleIndex, val, prev):
	# Get the current props of the song
	key = storage.fetch('key', 'C')
	scale_mode = storage.fetch('scale_mode', 'ionian')
	chord = storage.fetch('chord', 'I')
	chord_variation = storage.fetch('chord_variation', 'major triad')
	current_notes = storage.fetch('chord_notes', ['0', '4', '7'])
	scenes = storage.fetch('scenes', {})

	new_notes = []
	chord_resolution_type = chord_variations_table[chord_variations_table.findCell(chord_variation, caseSensitive=True).row, 'Tension / Resolution'].val

	# Do any scene-related music controls, which may have changed during time of day operation
	current_scene = storage.fetch('current_scene', 'day')
	current_scene_info = scenes[current_scene]
	next_scene = current_scene_info.next_scene_name

	if not current_scene_info.scale_mode == scale_mode:
		# Update the global storage and local variables
		new_scale_mode = current_scene_info.scale_mode
		storage.store('scale_mode', new_scale_mode)
		scale_mode = new_scale_mode

	# Get the instruments we're working with
	instruments = storage.fetch('instruments', {})
	current_scene_instruments = instruments[current_scene]
	next_scene_instruments = instruments[next_scene]

	# If we should change keys...
	if key_change_driver['pulse'] <= 0:
		# Reset the value of the OP
		key_change_driver.par.resetvalue = random.randint(20, 40)
		key_change_driver.par.resetpulse.pulse()

		# Grab a new key and scale mode, based on the mood and key change limitations
		current_key_row = keys_table.findCell(key, caseSensitive=True).row
		new_key = keys_table[current_key_row, 'Common Key Change Keys'].val.split(',')[random.randint(0, 3)]
		# Update the global storage and local variables
		storage.store('key', new_key)
		key = new_key

		new_scale_mode = current_scene_info.scale_mode
		# Update the global storage and local variables
		storage.store('scale_mode', new_scale_mode)
		scale_mode = new_scale_mode

		# Grab the new notes of the I chord in the new key
		scale_notes = scale_notes_table[scale_notes_table.findCell(scale_mode, caseSensitive=True).row, 'Notes'].val.split(',')
		new_notes = [scale_notes[0], scale_notes[2], scale_notes[4]] # Always I, but intended to that way
		# Update the global storage and local variables
		storage.store('chord_variation', 'major triad')
		chord_variation = 'major triad'
		storage.store('chord', 'I')
		chord = 'I'
		
		# Specify we changed keys
		change_type = "key"

	# Else, check if we should change chords
	elif change_chord_driver['pulse'] <= 0 and chord_resolution_type != 'tension':
		# Reset the value
		change_chord_driver.par.resetvalue = random.randint(0, 3)
		change_chord_driver.par.resetpulse.pulse()

		# Grab a transition chord
		possible_transitions = chord_table[chord_table.findCell(chord, caseSensitive=True).row, 'Common Transitions'].val.split(',')
		new_chord_row = chord_table.findCell(random.choice(possible_transitions), caseSensitive=True).row
		new_chord = chord_table[new_chord_row, 'Chord'].val
		new_chord_notes = chord_table[new_chord_row, 'Notes Above Root'].val.split(',')
		chord_type = chord_table[new_chord_row, 'Type'].val

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
			storage.store('chord_variation', chord_type + ' triad')
			chord_variation = 'major triad'

		# Specify we changed chord
		change_type = "chord"
		
	# Else, shift to a possible variation
	else:
		# Grab a transition chord variation
		new_chord_variant_info = generate_chord_variant(
			chord=chord,
			chord_variation=chord_variation,
			scale_mode=scale_mode,
		)
		new_notes = new_chord_variant_info[0]
		chord_variation = new_chord_variant_info[1]

		# Specify we changed chord variation
		change_type = "chord variation"

	# Handle changing notes based on updated information for the current and next scene
	change_notes_for_scene(
		current_chord_notes=current_notes,
		new_chord_notes=new_notes,
		key=key,
		instruments=current_scene_instruments,
		scene=current_scene,
	)
	change_notes_for_scene(
		current_chord_notes=current_notes,
		new_chord_notes=new_notes,
		key=key,
		instruments=next_scene_instruments,
		scene=next_scene
	)
	
	# Possibly trigger a melody
	melody_instruments = {key: value for key, value in current_scene_instruments.items() if value.instrument_role == 'melody'} | {key: value for key, value in next_scene_instruments.items() if value.instrument_role == 'melody'} # Prolly a better way of doing this
	trigger_melody(
		melody_instruments=melody_instruments,
		chord=chord,
		chord_variation=chord_variation,
		key=key,
		scale_mode=scale_mode,
		scene=current_scene,
	)

	# Also possibly trigger the percussion
	if change_type != "chord variation":
		percussion_instruments = {key: value for key, value in current_scene_instruments.items() if value.instrument_role == 'percussion'} | {key: value for key, value in next_scene_instruments.items() if value.instrument_role == 'percussion'} # Prolly a better way of doing this
		trigger_percussion(percussion_instruments=percussion_instruments)

	# If the scene isn't running, kill all the instruments in it
	# Kill any straggler instruments
	kill_instruments(
		instruments=instruments,
		current_scene=current_scene,
		next_scene=next_scene,
	)
	
	# Update the new variant + notes after the transition happens
	storage.store('chord_notes', new_notes)

	# Update the chord history table
	chord_history.appendRow([scale_mode, key, chord, chord_variation], 0)

	return

def whileOn(channel, sampleIndex, val, prev):
	return

def onOnToOff(channel, sampleIndex, val, prev):
	return

def whileOff(channel, sampleIndex, val, prev):
	return

def onValueChange(channel, sampleIndex, val, prev):
	return

# endregion