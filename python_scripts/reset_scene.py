# me - this DAT
# 
# channel - the Channel object which has changed
# sampleIndex - the index of the changed sample
# val - the numeric value of the changed sample
# prev - the previous sample value
# 
# Make sure the corresponding toggle is enabled in the CHOP Execute DAT.

storage = op('storage_op')
timer = op('timer')
scene_counter = op('scene_counter')

def onOffToOn(channel, sampleIndex, val, prev):
	# Reset to morning on the scene
	storage.store('current_scene', 'morning')
	storage.store('next_scene', 'day')
	timer.par.initialize.pulse()
	timer.par.start.pulse()
	scene_counter.par.resetpulse.pulse()

	return

def whileOn(channel, sampleIndex, val, prev):
	return

def onOnToOff(channel, sampleIndex, val, prev):
	return

def whileOff(channel, sampleIndex, val, prev):
	return

def onValueChange(channel, sampleIndex, val, prev):
	return
	