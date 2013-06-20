from datastreams.postprocess.headfilter import *
from datastreams.postprocess import inputs
from datastreams.postprocess.ppexcept import *
import glob
import threading
import socket



class PostprocessSocketListener(threading.Thread):
	def __init__(self, headfilter, port):
		threading.Thread.__init__(self)
		self.headfilter = headfilter
		self.port = port
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
		sock.bind(('', self.port))
		sock.listen(1)
		print "BOUND TO PORT", self.port
		self.sock = sock

	
	def accept_connection(self):
		sock = self.sock
		conn, addr = sock.accept()
		name = `addr`
		print "CONNECTION FROM",name
		inp = inputs.RawInputSource(name,
				self.headfilter.params["extra_data"],
				infile = conn.makefile("r"))
		self.headfilter.add_input_source(inp)
		self.headfilter.lock.acquire()
		e = self.headfilter.fetch(name)
		self.headfilter.next_entity[name] = e
		self.headfilter.lock.release()


	def run(self):
		while (1):
			self.accept_connection()
			
class input(HeadFilter):

	expected_parameters = {
		"file" : {
			"types" : "list",
			"doc" : "List of input files to read",
			"default" : [],
			"listdef" : {
				"types" : "string"
				},
			},
		"streaming_file" : {
			"types" : "list",
			"doc" : "List of streaming input files to read",
			"default" : [],
			"listdef" : {
				"types" : "string"
				},
			},
		"network_port" : {
			"types" : "integer",
			"doc" : "Port to listen for incoming connections",
			"default" : 0,
			},
		"socket_num" : {
			"types" : "integer",
			"doc" : "Number of connections to wait for",
			"default" : 0,
			},
		"conn" : {
			"types" : "list",
			"doc" : "List of other pipelines to connect to",
			"default" : [],
			"listdef" : {
				"types" : ["invocation"],
				"openinvodef" : {
					"output" : {
						"types" : ["string"],
						"default" : "default",
						},
					"queue_params" : {
						"types" : ["dictionary"],
						"default" : {},
						},
					"index" : {
						"types" : ["integer"],
						"default" : -1,
						},
					},
				},
			},
		"extra_data" : {
			"types" : "list",
			"doc" : "List of extra data decoder modules",
			"default" : [],
			"listdef" : {
				"types" : "string"
				},
			},
		"namespace" : {
			"doc" : "Namespace for entities created in this pipeline",
			"types" : ["dictionary", "string", "list"],
			"listdef" : {
				"types" : ["string"],
				"doc" : "Namespaces",
			},
			"default" : {}
		},
		"convert_timestamps" : {
			"doc" : "Convert timestamps",
			"types" : ["boolean"],
			"default" : False,
		},
	}


	def initialize(self):
		self.clockinfo = {}
		self.clockevent = self.namespace["DSTREAM_ADMIN_FAM/TIME_STATE"].get_id()
		self.convert = self.params["convert_timestamps"]
		if self.convert:
			self.warn("'convert_timestamps' option has known problems, use utility.timestamp()")

	

	def choose_next(self, entitydict):
		sourceids = entitydict.keys()
		min_sourceid = sourceids[0]
		min_time = entitydict[min_sourceid]
		min_sourceid = sourceids[0]

		for i in range(1, len(sourceids)):
			sourceid = sourceids[i]
			entity = entitydict[sourceid]
			if entity < min_time:
				min_time = entity
				min_sourceid = sourceid
		return min_sourceid

	def postprocess(self, entity):
		if not self.convert:
			return entity


		cid = entity.get_cid()
		machine = entity.get_machine()
		
		if cid == self.clockevent:
			# this is a clock synchronization event, and we need to update
			# our variables that assist in tsc-to-ns conversion
			self.clockinfo[machine] = entity.get_extra_data()

			print self.clockevent, machine, self.clockinfo[machine]

			self.clockinfo[machine]["nsecs"] = long(
				(self.clockinfo[machine]["tv_sec"] * 10**9) +
				 self.clockinfo[machine]["tv_nsec"])
			self.clockinfo[machine]["event"] = entity

			entity = self.preprocess(entity)
			
		return entity

	def preprocess(self, entity):
		if not self.convert:
			return entity
		
		cid = entity.get_cid()
		machine = entity.get_machine()
		
		if machine not in self.clockinfo:
			# we haven't gotten any timekeeping events for this machine
			# run the postprocess method, which will acquire timekeeping info
			# if this is a clock event. this scenario will always happen with
			# the very first event in a binary
			entity = self.postprocess(entity)
			if machine not in self.clockinfo:
				return entity

		# convert timestamps to nanoseconds
		for timetype in entity.get_times().values():
			# TODO: add uncertainty to converted timestamps
			#       refactor tsc-based histograms
			
			tsc = timetype["tsc"].get_value()
			offset_tsc = tsc - self.clockinfo[machine]["tsc"]

			#if offset_tsc < 0:
			#	raise Exception("Offset TSC is negative")

			offset_nsecs = ((offset_tsc * 
					self.clockinfo[machine]["mult"]) 
					>> self.clockinfo[machine]["shift"])
			

			timetype["ns"] = entities.TimeMeasurement(
					"ns", self.clockinfo[machine]["nsecs"] + 
					long(offset_nsecs),
					"global", 0, 0)	
		return entity

	def establish_connections(self):
		params = self.params
		pipeline = self.pipeline

		filelist = []

		# open input files
		for filename in self.params["file"]:
			x = glob.glob(filename)
			if not x:
				raise ConstructionException("Bad input filename "+filename)
			filelist.extend(x)	
		for filename in filelist:
			self.info("Opening input file "+`filename`)
			intype = inputs.determine_file_type(filename)
			if intype == "raw":
				i = inputs.RawInputSource(filename, 
						self.params["extra_data"])
			elif intype == "pickle":
				i = inputs.PickleInputSource(filename)
			elif intype == "xml":
				i = inputs.XMLInputSource(filename)

			self.add_input_source(i)

		for filename in self.params["streaming_file"]:
			i = inputs.OnlineRawInputSource(filename, 
					self.params["extra_data"],
					endless=True)
			self.add_input_source(i)


		# setup connections to other pipelines
		for pipename, params in self.params["conn"]:
			self.info("Creating input source to "+pipename+":"+params["output"])
			i = inputs.PipelineInputSource(
					pipename,
					params["output"],
					params["queue_params"],
					params["index"],
					pipeline)
			self.add_input_source(i)
	
		if self.params["network_port"]:
			self.sl = PostprocessSocketListener(self, self.params["network_port"])
			self.sl.setDaemon(True)

			for i in range(self.params["socket_num"]):
				self.sl.accept_connection()

			self.sl.start()

		# inject user-supplied namespace, if given
		ns = self.params["namespace"]
		if ns:
			self.info("Creating source for injected namespace")
			i = inputs.NamespaceInputSource(ns)
			self.add_input_source(i)


		
