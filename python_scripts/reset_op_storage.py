from typing import List, Dict

# me - this DAT
# 
# channel - the Channel object which has changed
# sampleIndex - the index of the changed sample
# val - the numeric value of the changed sample
# prev - the previous sample value
# 
# Make sure the corresponding toggle is enabled in the CHOP Execute DAT.

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
	storage.store('active_melody', 'none')
	storage.store('current_scene', 'night')

	# Instruments are stored grouped by scene, with each instrument being a dictionary of name and props
	instruments: Dict[str, Dict[str, Instrument]] = {
		'morning': {
			"english_horn": Instrument(base_note=54, num_voices=0, instrument_role="melody", scene="morning", playing_notes=[]), # Melody doesn't follow the typical chain, so we set the notes to 0 for safety + set the base note as the min. possible note
			"french_horn": Instrument(base_note=48, num_voices=4, instrument_role="chords", scene="morning", playing_notes=[]),
			"geigan_organ": Instrument(base_note=60, num_voices=4, instrument_role="chords", scene="morning", playing_notes=[]),
			"morning_bells": Instrument(base_note=72, num_voices=4, instrument_role="effects", scene="morning", playing_notes=[]),
			"fifth_morning_pad": Instrument(base_note=48, num_voices=1, instrument_role="effects", scene="morning", playing_notes=[]),
			"morning_sun_pad": Instrument(base_note=60, num_voices=1, instrument_role="effects", scene="morning", playing_notes=[]),
			"sub_bass_morning": Instrument(base_note=36, num_voices=1, instrument_role="bass", scene="morning", playing_notes=[]),
			"morning_birds": Instrument(base_note=0, num_voices=0, instrument_role="sfx", scene="morning", playing_notes=[]),
			"lake_morning": Instrument(base_note=0, num_voices=0, instrument_role="sfx", scene="morning", playing_notes=[]),
		}, 
		'day': {
			"flute": Instrument(base_note=69, num_voices=0, instrument_role="melody", scene="day", playing_notes=[]),
			"strings_hi_day": Instrument(base_note=72, num_voices=1, instrument_role="chords", scene="day", playing_notes=[]),
			"church_organ": Instrument(base_note=60, num_voices=4, instrument_role="chords", scene="day", playing_notes=[]),
			"chimes": Instrument(base_note=60, num_voices=4, instrument_role="effects", scene="day", playing_notes=[]),
			"strings_lo": Instrument(base_note=24, num_voices=1, instrument_role="bass", scene="day", playing_notes=[]),
			"harp": Instrument(base_note=48, num_voices=4, instrument_role="effects", scene="day", playing_notes=[]),
			"suspended_cymbal": Instrument(base_note=48, num_voices=1, instrument_role="percussion", scene="day", playing_notes=[]),
			"day_birds": Instrument(base_note=0, num_voices=0, instrument_role="sfx", scene="day", playing_notes=[]),
			"wind_day": Instrument(base_note=0, num_voices=0, instrument_role="sfx", scene="day", playing_notes=[]),
			"lake_day": Instrument(base_note=0, num_voices=0, instrument_role="sfx", scene="day", playing_notes=[]),
			
		},
		'evening': {
			"brass_ensemble_hi": Instrument(base_note=36, num_voices=0, instrument_role="melody", scene="evening", playing_notes=[]),
			"strings_hi_evening": Instrument(base_note=72, num_voices=1, instrument_role="chords", scene="evening", playing_notes=[]),
			"slow_space_pad": Instrument(base_note=48, num_voices=4, instrument_role="chords", scene="evening", playing_notes=[]),
			"106_organ": Instrument(base_note=60, num_voices=4, instrument_role="effects", scene="evening", playing_notes=[]),
			"gong": Instrument(base_note=36, num_voices=1, instrument_role="percussion", scene="evening", playing_notes=[]),
			"sub_bass_evening": Instrument(base_note=24, num_voices=1, instrument_role="bass", scene="evening", playing_notes=[]),
			"brass_ensemble_lo": Instrument(base_note=24, num_voices=1, instrument_role="bass", scene="evening", playing_notes=[]),
			"wind_evening": Instrument(base_note=0, num_voices=0, instrument_role="sfx", scene="evening", playing_notes=[]),
			"lake_evening": Instrument(base_note=0, num_voices=0, instrument_role="sfx", scene="evening", playing_notes=[]),
		},
		'night' : {
			"gaelic_voices": Instrument(base_note=56, num_voices=0, instrument_role="melody", scene="night", playing_notes=[]),
			"glockenspiel": Instrument(base_note=72, num_voices=1, instrument_role="chords", scene="night", playing_notes=[]),
			"reflectere_piano": Instrument(base_note=48, num_voices=4, instrument_role="chords", scene="night", playing_notes=[]),
			"dreamer_pad": Instrument(base_note=48, num_voices=4, instrument_role="chords", scene="night", playing_notes=[]),
			"that_moment_pad": Instrument(base_note=48, num_voices=4, instrument_role="chords", scene="night", playing_notes=[]),
			"warm_space_pad": Instrument(base_note=48, num_voices=4, instrument_role="chords", scene="night", playing_notes=[]),
			"meditation_pad": Instrument(base_note=60, num_voices=1, instrument_role="effects", scene="night", playing_notes=[]),
			"zen_bowl": Instrument(base_note=72, num_voices=4, instrument_role="effects", scene="night", playing_notes=[]),
			"sub_bass_night": Instrument(base_note=24, num_voices=1, instrument_role="bass", scene="night", playing_notes=[]),
			"cricket_chirps": Instrument(base_note=0, num_voices=0, instrument_role="sfx", scene="night", playing_notes=[]),
			"owl_hoots": Instrument(base_note=0, num_voices=0, instrument_role="sfx", scene="night", playing_notes=[]),
			"lake_night": Instrument(base_note=0, num_voices=0, instrument_role="sfx", scene="night", playing_notes=[]),
		},
	}
	storage.store('instruments', instruments)

	# Reference for scenes
	scenes: Dict[str, Scene] = {
		'morning': Scene(scene_name='morning', next_scene_name='day', scale_mode='lydian'),
		'day': Scene(scene_name='day', next_scene_name='evening', scale_mode='ionian'),
		'evening': Scene(scene_name='evening', next_scene_name='night', scale_mode='mixolydian'),
		'night' : Scene(scene_name='night', next_scene_name='morning', scale_mode='dorian'), #aeolian
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
	