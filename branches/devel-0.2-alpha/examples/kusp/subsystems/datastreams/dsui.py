import dsui_mod
import cPickle

def null_event(group, name, tag=0, data=None):
	pass

event = null_event

declare = dsui_mod.declare

write_time = dsui_mod.write_time

printf = dsui_mod.printf

close = dsui_mod.close

def _event(group, name, tag=0, data=None):
	if (data != None):
		data = cPickle.dumps(data)
		dsui_mod.log_event(group, name, tag, data)
	else:
		dsui_mod.log_event(group, name, tag)

def start(filename, buffers=16):
	global event
	dsui_mod.init(filename, buffers)
	event = _event
