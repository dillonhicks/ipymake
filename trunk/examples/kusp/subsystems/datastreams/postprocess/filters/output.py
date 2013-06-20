from datastreams.postprocess.filtering import *
import cPickle
from datastreams.postprocess.ppexcept import *
import tempfile
import datastreams.postprocess.queues as queues
import datastreams.postprocess.inputs as inputs
import struct
import os


	
class xml(OutputFilter):

	expected_parameters = {
		"filename" : {
			"types" : ["string"],
			"required" : True,
		}
	}


	def __init__(self, params):
		Filter.__init__(self, params)
		raise Exception("XML output unimplemented")

	def finalize(self):
		pass

	def process(self, entity):
		#write entity to file as XML data......
		pass

class pickle(OutputFilter):

	expected_parameters = {
		"picklelevel" : {
			"types" : ["integer"],
			"default" : 0,
		},
		"filename" : {
			"types" : ["string"],
			"required" : True,
		}
	}

	def __init__(self, params):
		Filter.__init__(self, params)

	def initialize(self):
		self.outfile = open(self.params["filename"], "wb")
		
		magicbin = struct.pack(inputs.magic_format,
				inputs.picklemagic)
		self.outfile.write(magicbin)

		# binary pickle format 2 and up don't work...
		self.pickler = cPickle.Pickler(self.outfile, 
				self.params["picklelevel"])
	
	def finalize(self):
		self.pickler.dump(entities.PipelineEnd())
		# FIXME: seek to beginning and write number of entities in stream
		self.outfile.close()
		pass

	def process(self, entity):
		entity.clear_cache()
		self.pickler.dump(entity)
		self.send(entity)

	def abort(self):
		self.outfile.close()
		os.remove(self.params["filename"])


