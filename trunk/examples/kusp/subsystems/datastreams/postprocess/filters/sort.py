"""Filters to sort datastreams by various methods."""

from datastreams.postprocess import filtering
from datastreams.postprocess import entities
from datastreams import namespaces

#Only have sort by TSC and Sequence number for now--what else can we sort by

class sort_time(filtering.Filter):
	"""Sorts datastream by time."""

	expected_parameters = {
		"sort_key" : {
			"types": "string",
			"doc" : "Time units to sort by",
			"default": "tsc"
		},
	}

	def initialize(self):
		self.entities = []
		
		self.key = self.params["sort_key"]
		

	def process(self, entity):
		self.entities.append(entity)

	def finalize(self):
		#Sort entities by time value
		self.entities.sort(key=lambda e: e.get_log_time()[self.key].get_value())
		
		#Send the sorted entities along the pipeline
		while self.entities:
			self.send(self.entities.pop(0))

	pass

class sort_seq(filtering.Filter):
	"""Sorts datastream by sequence number."""

	def initialize(self):
	    self.entities = []
	
	def process(self, entity):
	    self.entities.append(entity)
	
	def finalize(self):
		#Sort entities by sequence number
	    self.entities.sort(key=lambda e: e.get_time_object("log","sequence").get_value())
	    
	    #Pass sorted entities along pipeline
	    while self.entities:
	        self.send(self.entities.pop(0))
	



