from typing import List, Dict

# me - this DAT
# 
# channel - the Channel object which has changed
# sampleIndex - the index of the changed sample
# val - the numeric value of the changed sample
# prev - the previous sample value
# 
# Make sure the corresponding toggle is enabled in the CHOP Execute DAT.

# ================ Items in storage + defaults
# SONG PROPS
# key = 'C'
# scale_mode = 'ionian'
# chord = 'I'
# chord_variation = 'major triad'
# chord_notes = []
# current_scene = 'day'

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

class Scene:
	# Props
	scene_name: str
	next_scene_name: str
	scale_mode: str

	# Methods
	def __init__(self, scene_name: str, next_scene_name: str, scale_mode: str):
		self.scene_name = scene_name
		self.next_scene_name = next_scene_name
		self.scale_mode = scale_mode

def onOffToOn(channel, sampleIndex, val, prev):
	# Storage all the basic song properties
	storage = op('storage_op')
	storage.store('key', 'C')
	storage.store('scale_mode', 'ionian')
	storage.store('chord', 'I')
	storage.store('chord_variation', 'major triad')
	storage.store('chord_notes', ['0', '4', '7'] )
	storage.store('current_scene', 'day')
	storage.store('next_scene', 'evening')

	# Instruments are stored grouped by scene, with each instrument being a dictionary of name and props
	instruments: Dict[str, Dict[str, Instrument]] = {
		'morning': {}, #TODO
		'day': {
			"strings_hi": Instrument(base_note=72, num_voices=1, instrument_role="chords", scene="day", playing_notes=[]),
			"strings_lo": Instrument(base_note=24, num_voices=1, instrument_role="bass", scene="day", playing_notes=[]),
			"church_organ": Instrument(base_note=60, num_voices=4, instrument_role="chords", scene="day", playing_notes=[]),
			# "chimes": Instrument(base_note=60, num_voices=4, instrument_role="effects", scene="day", playing_notes=[]),
			"event_chimes": Instrument(base_note=60, num_voices=0, instrument_role="event", scene="day", playing_notes=[]),
		},
		'evening': {}, #TODO
		'night' : {
			"strings_melody": Instrument(base_note=48, num_voices=0, instrument_role="melody", scene="night", playing_notes=[]), # Melody doesn't follow the typical chain, so we set the notes to 0 for safety
			"meditation_pad": Instrument(base_note=60, num_voices=1, instrument_role="effects", scene="night", playing_notes=[]),
			# "zen_bowl": Instrument(base_note=72, num_voices=4, instrument_role="effects", scene="night", playing_notes=[]),
			"event_zen_bowl": Instrument(base_note=72, num_voices=0, instrument_role="event", scene="night", playing_notes=[]), # Same with event
			"bass_drone": Instrument(base_note=24, num_voices=1, instrument_role="bass", scene="night", playing_notes=[]),
			# "burnt_sun_pad": Instrument(base_note=48, num_voices=4, instrument_role="chords", playing_notes=[]),
			"dreamer_pad": Instrument(base_note=48, num_voices=4, instrument_role="chords", scene="night", playing_notes=[]),
			"106_organ": Instrument(base_note=60, num_voices=4, instrument_role="effects", scene="night", playing_notes=[]),
		},
		'late_night': {} #TODO
	}
	storage.store('instruments', instruments)

	# Reference for scenes
	scenes: Dict[str, Scene] = {
		'morning': Scene(scene_name='morning', next_scene_name='day', scale_mode='lydian'),
		'day': Scene(scene_name='day', next_scene_name='evening', scale_mode='ionian'),
		'evening': Scene(scene_name='evening', next_scene_name='night', scale_mode='mixolydian'),
		'night' : Scene(scene_name='night', next_scene_name='late_night', scale_mode='aeolian'),
		'late_night' : Scene(scene_name='late_night', next_scene_name='morning', scale_mode='dorian'),
	}
	storage.store('scenes', scenes)

	return

def whileOn(channel, sampleIndex, val, prev):
	return

def onOnToOff(channel, sampleIndex, val, prev):
	return

def whileOff(channel, sampleIndex, val, prev):
	return

def onValueChange(channel, sampleIndex, val, prev):
	return
	