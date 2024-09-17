import random
from typing import List
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
	base_note: int
	num_voices: int
	instrument_role: str # Possible roles: bass, chords, effects, melody, event
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

bell_event_driver = op('bell_event_driver')
light_trigger = op('light_trigger')
storage = op('storage_op')

# endregion

# region Helper Functions

def normalize_notes(notes):
	"""
	Normalizes notes to a single octave (pitch class)

	Parameters:
	notes (str array of numbers): the given notes of a chord, each chromatically above a root of 0

	Returns:
	An int array of notes in a given chord, normalized to be within a single octave
	"""
	return [int(note) % 12 for note in notes]

# endregion

def onOffToOn(channel, sampleIndex, val, prev):
	return

def whileOn(channel, sampleIndex, val, prev):
	return

def onOnToOff(channel, sampleIndex, val, prev):
	# Get the metadata and instruments for the scene
	current_scene = storage.fetch('current_scene', 'day')
	next_scene = storage.fetch('next_scene', 'night')
	instruments = storage.fetch('instruments', {})
	current_chord_notes = storage.fetch('current_chord_notes', ['0', '4', '7'])
	current_scene_instruments = instruments[current_scene]
	next_scene_instruments = instruments[next_scene]
	
	event_instruments = {key: value for key, value in current_scene_instruments.items() if value.instrument_role == 'event'} | {key: value for key, value in next_scene_instruments.items() if value.instrument_role == 'event'}

	# Make any event instruments play a note
	for instrument_name, instrument_props in event_instruments.items():
		# Stop any existing MIDI notes
		for note in instrument_props.playing_notes:
			op(instrument_name).SendMIDI('note', int(note), 0)

		# Play a random new midi note
		normalized_current_chord_notes = normalize_notes(current_chord_notes)
		new_note = instrument_props.base_note + int(random.choice(normalized_current_chord_notes)) # For example, 60 + 5 would 65, so F
		op(instrument_name).SendMIDI('note', int(new_note), 100)

		# Add the new instrument object
		new_instrument_props = instrument_props
		new_instrument_props.playing_notes = [str(new_note)]
		new_instrument = Instrument(**vars(new_instrument_props))

		# Store the new values in the dictionary
		scene = instrument_props.scene
		base_instruments = storage.fetch('instruments', {}) # We need to get the updated values from other scenes, so we have to directly fetch this from storage instead of passing in as a prop
		base_scene_instruments = instruments[scene]
		storage.store('instruments', base_instruments | {
			scene: base_scene_instruments | {
				instrument_name: new_instrument
			}
		})

	# Reset the bell driver
	bell_event_driver.par.resetvalue = random.randint(1, 10)
	bell_event_driver.par.resetpulse.pulse()

	# Pulse the light trigger
	light_trigger.par.value0.pulse(1, frames = 1)

	return

def whileOff(channel, sampleIndex, val, prev):
	return

def onValueChange(channel, sampleIndex, val, prev):
	return
	