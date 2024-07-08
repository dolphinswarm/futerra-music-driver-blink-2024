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

def onOffToOn(channel, sampleIndex, val, prev):
	# Reset the event driver (which tracks global time)
	event_driver.par.resetpulse.pulse()

	# This script just kills all running instruments LOL
	instruments = storage.fetch('instruments', {})
	for instrument_name, instrument_props in instruments.items():
		# If a melody, reset its clip
		if instrument_props.instrument_role == 'melody':
			# Remove all existing notes
			op(instrument_name).RemoveNotes(timeStart=0, pitchStart=0, timeEnd=8, pitchEnd=127)
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
	