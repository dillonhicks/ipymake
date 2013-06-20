import os

def add_alias(name, pid=0):
	f = open("/proc/taskalias", "w")
	f.write(`pid`+":0:"+name);
	f.close()

def add_alias_track(name, pid=0):
	f = open("/proc/taskalias", "w")
	f.write(`pid`+":1:"+name);
	f.close()

def add_alias_unique(name, pid=0):
	f = open("/proc/taskalias", "w")
	f.write(`pid`+":2:"+name);
	f.close()

def get_aliases():
	d = {}
	f = open("/proc/taskalias")
	for line in f:
		x = line.split(" ")
		pid = int(x[0])
		names = x[1:]
		d[pid] = [n[:-1] for n in names]
	return d

def is_aliased(name, pid=os.getpid()):
	a = get_aliases()
	if pid in a:
		if name in a[pid]:
			return True
	return False
	

