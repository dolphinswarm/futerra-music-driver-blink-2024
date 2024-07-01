# me - this DAT
# 
# channel - the Channel object which has changed
# sampleIndex - the index of the changed sample
# val - the numeric value of the changed sample
# prev - the previous sample value
# 
# Make sure the corresponding toggle is enabled in the CHOP Execute DAT.

storage = op('storage_op')

def onOffToOn(channel, sampleIndex, val, prev):
	# This script just kills all running instruments LOL
	# Need to filter to remove the title
	instruments = storage.fetch('instruments', {})
	for instrument in instruments:
		op(instrument).SendMIDI('flush')
		op(instrument).par.Clearchop.pulse()

	return

def whileOn(channel, sampleIndex, val, prev):
	return

def onOnToOff(channel, sampleIndex, val, prev):
	return

def whileOff(channel, sampleIndex, val, prev):
	return

def onValueChange(channel, sampleIndex, val, prev):
	return
	