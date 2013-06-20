import cPickle
from ppexcept import *
from filtering import *
import headfilter
import inputs
import entities
from datastreams import namespaces
import glob
import traceback
import os
import sys
import signal
import threading
import pprint

pp = pprint.PrettyPrinter()

def banner(s):
	print
	print s
	print "-"*len(s)


# Watcher class taken from:
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/496735
# solves problem of ctrl-C not working while postprocessing

class Watcher:
    """this class solves two problems with multithreaded
    programs in Python, (1) a signal might be delivered
    to any thread (which is just a malfeature) and (2) if
    the thread that gets the signal is waiting, the signal
    is ignored (which is a bug).

    The watcher is a concurrent process (not thread) that
    waits for a signal and the process that contains the
    threads.  See Appendix A of The Little Book of Semaphores.
    http://greenteapress.com/semaphores/

    I have only tested this on Linux.  I would expect it to
    work on the Macintosh and not work on Windows.
    """
    
    def __init__(self):
        """ Creates a child thread, which returns.  The parent
            thread waits for a KeyboardInterrupt and then kills
            the child thread.
        """
        self.child = os.fork()
        if self.child == 0:
            return
        else:
            self.watch()

    def watch(self):
        try:
            os.wait()
        except KeyboardInterrupt:
            # I put the capital B in KeyBoardInterrupt so I can
            # tell when the Watcher gets the SIGINT
            print 'Caught KeyboardInterrupt, aborting.'
            self.kill()
        sys.exit()

    def kill(self):
        try:
            os.kill(self.child, signal.SIGKILL)
        except OSError: pass


# this will need to be a CORBA interface
class ProcessingNode:
	"""each node has its own address space, and contains one
	or more pipelines. this will run as a daemon, and should therefore
	be re-usable
	
	tee_output is a flag indicating that the shared queues between nodes should
	log data to disk

	extra_modules is a list of modules to get additional filters from

	filters is a dictionary of pipelines, each value being a linear
	pipeline of filters
	"""
	def __init__(self, nodename, tee_output, extra_modules, filters, debug=False):
		self.pipelines = {}
		self.name = nodename
		self.tee_output = tee_output
		self.extra_modules = extra_modules
		self.debug_flag = debug

		for k,v in filters.iteritems():
			self.create_pipeline(k, v)

	def banner(self, str):
		if self.debug_flag:
			banner(str)

	def debug(self, text):
		if self.debug_flag:
			print text

	# part of corba interface
	def create_pipeline(self, name, filter_params):
		"""constructs a pipeline based on provided specification,
		and adds it to this node
		
		filter params is a list of tuples
		(filter, parameters) where filter is either a filter class name
		to be looked up, or the class itself, and parameters is a dictionary"""
		self.banner("Creating pipeline "+`name`)
		
		# instantiate filters
		filterlist = []
		for filtername, params in filter_params:
			self.debug("Creating filter "+`filtername`)

			if type(filtername) is str:
				filter_class = get_filter_class(filtername,
					self.extra_modules)
			else:
				filter_class = filtername

			f = filter_class(params)
			if self.debug_flag:
				pp.pprint(f.params)
				f.debug_flag = True

			filterlist.append(f)

		if not filterlist:
			raise ConstructionException("No filters specified for pipeline")

		# ensure that first filter is a head filter
		head = filterlist[0]
		if not isinstance(head, headfilter.HeadFilter):
			raise ConstructionException("First filter must be head filter")

		tail = filterlist[1:]
		
		pipeline = Pipeline(name, self, self.tee_output, head)
		for f in tail:
			pipeline.add_filter(f)
	
		self.pipelines[name] = pipeline

	def get_pipeline(self, pipename):
		return self.pipelines[pipename]

	def has_pipeline(self, pipeline):
		return pipeline in self.pipelines

	# corba
	def get_name(self):
		return self.name


	def run(self):
		"""run all the pipelines in this group concurrently"""
		self.banner("Establishing upstream connections")

		for name, pipe in self.pipelines.iteritems():
			pipe.establish_connections()
		
		self.banner("Executing postprocessing graph")
		for name, pipe in self.pipelines.iteritems():
			pipe.start()

		# warning: join call makes all signals ignored
		for name, pipe in self.pipelines.iteritems():
			pipe.join()
		
	def run_single(self):
		"""Only works if there is exactly one pipeline"""
		for name, pipe in self.pipelines.iteritems():
			pipe.establish_connections()
		
		self.banner("Executing postprocessing graph")
		for name, pipe in self.pipelines.iteritems():
			pipe.run()


	def run_single_doesntworkanymore(self):
		"""run all the pipelines in this group sequentially"""
		completed = []
		names = self.pipelines.keys()
		deps = {}
		self.banner("Establishing upstream connections")

		for name, pipe in self.pipelines.iteritems():
			# ignore dependencies not in our address space
			pipe.establish_connections()
			deps[name] = [dep for dep in 
					pipe.get_dependencies()
					if dep in names]

		errors = False

		while names:
			for name in names:
				dep = [dep for dep in deps[name]
						if dep not in completed]
				deps[name] = dep
				if not dep:
					self.banner("Executing pipeline "+`name`)

					try:
						self.pipelines[name].run()
					except PostprocessException, e:
						print self.get_name() + " ERROR: caught exception in pipeline "+`name`+":"
						traceback.print_exc()
						errors = True

					#print self.pipelines[name].namespace
					completed.append(name)
					names.remove(name)
					break
		if errors:
			print "WARNING: Pipeline group "+`self.get_name()`+" completed with errors."
		else:
			self.debug("Pipeline group "+`self.get_name()`+" completed successfully.")


class Pipeline(threading.Thread):
	def __init__(self, name, node, tee_output, head_filter):
		threading.Thread.__init__(self)
		self.name = name

		# should outputmultiplexers also write events to a file?
		self.tee_output = tee_output

		# an ordered list of Filter objects. as entities are read in,
		# they are written to the first filter in the chain, which passes it
		# along to the next, etc. the first filter is the pipeline itself
		self.filters = [head_filter]
		
		# pointer to the pipeline node that we are contained within
		self.node = node

		# at first we just start with the datastreams admin namespace.
		# input files will contain 1 or more namespace events which describe all
		# the entities within the input source. as we get them, they are merged into
		# our namespace here.
		self.namespace = namespaces.get_admin_ns()
		head_filter.set_pipeline(self)
		
	def add_filter(self, filter):
		"""append a filter object to the end of this pipeline"""
		prev = self.filters[-1]
		if len(prev.get_output_names()) == 0:
			raise ConstructionException("Previous filter in pipeline has no outputs; must be last")

		self.filters.append(filter)
		prev.assign_output("default", filter)
		filter.set_pipeline(self)
		
	def add_namespace(self, ns):
		nsi = inputs.NamespaceInputSource(ns)
		self.filters[0].add_input_source(nsi)

	# corba
	def connect(self, client, output_name, params, index):
		"""connect to an output source in this pipeline.
		returns a queue to retrieve data from"""
		try:
			o = self.filters[index].get_output(output_name)
		except KeyError:
			raise ConstructionException("Pipeline has no output named "+`output_name`)
		except IndexError:
			raise ConstructionException("Bad pipe index "+`index`)
		return o.connect(client, params)

	def run(self, extra_ns=None):
		"""initializes all filters and then begins filtering."""

		# if any namespace was given in the configuration file, merge it
		if extra_ns:
			c, ns = self.namespace.merge(extra_ns)
			nse = entities.Event(self.nsevent,
					None, 0, ns)
			self.send(nse)

		self.filters[0].run()

	def get_namespace(self):
		"""retrieve the pipeline's namespace datastructure."""
		return self.namespace

	def get_name(self):
		"""get the name of this pipeline"""
		return self.get_node().get_name() + ":" + self.name

	def get_node(self):
		"""get the ProcessingNode object that contains this pipeline"""
		return self.node

	def get_dependencies(self):
		return self.filters[0].get_dependencies()

	def establish_connections(self):
		self.filters[0].establish_connections()



