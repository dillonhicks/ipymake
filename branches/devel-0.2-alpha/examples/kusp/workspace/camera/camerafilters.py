from datastreams.postprocess import filtering
from datastreams import namespaces

class frame_kill(filtering.Filter):
	"""removes events that are not part of a movement decision"""	
	def initialize(self):
		self.elist = []
		self.tags = []

		self.decision_evt = self.get_ns_pointer(
				"TRACK_THREAD/MOVE_DECISION")

	def process(self, entity):

		if entity.get_cid() == self.decision_evt.get_cid():
			self.tags.append(entity.get_tag())
			
		self.elist.append(entity)

	def finalize(self):
		for e in self.elist:
			if e.get_type() != namespaces.EVENTTYPE:
				self.send(e)
				continue
			if (e.get_family_name() not in 
					["CAPTURE", "NETWORK_SERVER",
					"NETWORK_CLIENT", "TRACK_THREAD"]):
				self.send(e)
				continue

			if e.get_tag() in self.tags:
				self.send(e)
		self.elist = []


class tag_greaterthan(filtering.Filter):
	def process(self, entity):
		if entity.get_tag() and entity.get_tag() > 30:
			self.send(entity)
