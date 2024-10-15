# me - this DAT
# 
# channel - the Channel object which has changed
# sampleIndex - the index of the changed sample
# val - the numeric value of the changed sample
# prev - the previous sample value
# 
# Make sure the corresponding toggle is enabled in the CHOP Execute DAT.

storage = op('storage_op')
timer = op('Compound_Timer')
d3_osc = op('d3_osc')

def onOffToOn(channel, sampleIndex, val, prev):
	# Reset to morning on the scene
	storage.store('current_scene', 'night')
	timer.par.Initialize.pulse()
	timer.par.Start.pulse()
	op('Compound_Timer/loop_count').par.const0value = 0
	d3_osc.sendOSC('/d3/showcontrol/cue', [101])

	return

def whileOn(channel, sampleIndex, val, prev):
	return

def onOnToOff(channel, sampleIndex, val, prev):
	return

def whileOff(channel, sampleIndex, val, prev):
	return

def onValueChange(channel, sampleIndex, val, prev):
	return
	