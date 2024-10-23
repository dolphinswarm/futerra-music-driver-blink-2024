# me - this DAT
# 
# frame - the current frame
# state - True if the timeline is paused
# 
# Make sure the corresponding toggle is enabled in the Execute DAT.

# region OPs
song_data = op('song_data')
morning_instrument_data = op('morning_instrument_data')
day_instrument_data = op('day_instrument_data')
evening_instrument_data = op('evening_instrument_data')
night_instrument_data = op('night_instrument_data')
storage = op('storage_op')

# endregion

# region Helper Maps and Arrays
key_map = {
    'C': 0,
    'C#': 1,
    'D': 2,
    'D#': 3,
    'E': 4,
    'F': 5,
    'F#': 6,
    'G': 7,
    'G#': 8,
    'A': 9,
    'A#': 10,
    'B': 11
}

scale_mode_map = {
	'lydian': 0,
	'ionian': 1,
	'mixolydian': 2,
	'dorian': 3
}

current_scene_map = {
	'morning': 0,
	'day': 1,
	'evening': 2,
	'night': 3
}

chord_map = {
	'I': 0,
	'ii': 1,
	'iii': 2,
	'IV': 3,
	'V': 4,
	'vi': 5,
	'vii*': 6,
	'VI': 78,
	'VII': 9,
	'II': 10,
	'III': 11
}

chord_variation_map = {
    'major triad': 0,
    'minor triad': 1,
    'diminished triad': 2,
    'augmented triad': 3,
    'sus2': 4,
    'sus4': 5,
    '6': 6,
    'dominant 7': 7,
    'major 7': 8,
    'half-diminished 7': 9,
    'diminished 7': 10,
    'add9': 11
}

active_melody_map = {
	'none': 0,
	# Main melody
	'3': 1,
	'7': 1,
	'11': 1,
	'15': 1,
	# Time-dependent melodies
	'0': 2,
	'1': 3,
	'2': 4,
	'4': 5,
	'5': 6,
	'6': 7,
	'8': 8,
	'9': 9,
	'10': 10,
	'12': 11,
	'13': 12,
	'14': 13
}

items_to_pull = ['key', 'scale_mode', 'chord', 'chord_variation', 'current_scene', 'active_melody']

# endregion

def onStart():
	return

def onCreate():
	return

def onExit():
	return

def onFrameStart(frame):
	# For each item, get information from the storage and set the appropriate OP for OSC export
	for i, item in enumerate(items_to_pull):
		storage_val = storage.fetch(item)
		song_data.par['const' + str(i) + 'name'] = item
		song_data.par['const' + str(i) + 'value'] = globals()[item + '_map'][storage_val]

	# For each instrument, make a channel for its data
	storage_instrument_data = storage.fetch('instruments', {})
	for scene_name, scene_data in storage_instrument_data.items():
		i = 0
		for instrument_name, instrument_props in scene_data.items():
			for note in range(instrument_props.num_voices):
				globals()[scene_name + '_instrument_data'].par['const' + str(i) + 'name'] = instrument_name + '_note' + str(note + 1)
				globals()[scene_name + '_instrument_data'].par['const' + str(i) + 'value'] = instrument_props.playing_notes[note] if note < len(instrument_props.playing_notes) else 0
				i += 1

	return

def onFrameEnd(frame):
	return

def onPlayStateChange(state):
	return

def onDeviceChange():
	return

def onProjectPreSave():
	return

def onProjectPostSave():
	return

	