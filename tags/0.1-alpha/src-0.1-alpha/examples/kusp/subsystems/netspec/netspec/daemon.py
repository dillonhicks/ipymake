import protocol
#from pykusp import configfile
import pykusp.configutility as configfile
import os
import sys

NS_OK = 0
NS_WARNING = 1
NS_OK_EXIT = 2
NS_ERROR = 3
NS_DIED = 4


phase_table = {}

rfile = None
wfile = None

ack_flag = 0

def ns_set_execute(phase_name, spec, func):
	global phase_table
	phase_table[phase_name] = (spec, func)

def ns_acknowledge(err, message=None, filename=None, data=None):
	print "daemon SEnding ack",err,message,filename,data

	global ack_flag


	if type(filename) is str:
		filename = [filename]
	
	retval = {"error" : err}


	if filename:
		retval["files"] = filename
	if data:
		retval["config"] = data
	if message:
		retval["message"] = message


	ack_flag = True
	protocol.write_config(wfile, retval)
	
	if err == NS_OK or err == NS_WARNING:
		return
	elif err == NS_OK_EXIT:
		sys.exit(0)
	else:
		sys.exit(1)

def ns_begin(fd):
	global wfile, rfile, ack_flag
	
	wfile = os.fdopen(fd, "w")
	rfile = os.fdopen(fd, "r")

	while True:
		phase_config = protocol.read_config(rfile)
		ack_flag = False

		name = phase_config["phase_name"]
		params = phase_config["params"]

		try:
			spec, func = phase_table[name]
		except KeyError, ke:
			print "NETSPEC: Ignoring unknown phase", name
			continue

		if spec:
			try:
				params = configfile.check_config(params, spec)
			except Exception, e:
				print "BAD PARAMETERS FOR PHASE",name
				print e
				ns_acknowledge(NS_ERROR, None, None, params)



		print "NETSPEC: Executing phase",name

		func(params)

		print "NETSPEC: Phase",name,"complete"
		
		if not ack_flag:
			ns_acknowledge(NS_OK)



