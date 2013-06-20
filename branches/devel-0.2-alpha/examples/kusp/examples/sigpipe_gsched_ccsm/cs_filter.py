from datastreams.postprocess import filtering
from datastreams.postprocess import entities
from datastreams import namespaces

class cpu_time(filtering.Filter):
	"""This computes the total cpu time of all the running tasks by
	summing context switch events. Optionally, emits intervals of time 
	spent on the cpu for each task."""

	expected_parameters = {
		"emit_interval" : {
			"types" : "string",
			"doc" : "Name of emitted intervals of the context switch events \
					If not specified, no intervals are emitted. \
					Intervals will have the same tag data as the \
					events they were created from.",
			"default" : ""
		},
		"consume" : {
			"types" : "boolean",
			"doc" : "Whether to delete matching entities after processing",
			"default" : False
		},
	}

	def initialize(self):
		
		self.to_ptr = self.get_ns_pointer("SCHEDULER/SWITCH_TO")
		self.from_ptr = self.get_ns_pointer("SCHEDULER/SWITCH_FROM")

		if self.params["emit_interval"]:
			self.int_ptr = self.get_ns_pointer(self.params["emit_interval"])
		else:
			self.int_ptr = None
		

		self.consume = self.params["consume"]

		# A dictionary of SWITCH_TO event times which have not seen a corresponding SWITCH_FROM event 
		self.start_time = {}

		# A dictionary of lists of the time intervals for each task
		self.task_times = {}
		self.total_times = {}
		self.machines = []

	def process(self, entity):

		id = entity.get_pid()
		log_time = entity.get_log_time()
		machine = entity.get_machine()
		match = False

		if entity.get_cid() == self.to_ptr.get_cid():

			if machine not in self.machines:
				self.machines.append(machine)

			if id in self.start_time:
				self.warn("Switched to running task: " + `id`)
				self.start_time[id] = log_time
			else:
				self.start_time[id] = log_time

			match = True
		
		elif entity.get_cid() == self.from_ptr.get_cid():

			if id in self.start_time:

				# We have a matching start time in the start_times dictionary

				if id in self.task_times:
					self.task_times[id].append(log_time["tsc"].get_value() - self.start_time[id]["tsc"].get_value())
				else:
					self.task_times[id] = []
					self.task_times[id].append(log_time["tsc"].get_value() - self.start_time[id]["tsc"].get_value())

				if self.int_ptr:
					i = entities.Interval(
						self.int_ptr.get_cid(),
						self.start_time[id], log_time, id)
					self.send_output("default", i)

				del self.start_time[id]

			else:

				if machine not in self.machines:
					#If we get a switch_from event from a machine we haven't 
					#seen a switch_to event from yet, just skip the entity
					if not self.consume:
						self.send_output("default", entity)				
					return

				self.warn("Got from event without matching to event from task: " + `id`)

			match = True

		
		if not match or (match and not self.consume):
			self.send_output("default", entity)
			return

	def finalize(self):

		for id in self.task_times:
			self.total_times[id] = 0

		for id in self.task_times:
			for time in self.task_times[id]:
				self.total_times[id] = self.total_times[id] + time

		for id in self.total_times:
			print "Total time for task ", id, ": %11.3f" % self.total_times[id], " tscs"

class print_time(filtering.Filter):

	def initialize(self):
		self.i = 0
	def process(self, entity):
		self.i = self.i + 1
		log_time = entity.get_log_time()
		print "IP[", entity.get_tag(), "] tscs: %11.3f" % log_time["tsc"].get_value(), "\t tsc: %11.3f" % log_time["tsc"].get_value() 

