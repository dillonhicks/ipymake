from ppexcept import *
import imp
import string
import entities
from datastreams import namespaces
from pykusp import configfile
from os.path import split
import queues

class Filter:
	"""basic class from which all filters descend."""

	# METHODS YOU MAY WANT TO SUBCLASS

	def initialize(self):
		"""initialization which takes place after the filter
		is installed and ready in a pipeline.

		If your filter opens any files on disk for writing, open them here

		you will have access to self.namespace and self.pipeline
		when this is called. your filter's parameters will be verified and
		acessible from self.params.

		this is where you should retrieve namespace pointers
		
		basically, you should consider this the constructor."""	
		pass


	def process(self, entity):
		"""filtering function. subclass this. 
		
		your filtering function should use self.send() or
		self.send_output() to propogate entities down the
		pipeline.
		
		some filters will need to see the entire datastream
		before being able to emit entities. in this case, buffer
		them here and send everything in the finalize() method"""
		self.send(entity)

	
	def finalize(self):
		"""called when there are no more events.
		
		you should close all output files. in the case of accumulator
		filters, you should send all the buffered entities"""
		pass

	def abort(self):
		"""called if any fatal errors occur upstream. you must
		delete any output files created during initialize() or
		process().
		
		if you create output files during finalize(), there is
		no need to delete them here"""

	expected_parameters = {}
	"""configfile verification datastructure for user parameters"""

	output_names = ["default"]
	"""names of outputs this filter has"""

	builtin_namespace = {}
	"""hard-coded namespaces go here. use sparingly, its usually better
	to just declare them in the pipeline configuration"""

	debug_flag = False
	"""set to True to enable debugging messages; if false, calls to
	self.debug() don't print anything"""

	process_admin = False
	"""normally, datastreams administrative events are passed through
	bypassing process(). if you must see them, set this to true. be
	very careful, you can cause all kinds of problems if namespace events
	are not propagated."""

	# METHODS TO LEAVE ALONE

	def __init__(self, params):
		"""constructor. verifies the validity of supplied
		parameters and raises exception if they are bogus"""
		self.outputs = {}
		self.entcount = 0
		self.nsptrs = []
		self.pipeline = None
		self.namespace = None
		self.debug_level = 0

		for name in self.output_names:
			self.outputs[name] = None

		# add boilerplate to parameter def
		self.expected_parameters = configfile.check_spec({
			"root":{
				"required":True,
		    		"dictdef":self.expected_parameters,
		    		"types":["dictionary"]}})
	
		try:
			self.params = configfile.check_config(params, 
					self.expected_parameters)
		except configfile.ConfigfileVerifyException, ex:

			raise FilterVerifyException("In filter "+self.get_name()+":\n"+str(ex))

			

	def get_name(self):
		"""get the name of this filter, with the name of the pipeline
		it is in prepended to it."""
		if self.pipeline:
			return self.pipeline.get_name()+":"+self.__class__.__name__
		else:
			return self.__class__.__name__

	def info(self, text):
		"""print an informative message"""
		if self.debug_level > 1:
			print self.get_name()+": "+str(text)

	def warn(self, text):
		"""print a non-fatal warning message"""
		print self.get_name()+" WARNING: "+str(text)

	def error(self, text):
		"""generate an error"""
		raise FilterException(text)

	def debug(self, text):
		"""print a debugging message, only if self.debug_flag is true"""
		if self.debug_flag:
			print self.get_name()+": "+str(text)

	def get_ns_pointer(self, entityname):
		"""get a NamespacePointer object for a named entity. 
		this object will be updated anytime new namespace events
		are receieved."""
		nsptr = NamespacePointer(entityname, self.namespace)
		self.nsptrs.append(nsptr)
		return nsptr

	def set_pipeline(self, pipeline):
		self.pipeline = pipeline
		self.namespace = pipeline.get_namespace()

		if self.builtin_namespace:
			self.pipeline.add_namespace(self.builtin_namespace)
		
		self.nsevent = self.namespace["DSTREAM_ADMIN_FAM/NAMESPACE"].get_id()
		
	
		for k, v in self.outputs.iteritems():
			if not v and k != "default":
				self.info("Output '"+k+"' not assigned to anything, sending to default")


		self.initialize()

	def receive(self, entity):
		"""receive an entity. called by the previous filter in the pipeline"""
		if entity.message:
			if entity.message == entities.PIPELINE_ERROR:
				self.info("aborting due to upstream error.")
				self.abort()
			elif entity.message == entities.PIPELINE_EOF:
				try:
					self.finalize()
				except FilterException, pe:
					print self.get_name()+" failed during finalization"
					raise
				self.debug("Processed "+`self.entcount`+" entities.")
			self.send(entity)
		else:
			try:
				if entity.is_admin():
					# administrative event
					if entity.get_cid() == self.nsevent:
						for nsptr in self.nsptrs:
							nsptr.update()
					if self.process_admin:
						try:
							self.entcount = self.entcount + 1
							self.process(entity)
						except FilterException, pe:
							print self.get_name()+" failed processing admin entity "+entity
							raise
					else:
						self.send(entity)
				else:
					try:
						self.entcount = self.entcount + 1
						self.process(entity)
					except FilterException, pe:
						print self.get_name()+" failed processing entity "+entity
						raise
			except Exception, e:
				self.warn("Caught exception: "+`e`)
				print "ENTITY",`entity`
				raise

	def assign_output(self, name, component):
		"""assign an object, which must implement a receive() method, to
		one of this filter's named outputs. called by the pipeline during setup"""
		if name not in self.outputs:
			raise ConstructionException("Output "+`name`+" does not exist")
		if self.outputs[name]:
			raise ConstructionException("Output "+`name`+" already assigned")
		self.outputs[name] = component
	
	def get_output_names(self):
		"""return the names of all the outputs"""
		return self.outputs.keys()

	def get_output(self, name):
		"""get the object that corresponds to a named output.

		the act of calling this function will create an OutputMultiplexer
		if there was no output object for the given name"""

		if not self.outputs[name]:
			om = OutputMultiplexer(name, 
				self.pipeline.tee_output)
			om.set_pipeline(self.pipeline)
			self.outputs[name] = om

		return self.outputs[name]

	def get_pipeline(self):
		"""return the pipeline that this filter is installed in"""
		return self.pipeline

	def send(self, entity):
		"""send entity to all outputs"""

		sent = []

		for k,v in self.outputs.iteritems():
			# this check is to prevent duplication in the
			# case of more than one output going to the same
			# destination
			if v and v not in sent:
				self.send_output(k, entity)
				sent.append(v)
		sent = []

	def send_output(self, name, entity):
		"""send entity to one of this filter's named outputs.
		
		if this output is unconnected, the entity will get sent
		to the default output instead"""
		o = self.outputs[name]
		if not entity.namespace:
			entity.namespace = self.namespace
		
		# if this output wasn't connected, send the event to
		# the default output instead
		if o:
			o.receive(entity)
		elif name != "default":
			self.send_output("default", entity)


class OutputFilter(Filter):
	process_admin = True

class OutputMultiplexer(OutputFilter):
	output_names = []

	def __init__(self, name, tee_output_flag):
		Filter.__init__(self, {})
		self.name = name
		self.tee = tee_output_flag

	def initialize(self):
		if not self.tee:
			return

		self.filename = self.pipeline.get_name()+"."+self.name+".tee.pp2"
		poutput = PickleOutput(self.filename)
		self.outputs["tee-output"] = poutput


	# corba
	def connect(self, remote_pipe_name, queue_params):
		"""connect to this multiplexer, obtaining a queue to retrieve entities"""
		if type(queue_params) is str:
			queue_params = cPickle.loads(queue_params)
		q = queues.PostprocessQueue(maxsize=100)
		self.outputs[remote_pipe_name] = q
		return q
	
	def process(self, entity):
		entity.clear_cache()
		self.send(entity)


class NamespacePointer:
	"""this class assists in retrieving numerical entity composite ids

	when filtering starts, only the admin namespace is known. periodically
	namespace events will come in, which are merged with the pipeline's
	namespace. every time this happens, this object will look up its
	named entity in the namespace and save its cid. if it is not found,
	(i.e. the namespace event that describes this entity hasn't arrived yet)
	the cid will be -1.

	you can then use the expression (entity.get_cid() == nspointer.get_cid()) to
	check if an incoming entity is an instance of this one. this is much faster
	than doing a string comparison of entity and family names"""
	def __init__(self, entityname, ns):
		self.ename = entityname
		self.cid = -1
		self.ns = ns
	
	def get_cid(self):
		"""return the composite id associated with the entitiy, or
		-1 if we don't know yet"""
		return self.cid

	def update(self):
		"""called by the filtering framework whenever the pipeline's
		namespace has been updated"""
		if self.ename in self.ns:
			new_cid = self.ns[self.ename].get_id()
			self.cid = new_cid


fprefix = "datastreams.postprocess.filters."

def get_filter_class(filter_name, localmod):
	filter_name_list = filter_name.rsplit('.', 1)
	module_name = filter_name_list[0] 
	filter_class_name = filter_name_list[1] 

	localmod = [localmod, [split(mod) for mod in localmod]]
	localmod[1] = [tail for (head, tail) in localmod[1]]

	if module_name + ".py" in localmod[1]:
		filename = localmod[0][localmod[1].index(module_name + ".py")]
		a = open(filename)
		m = imp.load_module(module_name, a, filename, 
				('.py', 'r', imp.PY_SOURCE))

	else:
		try:
			m = __import__(module_name, globals(),{},[filter_class_name])
		except ImportError, ie:
			module_name = fprefix+module_name
			m = __import__(module_name, globals(),{},[filter_class_name])		
	
	try:
		filter_ref = getattr(m, filter_class_name)
	except AttributeError, ex:
		print ex
		raise UnknownFilterException, "Filter class "+ \
		      filter_class_name+" does not exist in module "+ \
		      module_name+"."
	return filter_ref

def get_filter_list(mod_name):
	"""
	This function analyzes a filter module, and returns
	a list with the names of all the filters it contains,
	which can be individually retrieved with get_filter()

	
	"""
	long_mod_name = string.strip(mod_name)
	
	# import the filter module
	try:
		try:
			filter_module = __import__(long_mod_name)
		except ImportError:
			# wasn't able to find the filter module in the PYTHONPATH;
			# let's see if it is in postprocess.filters.builtin
			print long_mod_name+" not found in pythonpath"
			long_mod_name = fprefix+long_mod_name
			print "trying",long_mod_name
			filter_module = __import__(long_mod_name)
			pass
		pass
	except ImportError, ex:
		raise UnknownModuleException, str(ex)
	
	
	
	# due to the way __import__ works, we need to traverse until
	# we get to the actual module
	components = long_mod_name.split('.')
	for comp in components[1:]:
		filter_module = getattr(filter_module, comp)
		pass
	pass

	# obtain the list of filters within the module
	# by convention, any symbol ending with "_filter" is a filter
	# class
	filter_list = dir(filter_module)
	filter_list = map(lambda s:mod_name+"."+s[:-7], filter_list)
	
	return filter_list

def get_filter_help(filtername):
	"""Return a string with help information for a specific filter"""

	try:
		filter = get_filter_class(filtername, [])
	except UnknownFilterException,ex:
		return str(ex)

	result = ""

	# FIXME: use textwrap
	if filter.__doc__:
		helpstrings = filter.__doc__.splitlines()
		for eachline in helpstrings:
			a = eachline.strip()
			result = result + a + "\n"
			pass
	else:
		result = result + "This filter has no documentation.\n"
	


	# where in the pipeline can this filter be placed?
	result = result + "This filter's outputs are named: " + `filter.output_names`+ "\n"
	

	result = result + '\nParameters: \n'
	import StringIO

	s = StringIO.StringIO()
	x =  configfile.check_spec({
			"root":{
				"required":True,
		    		"dictdef":filter.expected_parameters,
		    		"types":["dictionary"]}})
	configfile.get_dictionary_help(s,x["root"]["dictdef"], 0)
	result = result + s.getvalue()
	return result

def get_module_help(modulename):
	"""Return a string with help information for all filters in a module"""
	result = ""
	try:
		for filtername in get_filter_list(modulename):
			result = result + filtername + "\n" + "-"*len(filtername)
			result = result + "\n" + get_filter_help(filtername)
			pass
		return result
	except UnknownModuleException:
		return "Unknown module " + modulename
	pass


