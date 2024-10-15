# me - this DAT
# 
# channel - the Channel object which has changed
# sampleIndex - the index of the changed sample
# val - the numeric value of the changed sample
# prev - the previous sample value
# 
# Make sure the corresponding toggle is enabled in the CHOP Execute DAT.

storage = op('storage_op')
event_driver = op('event_driver')
song_props = op('song_props')
chord_history = op('chord_history')

def onOffToOn(channel, sampleIndex, val, prev):
	# Reset the event driver (which tracks global time)
	event_driver.par.resetpulse.pulse()

	# Also reset global time for good measure
	# me.time.frame = 1

	# Also also reset Ableton
	# song_props.par.Stop.pulse() TODO FIGURE OUT WHY NOT WORKING AS EXPECTED

	# Clear the chord history
	while chord_history.numRows > 1:
		chord_history.deleteRow(chord_history.numRows - 1)

	# Kill all the running instruments
	instruments = storage.fetch('instruments', {})
	for scene in instruments.values():
		for instrument_name, instrument_props in scene.items():
			# print(instrument_name)

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

	return

def whileOn(channel, sampleIndex, val, prev):
	return

def onOnToOff(channel, sampleIndex, val, prev):
	return

def whileOff(channel, sampleIndex, val, prev):
	return

def onValueChange(channel, sampleIndex, val, prev):
	return
	