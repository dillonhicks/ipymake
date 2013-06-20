
"""Filters to reduce entities into aggregate stats"""

from datastreams.postprocess import filtering, entities


class AbstractReduce(filtering.Filter):
	expected_parameters = {
		"operation" : {
			"doc" : "operation to perform",
			"types" : "string",
			"constraints" : ["sum", "mean", "min", "max", "median"],
			"required" : True
		},
		"dest_event" : {
			"doc" : "generated event for reduced data, extra data with value",
			"types" : "string"
		},
		"consume" : {
			"types" : "boolean",
			"doc" : "Whether to delete matching entities after processing",
			"default" : False
		}
	}



	def initialize(self):
		self.vals = []
		self.consume = self.params["consume"]

	output_names = ["default", "reduced"]

	def finalize(self):
		if not self.vals:
			self.warn("No matching data to reduce")
			return


		self.info("Performing reduction...")

		result = self.vals[0]

		if self.params["operation"] == "sum":
			for v in self.vals[1:]:
				result = result + v
		elif self.params["operation"] == "min":
			for v in self.vals[1:]:
				if v < result:
					result = v
		elif self.params["operation"] == "max":
			for v in self.vals[1:]:
				if v > result:
					result = v
		elif self.params["operation"] == "mean":
			mean = 0.0
			for v in self.vals:
				mean = mean + float(v)
			mean = mean / len(self.vals)
			
			variance = 0.0
			for v in self.vals:
				variance = variance + (mean - float(v))**2
			variance = variance / len(self.vals)

			result = (mean, variance)

		elif self.params["operation"] == "median":
			sz = len(self.vals)
			valscpy = self.vals[:]
			valscpy.sort()
			if sz & 1:
				result = float(valscpy[sz // 2])
			else:
				result = (float(valscpy[sz // 2 - 1]) + 
						float(valscpy[sz // 2])) / 2.0

		spec = self.namespace[self.params["dest_event"]]
		e = entities.Event(spec.get_id(), entities.get_zero_timedict(),
				None, result)

		self.info("Finished.")
		self.send_output("reduced", e)



class event(AbstractReduce):
	"""filter to reduce event data by a specific operation,
	and write a new event tagged with the result"""

	def __init__(self, params):
		# hack to 'inherit' parameters
		self.expected_parameters.update(self.subclass_expected_parameters)
		AbstractReduce.__init__(self, params)
	

	subclass_expected_parameters = {
		"data" : {
			"doc" : "data to use from source event",
			"types" : "invocation",
			"default" : ("tag",{}),
			"invodef" : {
				"tag" : {},
				"extra_data" : {
					"item" : {
						"types" : "list",
						"listdef" : {
							"types" : "string"
						},
						"default" : []
					}
				},
				"time" : {
					"units" : {
						"types" : "string",
						"default" : "ns",
					}
				}
			}
		},
		"src_event" : {
			"doc" : "event to obtain data",
			"types" : "string"
		},
	}


	def initialize(self):
		AbstractReduce.initialize(self)
		self.datasource, self.dataparam = self.params["data"]
		self.event_ptr = self.get_ns_pointer(self.params["src_event"])
		
	def process(self, entity):
		if entity.get_cid() != self.event_ptr.get_cid():
			self.send_output("default", entity)
			return

		if self.datasource == "tag":
			self.vals.append(entity.get_tag())
		elif self.datasource == "extra_data":
			ed = entity.get_extra_data()
			for key in self.dataparam["item"]:
				ed = ed[key]
			self.vals.append(ed)
		elif self.datasource == "time":
			self.vals.append(entity.get_log_time(self.dataparam["units"]))
		
		if not self.consume:
			self.send_output("default",entity)


class interval(AbstractReduce):
	"""filter to reduce event data by a specific operation,
	and write a new event tagged with the result"""

	subclass_expected_parameters = {
		"src_interval" : {
			"doc" : "event to obtain data",
			"types" : "string"
		},
	}

	def __init__(self, params):
		# hack to 'inherit' parameters
		self.expected_parameters.update(self.subclass_expected_parameters)
		AbstractReduce.__init__(self, params)
	
	def initialize(self):
		AbstractReduce.initialize(self)
		self.event_ptr = self.get_ns_pointer(self.params["src_interval"])

	def process(self, entity):
		if entity.get_cid() != self.event_ptr.get_cid():
			self.send_output("default", entity)
			return

		self.vals.append(entity.get_duration())
		
		if not self.consume:
			self.send_output("default",entity)

