try:
	import cPickle as pickle
except:
	import pickle
import socket
import struct

def read_config(fd):
	b = struct.calcsize("i")
	s = fd.read(b)
	sz = struct.unpack("i", s)[0]
	if (sz > 32767):
		print "BAD SIZE", sz
		return {}

	cfg = fd.read(sz)
	try:
		retval = pickle.loads(cfg)
	except:
		raise
	return retval

def write_config(fd, config):
	try:
		message = pickle.dumps(config)
	except:
		raise
	sz_data = struct.pack("i", len(message))
	fd.write(sz_data)
	fd.flush()

	fd.write(message)
	fd.flush()

def send_message(host, port, cfg):
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	try:
		sock.connect((host, port))
		fd = sock.makefile('w')
		write_config(fd, cfg)
		sock.close()
	except:
		raise
	

def parse_host_string(hoststring):
	userstring = None
	ruser = None
	rport = 22
	host = None
	rpassword = None
	
	u = hoststring.split('@')
	if len(u) == 2:
		userstring, hoststring = u
	else:
		hoststring = u[0]
	if userstring:
		u = userstring.split(':')
		if len(u) == 2:
			ruser, rpassword = u
		else:
			ruser = u[0]
	u = hoststring.split(':')
	if len(u) == 2:
		host, rport = u
	else:
		host = u[0]

	return host, rport, ruser, rpassword

 

