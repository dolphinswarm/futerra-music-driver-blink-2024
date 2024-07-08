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

# INSTRUMENT PROPS
# instruments = {
# 	"synth_pad": {},
#   "meditation_pad": {},
# 	"zen_bowl": {},
#	"bass_drone": {},
# }

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

def onOffToOn(channel, sampleIndex, val, prev):
	# Storage all the basic song properties
	storage = op('storage_op')
	storage.store('key', 'C')
	storage.store('scale_mode', 'ionian')
	storage.store('chord', 'I')
	storage.store('chord_variation', 'major triad')
	storage.store('chord_notes', ['0', '4', '7'] )

	# Store instruments in a dictionary, then save that in storage
	instruments: Dict[str, Instrument] = {
		# Meditative
		"synth_pad": Instrument(base_note=60, num_voices=4, instrument_role="chords", playing_notes=[]),
		"meditation_pad": Instrument(base_note=60, num_voices=1, instrument_role="effects", playing_notes=[]),
		"zen_bowl": Instrument(base_note=72, num_voices=4, instrument_role="effects", playing_notes=[]),
		"bass_drone": Instrument(base_note=24, num_voices=1, instrument_role="bass", playing_notes=[]),

		# Retro
		"synth_melody": Instrument(base_note=60, num_voices=0, instrument_role="melody", playing_notes=[]), # Melody doesn't follow the typical chain, so we set the notes to 0 for safety
		"synth_pad_retro": Instrument(base_note=60, num_voices=4, instrument_role="chords", playing_notes=[]),
		"synth_arpeggiator": Instrument(base_note=60, num_voices=4, instrument_role="effects", playing_notes=[]),
		"bass_drone_retro": Instrument(base_note=24, num_voices=1, instrument_role="bass", playing_notes=[]),

		# Church
		"choir_melody": Instrument(base_note=60, num_voices=0, instrument_role="melody", playing_notes=[]),
		"choir_ahs": Instrument(base_note=60, num_voices=4, instrument_role="chords", playing_notes=[]),
		"strings_hi": Instrument(base_note=72, num_voices=1, instrument_role="chords", playing_notes=[]),
		# "strings_mid": Instrument(base_note=48, num_voices=4, instrument_role="chords", playing_notes=[]),
		"strings_lo": Instrument(base_note=24, num_voices=1, instrument_role="bass", playing_notes=[]),
		"church_organ": Instrument(base_note=60, num_voices=4, instrument_role="chords", playing_notes=[]),
		"chimes": Instrument(base_note=60, num_voices=4, instrument_role="effects", playing_notes=[]),
	}

	# Store the dictionary in storage
	storage.store('instruments', instruments)
	
	return

def whileOn(channel, sampleIndex, val, prev):
	return

def onOnToOff(channel, sampleIndex, val, prev):
	return

def whileOff(channel, sampleIndex, val, prev):
	return

def onValueChange(channel, sampleIndex, val, prev):
	return
	