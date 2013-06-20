import filtering
import entities
import thread
import time
import inputs
import copy
import sys

class HeadFilter(filtering.Filter):
	"""this is the first filter in a pipeline, and has an execution loop
	which drives the rest of the pipeline"""

	#debug_flag = True

	def choose_next(self, entitydict):
		"""entitydict is a mapping from source ids (which can be used to 
		reference source objects in self.sources) to the next available entity
		for that source.

		this function examines these entities and returns the source id of the
		source to obtain the next event."""

		raise Exception("Abstract Method")

	def preprocess(self, entity):
		"""any processing that needs to be done to an entity BEFORE a decision
		is made to choose the next entity. you may return None if the
		entity is to be rejected."""
		return entity

	def postprocess(self, entity):
		"""any processing that needs to be done to an entity AFTER a decision
		is made to choose the next entity"""
		return entity


	def open_sources(self):
		"""initialization step. create any sources here and install them
		with add_input_source. this function is called from establish_connections()
		and after it completes, each source will be individually opened"""
		pass


	def __init__(self, params):
		filtering.Filter.__init__(self, params)

		# a dictionary of named input sources. each one maps to an InputSource
		# object. the run() method iterates through all the sources and
		# sends them in chronological order to the filters
		self.sources = {}

		# a dictionary, with each key being an input source. the value
		# is another dictionary, which maps entity composite IDs from that
		# source to composite IDs in the merged namespace. if a composite id
		# is not present in this dictionary, it will be unmodified.
		self.remapping = {}

		# This dictionary maps input source names to the next available
		# entity for that input source
		self.next_entity = {}

		self.lock = thread.allocate_lock()

		self.terminate_flag = False


	def stop(self):
		self.debug("stop called")
		self.lock.acquire()
		self.terminate_flag = True
		self.lock.release()


	def run(self):
		"""main execution function which drives entire pipeline.
		
		entities are demultiplexed from the input sources and pushed
		chronologically through the pipeline until there are no more
		entities.
		
		you must have first called establish_connections() before 
		you can call run()"""

		self.nsevent = self.namespace["DSTREAM_ADMIN_FAM/NAMESPACE"].get_id()

		# build the next_entity dictionary
		self.lock.acquire()
		for sourceid, source in self.sources.iteritems():
			entity = self.fetch(sourceid)
			if entity.message == entities.PIPELINE_EOF:
				self.sources[sourceid].close()
			else:
				self.next_entity[sourceid] = entity
		self.lock.release()



		# iterate, sending the earliest event down the pipeline,
		# until there are no more events
		while(True):
			self.lock.acquire()
			if self.terminate_flag or not self.next_entity:
				self.lock.release()
				break

			min_sourceid = self.choose_next(self.next_entity)
			
			try:
				ne = self.next_entity[min_sourceid]
				ne = self.postprocess(ne)
				if ne:
					self.send(ne)
				
			except Exception, e:
				self.info("caught exception "+`e`)
				self.send(entities.PipelineError())
				raise
			
			nextent = self.fetch(min_sourceid)

			if nextent.message == entities.PIPELINE_EOF:
				self.info("Finished reading data from source "+`min_sourceid`)
				self.sources[min_sourceid].close()
				del self.sources[min_sourceid]
				del self.next_entity[min_sourceid]
			else:
				self.next_entity[min_sourceid] = nextent
			self.lock.release()
		
		# all done. send a pipelineend message
		self.send(entities.PipelineEnd())


	def add_input_source(self, source):
		"""add an input source object for this pipeline to read entities from"""
		self.lock.acquire()
		sourceid = source.get_name()
		self.sources[sourceid] = source
		self.remapping[sourceid] = {}
		source.open()
		self.lock.release()

	def establish_connections(self):
		"""create and open all input sources.

		this has to be a separate step from run(), because
		otherwise there will be no way to construct the dependencies"""
		pass

	
	def get_dependencies(self):
		"""return names of pipelines that this depends on for data"""

		deps = []
		self.lock.acquire()
		for source in self.sources.values():
			d = source.get_dependency()
			if d:
				deps.append(d)
		self.lock.release()
		return deps

	def process(self, entity):
		raise Exception("process should never be called on a head filter")


	def fetch(self, sourceid):
		"""fetch an entity from a named input source, and do some preprocessing
		before being merged."""

		#self.namespace.check_ids()

		while True:
			try:
				entity = self.sources[sourceid].read()
			except Exception:
				self.info("ERROR: Failed to read entity from input source "+`sourceid`)

				self.send(entities.PipelineError())
				raise

			if (entity.message == entities.PIPELINE_EOF or
				entity.message == entities.PIPELINE_ERROR):
				# this is a special entity that specifies end-of-file. it gets
				# passed along so all filters and outputs can close themseleves
				return entity

			entity = self.preprocess(entity)

			if not entity:
				continue

			cid = entity.get_cid()
			if cid == self.nsevent:
				# this is a namespace event. merge the namespace into our own,
				# renumbering new families/entities as necessary. any renumbering
				# done will be noted in the source-specific remapping dictionary
				# so entities can automatically be renumbered as they come in
				conflicts, new_ns = self.namespace.merge(entity.get_extra_data())
				if conflicts:
					pass
					#print "CONFLICTS",conflicts
				for old_cid, new_cid in conflicts.iteritems():
					#print sourceid, old_cid, new_cid
					self.remapping[sourceid][old_cid] = new_cid

				# if our namespace wasn't changed, no point in passing along
				# data. return None, which means 'try again'
				if not new_ns.values():
					continue

				entity = entity.change_extra_data(new_ns)
			
			# the cid is still the value read in from the input source
			# if during merging this needs to be changed, the cid will be
			# in the remapping dictionary
			if cid in self.remapping[sourceid]:
				#print self.remapping[sourceid]
				entity = entity.change_cid(self.remapping[sourceid][cid])
				
			# entities can look up their own information in the namespace.
			# this value is cleared before it is serialized to not waste space
			try:
				entity.set_namespace(self.namespace)
			except Exception, e:
				self.info("FAIL")
				raise

			#print entity
			return entity

