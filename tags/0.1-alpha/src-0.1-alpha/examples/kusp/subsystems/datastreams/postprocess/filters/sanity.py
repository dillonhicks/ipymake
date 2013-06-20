
from datastreams.postprocess import filtering, entities

class check_cs_seq(filtering.Filter):
	def initialize(self):
		self.stptr = self.get_ns_pointer("SCHEDULER_FAM/SWITCH_TO")
		self.sfptr = self.get_ns_pointer("SCHEDULER_FAM/SWITCH_FROM")
		self.lastpids = {}
		pass
	
	def process(self, entity):
		cid = entity.get_cid()
		seqtime = entity.get_time_object("log", "sequence")
		fname = seqtime.get_clocksource()
		pid = entity.get_tag()

		if cid == self.stptr.get_cid():
			if fname not in self.lastpids:
				self.lastpids[fname] = pid
				return
			elif self.lastpids[fname]:
				raise Exception("%s: consequtive switch to"\
					"[%d, %d]" % (fname, self.lastpids[name],\
							pid))
			else:
				self.lastpids[fname] = pid
				pass
			pass

		if cid == self.sfptr.get_cid():
			if fname not in self.lastpids:
				self.lastpids[fname] = -1
				return




class abort_on_hole(filtering.Filter):
	def initialize(self):
		self.last = {}
	
	def process(self, entity):
		seqtime = entity.get_time_object("log", "sequence")
		seq = seqtime.get_value()
		fname = seqtime.get_clocksource()

		self.send(entity)

		if fname not in self.last:
			self.last[fname] = seq
			return

		if seq > self.last[fname]+1:
			raise Exception("%s: hole at seq %d to %d" % (fname,\
				self.last[fname], seq))
		else:
			self.last[fname] = seq
			pass
		pass
	pass

class hole(filtering.Filter):

	def initialize(self):
		self.vals = {}
		self.max_seen = {}

	def process(self, entity):
		seqtime = entity.get_time_object("log","sequence")
		seq = seqtime.get_value()
		fname = seqtime.get_clocksource()
		
		if seq > 1:
			if fname not in self.vals:
				self.vals[fname] = [seq]
				self.max_seen[fname] = seq
			else:
				if seq > self.max_seen[fname]:
					self.max_seen[fname] = seq
				self.vals[fname].append(seq)
		self.send(entity)


	def finalize(self):
		for fname in self.vals:
			self.vals[fname].sort()

			for i in range(2, self.max_seen[fname]+1):
				s = self.vals[fname][0]
				if s == i:
					self.vals[fname] = self.vals[fname][1:]
				else:
					self.warn("Missing entity sequence number "+`i`+
							" for "+fname)



