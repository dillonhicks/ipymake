from datastreams.postprocess import filtering
from datastreams.postprocess import entities
from datastreams import namespaces

# This file is an implentation of a custom filter for use with the Datastreams Post-processing
# framework. Any custom filter must import the three fields above. Filtering provides the
# necessary basic framework, entities provides the python representations of the different
# datastreams event types, and namespaces provides a specification for interaction with
# Datastreams events. All three files can be found in the kusp tree at:
#	kusp/datastreams/src/datastreams
# or
#	kusp/datastreams/src/datastreams/postprocess2
# Reading through the files themeselves may provide a clearer understanding of the options
# available to a developer wishing to implement a custom post-processing filter.


# Every implentation of a custom filter must implement a class taking an object of type
# filtering.Filter. The name of the class is the name by which you will call the filter
# in your post-processing congiuration file. See the conguration file in this same directory
# for clarification.

class pipeline_intervals(filtering.Filter):
	"""This computes the intervals between the various pipeline gaps by generating
	intervals from the Datastreams events recorded by sigpipe.c."""

	# The above triple quoted lines are simply documentation explaining the purpose of
	# this filter. Below is a dictionary called expected_parameters. It is not required
	# that a filter implement this dictionary, however, if you wish to, it provdes a
	# simple method of providing arguments to your filter from the configuration file.

	# Each element in the dictionary "expected_parameters" is itself a dictionary. The
	# first name is the identifier you will use to call this filter option from the
	# configuration file. The "types" key word limits the input to the filter option;
	# you can specify 'string', 'integer', 'boolean', or any other standard python type.
	# The "doc" key word is for documentation describing the purpose of the filter option.
	# The default key word allows the developer to specify a default value to be used if
	# the filter option is not specified in the configuration file. Not shown is the 
	# "required" option, which will require the configuration file to specify a value
	# for this filter option. Failing to do so will prevent the filter from initializing.
	# For this reason, it is not useful to use the "default" and "required" key words
	# together.

	# Also note that the expected parameters dictionary will be used to screen
	# configuration file options. Any options specified in the configuration file that
	# are not explicitly defined in expected_parameters will be considered invalid
	# input and the filter will not initialize.

	expected_parameters = {
		"gap_one_interval" : {
			"types" : "string",
			"doc" : "Name of emitted intervals of the first gap in the pipeline",
			"default" : ""
		},
		"all_gaps_intervals" : {
			"types" : "string",
			"doc" : "Name of emitted intervals of all the gaps in the pipeline",
			"default" : ""
		},
		"pipeline_interval" : {
			"types" : "string",
			"doc" : "Name of emitted intervals of the total pipeline traversal",
			"default" : ""
		},
		"consume" : {
			"types" : "boolean",
			"doc" : "Whether to delete matching entities after processing",
			"default" : False
		},
	}

	# Each custom filter implementation can implement three different hooks which will
	# be recognized by the Datastreams Post-processing framework. They are, in the order
	# they will be executed; "initialize", "process", and "finalize". The first and last
	# hooks, "initalize" and "finalize", do not need to be implemented for the filter to
	# function.

	# The "initialize" hook provides a location for declaring global variables and reading
	# in any filter options or conguration file arguments specified by the expected_parameters
	# dictionary. It is called before any other portion of the filter. The hook takes in a
	# reference to "self" which is, as the name indicates, the filter itself. To create a
	# global variable, just add the variable in dotted notation to "self".
	
	def initialize(self):
		
		# Here, we store the namespaces of the Datastreams events our filter will be
		# concerned with into several variables attached to self. The get_ns_pointer
		# function will create a namespace pointer which can be used for comparison
		# with the datastream events which will be processed in the next part of the
		# filter.
		self.sent_ptr = self.get_ns_pointer("GAP_TEST/SIG_SENT")
		self.rcvd_ptr = self.get_ns_pointer("GAP_TEST/SIG_RCVD")

		self.start_ptr = self.get_ns_pointer("PIPE_TEST/PIPE_START")
		self.end_ptr = self.get_ns_pointer("PIPE_TEST/PIPE_END")

		# Here, we check for, and then store, the configuration file options. The first
		# three options were for the namespaces of intervals which we will generate. In
		# the pipeline confuration file, sigpipe.pipes, you can see how each interval is
		# defined in the namespace at the "head" of a pipeline, and then provided as
		# arguments to the custom filter.
		if self.params["gap_one_interval"]:
			self.gap_one_ptr = self.get_ns_pointer(self.params["gap_one_interval"])
		else:
			self.gap_one_ptr = None

		if self.params["all_gaps_intervals"]:
			self.all_gaps_ptr = self.get_ns_pointer(self.params["all_gaps_intervals"])
		else:
			self.all_gaps_ptr = None

		if self.params["pipeline_interval"]:
			self.pipe_ptr = self.get_ns_pointer(self.params["pipeline_interval"])
		else:
			self.pipe_ptr = None

		# This last parameter will simply determine if the events used to generate
		# the above intervals will be passed on to any following filters, or destroyed.
		self.consume = self.params["consume"]

		# Here we define several dictionaries to hold data which will need to be available
		# at any point in the filter.
		self.sent_events = {}
		self.pipe_events = {}
		self.rejected_signal_events = {}
		self.rejected_pipe_events = {}

	# The "process" hook must be implemented when creating a custom filter. It is also the only
	# hook which receives the events flowing down the pipeline. Most processing, filtering, or
	# data collection occurs here.

	def process(self, entity):

		match = False

		# Here we are looking for a pipeline start event. We compare the namespace of the
		# current event in the pipeline with our stored pipeline start event namespace. Note
		# that we operate on the single entity which has entered the pipeline. The framework
		# will call process repeatedly and pass in each entity that has reached the stage
		# of the pipeline wich uses this filter.
		if entity.get_cid() == self.start_ptr.get_cid():
			match = True

			# We are fetching the time at which the event was logged
			start_time = entity.get_log_time()
			# also the tag value recorded at that time
			sig_num = entity.get_tag()
			# and then storing the time in a unique location in a dictionary
			self.pipe_events[sig_num] = start_time
	
		# Here we are looking for a pipeline end event. When we find one, we look to see if
		# there is starting event for this particular signal. We add an error message
		# that can be displayed to screen or printed to a file. If there is a matching start
		# event, we create a new interval event using the namespace we specified in the
		# configuration file, the start and end event pair, and the signal number as a tag
		# value. The "self.send_output" function is what actually send the new interval
		# event out into the pipeline, to be seen by any following filters.
		if entity.get_cid() == self.end_ptr.get_cid():
			match = True

			end_time = entity.get_log_time()
				
			sig_num = entity.get_tag()

			if sig_num not in self.pipe_events:
				self.warn("Missing start event for signal "+`sig_num`)
				self.rejected_pipe_events[sig_num] = end_time
			else:
				start_time = self.pipe_events[sig_num]
				del self.pipe_events[sig_num]
				i = entities.Interval(self.pipe_ptr.get_cid(), start_time, end_time, sig_num)
				self.send_output("default", i)

		# Here we are looking for a signal sent event, similar to above. However, instead
		# of using the tag value directly, we decompose it back into a pipeline stage number
		# and a signal number by reversing the operation used to form the tag in sigpipe.c.
		# We store the time of the signal sent event into a 2 dimensional dictionary for easy
		# searching.
		if entity.get_cid() == self.sent_ptr.get_cid():
			match = True

			sent_time = entity.get_log_time()
			
			tag = entity.get_tag()

			pipe_stage = tag >> 27

			sig_num = tag & 134217727

			if pipe_stage not in self.sent_events:
				self.sent_events[pipe_stage] = {sig_num:sent_time}
			else:
				self.sent_events[pipe_stage][sig_num] = sent_time
	
		# Here we are looking for a signal rcvd event. Again, we decompose the tag value. Note
		# that we decrement the pipeline stage number, as the sent event for a particular signal
		# must have come from the previous stage in the pipeline. We then search our 2 dimensional
		# dictionary based on the previous pipeline number and the signal number to see if there is
		# a matching sent event. If there is, we generate an interval event, just like we did above.
		# We also make a second check to see if these two events represent the gap between the first
		# and second elements of the pipeline. If they do, we generate a second interval event with
		# a different namespace than the first.
		if entity.get_cid() == self.rcvd_ptr.get_cid():
			match = True

			rcvd_time = entity.get_log_time()
				
			tag = entity.get_tag()

			pipe_stage = tag >> 27
			pipe_stage = pipe_stage - 1

			sig_num = tag & 134217727

			if pipe_stage not in self.sent_events:
				self.warn("Missing sent event for pipe stage "+`pipe_stage`)
				self.rejected_signal_events[tag] = rcvd_time
			elif sig_num not in self.sent_events[pipe_stage]:
				self.warn("Missing sent event for signal "+`sig_num`)
				self.rejected_signal_events[tag] = rcvd_time
			else:
				sent_time = self.sent_events[pipe_stage][sig_num]
				del self.sent_events[pipe_stage][sig_num]
				i = entities.Interval(
					self.all_gaps_ptr.get_cid(),
					sent_time, rcvd_time, tag)
				self.send_output("default", i)

				if pipe_stage == 1:
					i = entities.Interval(
						self.gap_one_ptr.get_cid(),
						sent_time, rcvd_time, tag)
					self.send_output("default", i)

		if (not match) or (match and not self.consume):
			self.send_output("default", entity)


		# If we were to do so, here is where we would implement "finalize". The "finalize" hook is
		# executed after all other portions of the filter. Because of this, one of the more common
		# uses of the "finalize" portion of the filter is operations that require the entire event
		# stream. The events received in "process" can simply be stored in a list or dictionary, and
		# then the entire set of event data will be available here, as "finalize" will not be called
		# until every event entering the filter has passed through "process". After performing post-
		# processing on the entire set of events, those that the developer desires to pass on to the
		# rest of the pipeline are sent using the same self.send_output command seen above.
