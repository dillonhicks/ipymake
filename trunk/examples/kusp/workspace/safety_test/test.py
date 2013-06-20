from datastreams.postprocess import filtering
from datastreams.postprocess import entities
from datastreams import namespaces

class State:
	TIMEOUT_START = 0
	TIMEOUT = 1
	TIMEOUT_SCHED = 2
	TIMEOUT_END = 3
	LINUX_START = 4
	FORCE_LINUX = 5
	LINUX_END = 6

class Verify(filtering.Filter):
	"""
	Verify that events were output by the safety sdf when the test was run.
	"""
	expected_parameters = {
		"consume" : {
			"types" : "boolean",
			"doc" : "Whether to delete matching entities after processing",
			"default" : False
		},
	}
	
	def initialize(self):
		
		self.linux_to = self.get_ns_pointer("SDF_SAFE/LINUX_TIMEOUT")
		self.linux_to_sched = self.get_ns_pointer("SDF_SAFE/LINUX_TIMEOUT_SCHED")
		self.force_linux = self.get_ns_pointer("SDF_SAFE/FORCE_LINUX")
		self.timeout_start = self.get_ns_pointer("TEST/TIMEOUT_START")
		self.timeout_end = self.get_ns_pointer("TEST/TIMEOUT_END")
		self.linux_start = self.get_ns_pointer("TEST/LINUX_START")
		self.linux_end = self.get_ns_pointer("TEST/LINUX_END")

		# This last parameter will simply determine if the events used to generate
		# the above intervals will be passed on to any following filters, or destroyed.
		self.consume = self.params["consume"]

		self.state = State.TIMEOUT_START

	def process(self, entity):
		match = False
			
		if entity.get_cid() == self.timeout_start.get_cid():
			match = True

			if self.state is State.TIMEOUT_START:
				self.state = State.TIMEOUT
	
		if entity.get_cid() == self.linux_to.get_cid():
			match = True

			if self.state is State.TIMEOUT:
				self.state = State.TIMEOUT_SCHED

		if entity.get_cid() == self.linux_to_sched.get_cid():
			match = True

			if self.state is State.TIMEOUT_SCHED:
				self.state = State.TIMEOUT_END
				print "Timeout test PASSED."

		if entity.get_cid() == self.timeout_end.get_cid():
			match = True
			
			if self.state is not State.TIMEOUT_END:
				print "Timeout test FAILED."

			self.state = State.LINUX_START

		if entity.get_cid() == self.linux_start.get_cid():
			match = True

			self.state = State.FORCE_LINUX

		if entity.get_cid() == self.force_linux.get_cid():
			match = True
		
			if self.state is State.FORCE_LINUX:
				self.state = State.LINUX_END
				print "Force linux test PASSED."

		if entity.get_cid() == self.linux_end.get_cid():
			match = True
		
			if self.state is not State.LINUX_END:
				print "Force linux test FAILED."

		if (not match) or (match and not self.consume):
			self.send_output("default", entity)

