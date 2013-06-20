from datastreams.postprocess import filtering
from datastreams.postprocess import entities
from datastreams import namespaces
import os
import sys
import copy
import time

class sort(filtering.Filter):
	"""sort all the entities in a datastream.

	this is an accumulator filtering, which means that no entities
	will be output until the entire datastream has been recieved."""

	expected_parameters = {
		"sort_key" : {
			"types": "string",
			"doc" : "Time units to sort by",
			"default": "ns"
		}
	}

	process_admin = True

	def initialize(self):
		self.entities = []
		self.key = self.params["sort_key"]

	def process(self, entity):
		self.entities.append(entity)

	def finalize(self):
		self.info("Sorting begins.")
		self.entities.sort(key=lambda e: e.get_log_time()[self.key].get_value())
		self.info("Sorting finished.")

		while (self.entities):
			e = self.entities.pop(0)
			self.send(e)


class time_skip(filtering.Filter):
	expected_parameters = {
		"skip_time" : {
			"types" : ["integer"],
			"required" : True
		}
	}

	def initialize(self):
		self.target_time = None

	def process(self, entity):
		if self.target_time == None:
			b = entity.get_nanoseconds()
			self.target_time = b + (self.params["skip_time"] * 10**9)

		if (entity.get_nanoseconds() > self.target_time):
			self.send(entity)


class tag_copy(filtering.Filter):
	expected_parameters = {
		"src_event" : {
			"types" : ["string"],
			"required" : True
		},
		"dest_event" : {
			"types" : ["string"],
			"required" : True
		}
	}

	def initialize(self):
		self.src = self.get_ns_pointer(self.params["src_event"])
		self.dest = self.get_ns_pointer(self.params["dest_event"])
		self.tag = None
	
	def process(self, entity):
		if entity.get_cid() == self.src.get_cid():
			self.tag = entity.get_tag()
		elif entity.get_cid() == self.dest.get_cid():
			if self.tag != None:
				entity = entity.change_tag(self.tag)
		self.send(entity)
		

class set_tag(filtering.Filter):
	expected_parameters = {
		"tag" : {
			"types" : ["any"],
			"required" : True
		}
	}

	def process(self, entity):
		entity = entity.change_tag(self.params["tag"])
		self.send(entity)


class sink(filtering.Filter):
	def process(self, entity):
		pass


class null(filtering.Filter):
	def process(self, entity):
		self.send(entity)




class machine(filtering.Filter):

	expected_parameters = {
		"machine" : {
			"types" : ["string"],
			"required" : True,
		}
	}

	def process(self, entity):
		if entity.get_machine() == self.params["machine"]:
			self.send(entity)
	

class timestamp(filtering.Filter):
	"""convent TSC-based timestamps to nanoseconds, using data from clock
	administrative events. you can have data from multiple machines, and the
	filter will keep track of tsc-to-nanosecond correspondence for multiple 
	machines"""


	expected_parameters = {
		"redo_clock" : {
			"types" : ["boolean"],
			"doc" : "Whether to recompute timestamps for entities that already have a nanosecond value",
			"default" : False
		},
		"consume" : {
			"types" : ["boolean"],
			"doc" : "Consume clock administrative events",
			"default" : False
		}
	}

	process_admin = True

	def initialize(self):
		self.clockinfo = {}
		
		self.clockevent = self.namespace["DSTREAM_ADMIN_FAM/TIME_STATE"].get_id()
		self.redo_clock = self.params["redo_clock"]
		self.consume = self.params["consume"]
	
	def process(self, entity):

		cid = entity.get_cid()
		
		if cid == self.clockevent:
			# this is a clock synchronization event, and we need to update
			# our variables that assist in tsc-to-ns conversion
			machine = entity.get_machine()
			self.clockinfo[machine] = entity.get_extra_data()
			self.clockinfo[machine]["nsecs"] = long(
				(self.clockinfo[machine]["tv_sec"] * 10**9) +
				 self.clockinfo[machine]["tv_nsec"])
			if self.consume:
				return

		machine = entity.get_machine()
		if machine not in self.clockinfo:
			self.send(entity)

		# convert timestamps to nanoseconds
		for timetype in entity.get_times().values():
			# FIXME: should 'ns' be hard-coded?
			if self.redo_clock or "ns" not in timetype:
				# TODO: add uncertainty to converted timestamps
				#       refactor tsc-based histograms

				tsc = timetype["tsc"].get_value()
				offset_tsc = tsc - self.clockinfo[machine]["tsc"]
				offset_nsecs = ((offset_tsc * 
						self.clockinfo[machine]["mult"]) 
						>> self.clockinfo[machine]["shift"])
				timetype["ns"] = entities.TimeMeasurement(
						"ns", self.clockinfo[machine]["nsecs"] + 
						long(offset_nsecs),
						"global", 0, 0)

		self.send(entity)

class crop(filtering.Filter):

	expected_parameters = {
		"start_event": {
			"types": "string", "doc":"Start event"
		},
		"end_event": {
			"types": "string", "doc":"End event"
		}
	}

	def initialize(self):
		self.start = -1
		self.end = -1
		self.mode = 0
		self.start = self.get_ns_pointer(self.params["start_event"])
		self.end = self.get_ns_pointer(self.params["end_event"])

	def process(self, entity):
		if self.mode == 0:
			if entity.get_cid() == self.start.get_cid():
				self.mode = 1
				self.send(entity)
			else:
				return
		elif self.mode == 1:
			if entity.get_cid() == self.end.get_cid():
				self.mode = 2
			self.send(entity)
		else:
			return

class tag_group(filtering.Filter):
        def initialize(self):
		    # This dictionary will maintain the list of entities in each 
		    # tag group. The key for the dictionary shall be the tag value
		    self.tag_groups = {}
            
        def process(self,entity):
            """Choose which bucket the entity goes into based on the tag because
            the tag is the key to to the dictionary"""
            tag=entity.get_tag()
            if((tag in self.tag_groups.keys())==0):
                self.tag_groups[tag] = [entity]
            else:
                self.tag_groups[tag].append(entity)				            

        def finalize(self):
            # First write out the entities in tag order. After this close the
            # output stream.
            for tag in self.tag_groups.keys():
                for entity in self.tag_groups[tag]:
                    self.send(entity)

            # We have written all the cached entities to the output stream. We
            # now have to close the output object of this filter
            # self.output.close()

class shmem_control_read(filtering.Filter):
    expected_parameters = {
		"start_event": {
			"types": "string", "doc":"Start event"
		},
		"end_event": {
			"types": "string", "doc":"End event"
		},
        "middle_event": {
            "types": "string", "doc":"Middle Event"
        },
        "contention_interval": {
            "types": "string", "doc":"Contention Interval"
        },
        "non_contention_interval": {
            "types": "string", "doc":"Non-Contention Interval"
        },
        "consume" : {
            "types" : "boolean",
            "doc" : "Whether to delete matching entities after processing",
			"default" : False
		},
        "upperbound" : {
            "types": "integer", "doc":"Upperbound",
            "default" : 0
        }		
    }
    def initialize(self):
        self.start_ptr = self.get_ns_pointer(
                self.params["start_event"])
        self.end_ptr = self.get_ns_pointer(
                self.params["end_event"])
        self.middle_ptr = self.get_ns_pointer(
                self.params["middle_event"])
        self.contention_interval_ptr = self.get_ns_pointer(
                self.params["contention_interval"])
        self.non_contention_interval_ptr = self.get_ns_pointer(
                self.params["non_contention_interval"])
        self.upperbound = self.params["upperbound"]
        self.mode = 0
        self.contentions = 0
        self.is_contention = 0
    

    def process(self,event):
        if self.mode == 0:
            if event.get_cid() == self.start_ptr.get_cid():
                self.start_time = event.get_log_time()
                self.mode = 1
            else:
                self.send_output("default", event)
        elif self.mode == 1:
            if event.get_cid() == self.middle_ptr.get_cid():
                self.contentions = self.contentions + 1
                self.is_contention = 1
            elif event.get_cid() == self.end_ptr.get_cid():
                self.end_time = event.get_log_time()
                e = self.end_time["ns"].get_value() - self.start_time["ns"].get_value()
                if self.upperbound == 0 or e < self.upperbound:
                    if not self.is_contention:
                        i = entities.Interval(
                            self.non_contention_interval_ptr.get_cid(),
                            self.start_time, self.end_time)
                    else:
                        i = entities.Interval(
                            self.contention_interval_ptr.get_cid(),
                            self.start_time, self.end_time)
                    self.send_output("default", i)                    
                self.mode = 0
                self.is_contention = 0
            else: 
                self.send_output("default", event)
        
    def finalize(self):
        print "The number of contentions between the start and the end event is ",self.contentions


class context_switch(filtering.Filter):
	expected_parameters = {
		"start_event": {
			"types": "string", "doc":"Start event"
		},
		"end_event": {
			"types": "string", "doc":"End event"
		},
		"cs_pid": {
			"types" : "integer", "doc":"This is the pid of the process that we are tracking"
		},
		"result_event" : {
			"types" : "string",
			"doc" : "Family/event name of end event",
			"required" : True
		},
		"consume" : {
			"types" : "boolean",
			"doc" : "Whether to delete matching entities after processing",
			"default" : False
		}		
	}
	output_names = ["default", "result_event"]

	def initialize(self):
		self.start_ptr = self.get_ns_pointer(
			    self.params["start_event"])
		self.end_ptr = self.get_ns_pointer(
			    self.params["end_event"])
		self.switch_from_ptr = self.get_ns_pointer(
			    "SCHEDULER_FAM/SWITCH_FROM")	
		self.switch_to_ptr = self.get_ns_pointer(
			    "SCHEDULER_FAM/SWITCH_TO")	
		self.consume = self.params["consume"]
		self.pid = self.params["cs_pid"]
		self.away_time = 0
		self.block_count = 0
		self.already_blocked = 0
		self.mode = 0
	
	def process(self,event):
		if self.mode == 0:
			if event.get_cid() == self.start_ptr.get_cid(): 
				self.start_time = event.get_log_time("ns")
				self.mode = 1
			elif not self.consume:
				self.send_output("default", event)
		elif self.mode == 1:
			if event.get_cid() == self.switch_from_ptr.get_cid() and event.get_tag() == self.pid:
				self.from_time = event.get_log_time("ns")
				self.mode = 2
				if self.already_blocked == 0:
					self.block_count = self.block_count + 1
					self.already_blocked = 1
			elif event.get_cid() == self.end_ptr.get_cid():
				self.end_time = event.get_log_time("ns")
				result_time = self.end_time - self.start_time - self.away_time
				spec = self.namespace.get_entity_spec_byname(self.params["result_event"])
				e = entities.Event(spec.get_cid(), entities.get_zero_timedict(),
						result_time,0)
				self.send_output("result_event",e)
				self.mode = 0
				self.already_blocked = 0
				self.away_time = 0
			elif not self.consume:
				self.send_output("default", event)
		elif self.mode == 2:
			if event.get_cid() == self.switch_to_ptr.get_cid() and event.get_tag() == self.pid:
				self.to_time = event.get_log_time("ns")
				self.away_time = self.away_time + (self.to_time - self.from_time)
				self.mode = 1
			elif not self.consume:
				self.send_output("default", event)
	
	def finalize(self):
		print "The number of times this thread was blocked between the processing is "
	        print self.block_count
	
			
class narrate(filtering.Filter):
	expected_parameters = {
		"output":{"types":"string",
			  "doc":"Output file to send narration text",
			  "default":"-",
			  },
		"divisor":{"types":"real",
			   "doc":"Value to divide converted timestamps by",
			   "default":1
			   },
		"line_every_n_us":{"types":"integer",
				   "doc":"place a line every n microseconds",
				   "default":0
			},
		"print_extra_data":{"types":"boolean",
				"doc":"print extra data associated with events",
				"default":False
			},
		"print_description":{"types":"boolean",
				"doc":"print description associated with events",
				"default":True
			},
		"ignore_time":{"types":"boolean",
				"doc":"Ignore all time related operations",
				"default":False
			},
		"absolute_time":{"types":"boolean",
				"doc":"Format timestamps as time-of-day",
				"default":False
			},
		"show_admin":{"types":"boolean",
				"doc":"Format timestamps as time-of-day",
				"default":True
			}
	}

	etypemap = {
		namespaces.INTERVALTYPE : "I",
		namespaces.COUNTERTYPE  : "C",
		namespaces.OBJECTTYPE   : "O",
		namespaces.HISTOGRAMTYPE: "H",
		namespaces.EVENTTYPE    : "E",
		namespaces.INTERNALEVENTTYPE : "IE"
	}

	def initialize(self):
		if self.params["output"] == "-":
			self.outfile = sys.stdout
		else:
			self.outfile = open(self.params["output"], "w")
		self.prev_time = -1
		self.line_timetamp = 0
		self.ignore_time = self.params["ignore_time"]
		self.printf_ptr = self.get_ns_pointer("DSTREAM_ADMIN_FAM/PRINTF")

		self.process_admin = self.params["show_admin"]


	def process(self, entity):
	
		skip_rest = False

		if entity.get_cid() == self.printf_ptr.get_cid():
			ename = `entity.get_extra_data()`
			skip_rest = True
		else:
			ename = entity.get_family_name() + "/" + entity.get_name()
			if self.params["print_description"]:
				ename = ename + ": " + entity.get_description()

		if (self.ignore_time) or "ns" not in entity.get_log_time():
			timestr = "seq="+`entity.get_sequence()`
		elif self.params["absolute_time"]:
			timestr = `time.ctime(entity.get_nanoseconds()/10**9)`
		else:
			time_val = float(entity.get_nanoseconds()) / self.params["divisor"]

			if self.prev_time == -1:
				offset = 0
			else:
				offset = round((time_val - self.prev_time), 3)
			
			self.prev_time = time_val
			fmt = r'%+11.3f'
			timestr = fmt % offset
		
		clocksource = entity.get_time_object("log","tsc").get_clocksource()
		etype = self.etypemap[entity.get_type()]
		linestr = clocksource + " " + timestr + " " + etype + " " + ename
		if entity.get_type() == namespaces.EVENTTYPE and not skip_rest:
			linestr = linestr + " PID (" + `entity.get_pid()` + ")" + " TAG (" + `entity.get_tag()` + ")\n"
			if self.params["print_extra_data"] and entity.get_extra_data() != None:
				linestr = linestr + `entity.get_extra_data()`+"\n"
		elif entity.get_type() == namespaces.INTERVALTYPE:
			if not self.ignore_time:
				linestr = linestr + " (" + `entity.get_tag()` + ") (" + `entity.get_duration()`+")\n"
			else:
				linestr = linestr + " (" + `entity.get_tag()` + ")\n"

			if self.params["print_extra_data"] and entity.get_tag() != None:
				linestr = linestr + `entity.get_tag()`+"\n"
		elif entity.get_type() == namespaces.COUNTERTYPE:
			linestr = linestr + " (count=" + `entity.get_count()` + ")\n"
		elif entity.get_type() == namespaces.HISTOGRAMTYPE:
			linestr = linestr + " (count=" + `entity.get_count()` + ", avg="+`entity.get_mean()` + ")\n"
			if self.params["print_extra_data"]:
				pass
				#linestr = linestr + self.print_histogram(entity)
		elif entity.get_type() == namespaces.INTERNALEVENTTYPE:
			linestr = linestr + " PID (" + `entity.get_pid()` + ")" + " TAG (" + `entity.get_tag()` + ")\n"
		else:
			linestr = linestr + "\n"
		#linestr = linestr + `entity.time` + "\n"
		self.outfile.write(linestr)
		self.send(entity)

	def print_histogram(self, h):
		# unfinished. should print a text representation of a histogram
		bc = h.get_num_buckets()
		bd = 1
		ebc = bc
		while ebc > 70:
			bd = bd + 1
			ebc = bc / bd



	def finalize(self):
		if self.outfile != sys.stdout:
			self.outfile.close()

	def abort(self):
		if self.outfile != sys.stdout:
			self.outfile.close()
			os.remove(self.params["output"])


class tag_matcher(filtering.Filter):
	#Filters out events of those events whose tags do not match
	#	the given events or tag numbers

	expected_parameters = {
		"events" : {
			"types" : "list",
			"doc" : "List of events whose tags to match on",
			"listdef" : {
				"types" : "string"
			},
			"default" : []
		},
		"tags" : {
			"types" : "list",
			"doc" : "Tag numbers to match on",
			"listdef" : {
				"types" : "integer"
			},
			"default" : []
		},
		"invert_output" : {
			"types" : "boolean",
			"doc" : "If true, filter out only events whose tag numbers match the given events/tags",
			"default" : False
		}
	}

	def initialize(self):
		self.tags = self.params["tags"]
		self.entities = []
		self.evt_ptrs = []
		self.invert_output = self.params["invert_output"]

		for name in self.params["events"]:
			self.evt_ptrs.append(self.get_ns_pointer(name))

	def process(self, entity):
		for ptr in self.evt_ptrs:
			if entity.get_cid() == ptr.get_cid() and entity.get_tag() not in self.tags:
				self.tags.append(entity.get_tag())
		
		self.entities.append(entity)
	
	def finalize(self):

		for evt in self.entities:
			if evt.get_tag() in self.tags:
				if not self.invert_output:
					self.send_output("default", evt)
			else:
				if self.invert_output:
					self.send_output("default", evt)

class clksync_info(filtering.Filter):
	# Prints out info concerning clksync in the datastream
	# If you're having trouble with clksync, the information
	# generated by this filter may be of some help

	expected_parameters = {
		"consume" : {
			"types" : "boolean",
			"doc" : "Whether to delete matching entities after processing",
			"default" : False
		}		
	}	
	
	def initialize(self):
		self.kern_rcv_ptr = self.get_ns_pointer(
				"CLKSYNC/KERN_RCV_PKT")
		self.kern_xmt_ptr = self.get_ns_pointer(
				"CLKSYNC/KERN_XMT_PKT")
		self.get_nfo_ptr = self.get_ns_pointer(
				"CLKSYNC/KERN_GET_INFO")
		self.adj_ptr = self.get_ns_pointer(
				"CLKSYNC/ADJUST")
		self.sync_end_tsc_ptr = self.get_ns_pointer(
				"CLKSYNC/SYNC_END_TSC")
		self.delay_ptr = self.get_ns_pointer(
				"CLKSYNC/DELAY")
		self.get_client_nfo_ptr = self.get_ns_pointer(
				"NTPDATE/NTP_CLIENT_GET_NFO")
		self.client_rcv_ptr = self.get_ns_pointer(
				"NTPDATE/CLIENT_RCV_PKT")
		self.server_xmt_ptr = self.get_ns_pointer(
				"NTPDATE/SERVER_XMT_PKT")
		self.start_tsc_ptr = self.get_ns_pointer(
				"NTPDATE/START_TSC")
		self.end_tsc_ptr = self.get_ns_pointer(
				"NTPDATE/END_TSC")
		self.xmt_tsc_ptr = self.get_ns_pointer(
				"NTPDATE/XMT_TSC")
		self.rcv_tsc_ptr = self.get_ns_pointer(
				"NTPDATE/RECV_TSC")
		self.ntp_offset_ptr = self.get_ns_pointer(
				"NTPDATE/NTP_OFFSET")
		self.ntp_delay_ptr = self.get_ns_pointer(
				"NTPDATE/NTP_DELAY")
		self.ntp_raw_delay_ptr = self.get_ns_pointer(
				"NTPDATE/NTP_RAW_DELAY")
		self.ntp_start_ptr = self.get_ns_pointer(
				"NTPDATE/NTP_START_TIME")
		self.xtime_start_ptr = self.get_ns_pointer(
				"NTPDATE/XTIME_START_TIME")
		self.ntp_end_ptr = self.get_ns_pointer(
				"NTPDATE/NTP_END_TIME")
		self.xtime_end_ptr = self.get_ns_pointer(
				"NTPDATE/XTIME_END_TIME")
		self.ntp_recv_ptr = self.get_ns_pointer(
				"NTPDATE/NTP_RECV_TIME")
		self.xtime_recv_ptr = self.get_ns_pointer(
				"NTPDATE/XTIME_RECV_TIME")
		self.ntp_xmt_ptr = self.get_ns_pointer(
				"NTPDATE/NTP_XMT_TIME")
		self.xtime_xmt_ptr = self.get_ns_pointer(
				"NTPDATE/XTIME_XMT_TIME")
		self.ntp_t1_t0_ptr = self.get_ns_pointer(
				"NTPDATE/T1_T0")
		self.ntp_t2_t3_ptr = self.get_ns_pointer(
				"NTPDATE/T2_T3")

		self.consume = self.params["consume"]
		self.evts = {}
		self.chosen_end_tscs = []

	def process(self, entity):
		match = False
	
                # The basic idea behind this filter is that ntpdate
                # sends packets back and forth between client and
                # server machines. Each round trip packet is tagged
                # with some pkt_id and the information for each
                # packet can be narrated and observed with this
                # filter.

		if entity.get_cid() == self.kern_rcv_ptr.get_cid():
			# Generated in the kernel code that is called
			# when a packet is received and after our timestamp
			# is attached to the packet
			# XXX: Each pkt_id may have more than one kern_xmt or
			# kern_rcv event. Hence we store these as a list

			rcv_data = entity.get_extra_data()
			pkt_id = rcv_data["pkt_id"]
			if self.evts.has_key(pkt_id):
				if self.evts[pkt_id].has_key("kern_rcv_evts"):
					self.evts[pkt_id]["kern_rcv_evts"].append(rcv_data)
				else:
					self.evts[pkt_id]["kern_rcv_evts"] = []
					self.evts[pkt_id]["kern_rcv_evts"].append(rcv_data)
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["kern_rcv_evts"] = []
				self.evts[pkt_id]["kern_rcv_evts"].append(rcv_data)
			match = True
		elif entity.get_cid() == self.kern_xmt_ptr.get_cid():
			# Generated in the kernel code that is called
			# right before a packet is transmitted

			xmt_data = entity.get_extra_data()
			pkt_id = xmt_data["pkt_id"]
			if self.evts.has_key(pkt_id):
				if self.evts[pkt_id].has_key("kern_xmt_evts"):
					self.evts[pkt_id]["kern_xmt_evts"].append(xmt_data)
				else:
					self.evts[pkt_id]["kern_xmt_evts"] = []
					self.evts[pkt_id]["kern_xmt_evts"].append(xmt_data)
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["kern_xmt_evts"] = []
				self.evts[pkt_id]["kern_xmt_evts"].append(xmt_data)
			match = True
		elif entity.get_cid() == self.get_client_nfo_ptr.get_cid():
			# Generated in the client ntpdate code
			# Prints out nfo associated with the packet
			# we are about to process
			
			get_client_nfo_data = entity.get_extra_data()
			pkt_id = entity.get_tag()
			if self.evts.has_key(pkt_id):
				self.evts[pkt_id]["get_client_nfo_evt"] = get_client_nfo_data
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["get_client_nfo_evt"] = get_client_nfo_data
			match = True
		elif entity.get_cid() == self.client_rcv_ptr.get_cid():
			# Generated in the ntp code when ntp has received
			# the packet back from the server and is about to
			# do processing on its contents

			client_rcv_data = entity.get_extra_data()
			if self.evts.has_key(client_rcv_data["pkt_id"]):
				self.evts[client_rcv_data["pkt_id"]]["user_client_rcv_evt"] = client_rcv_data
			else:
				self.evts[client_rcv_data["pkt_id"]] = {}
				self.evts[client_rcv_data["pkt_id"]]["user_client_rcv_evt"] = client_rcv_data
			match = True
		elif entity.get_cid() == self.server_xmt_ptr.get_cid():
			# Generated in the server's ntp code
			# The attached packet should have the timestamp 
			# information from the first half of the round
			# round trip, but has not yet been timestamped
			# by the server kernel code
			# XXX: Has not been implemented

			server_xmt_data = entity.get_extra_data()
			if self.evts.has_key(server_xmt_data["pkt_id"]):
				self.evts[server_xmt_data["pkt_id"]]["user_server_xmt_evt"] = server_xmt_data
			else:
				self.evts[server_xmt_data["pkt_id"]] = {}
				self.evts[server_xmt_data["pkt_id"]]["user_server_xmt_evt"] = server_xmt_data
			match = True
		elif entity.get_cid() == self.start_tsc_ptr.get_cid():
			# Generated after offset has been computed
			# for a particular clksync request

			start_tsc = entity.get_extra_data()
			pkt_id = entity.get_tag()
			if self.evts.has_key(pkt_id):
				self.evts[pkt_id]["start_tsc"] = start_tsc
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["start_tsc"] = start_tsc
			match = True
		elif entity.get_cid() == self.end_tsc_ptr.get_cid():
			# Generated after offset has been computed
			# for a particular clksync request
			end_tsc = entity.get_extra_data()
			pkt_id = entity.get_tag()
			if self.evts.has_key(pkt_id):
				self.evts[pkt_id]["end_tsc"] = end_tsc
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["end_tsc"] = end_tsc
			match = True
		elif entity.get_cid() == self.xmt_tsc_ptr.get_cid():
			# Generated after offset has been computed
			# for a particular clksync request
			xmt_tsc = entity.get_extra_data()
			pkt_id = entity.get_tag()
			if self.evts.has_key(pkt_id):
				self.evts[pkt_id]["xmt_tsc"] = xmt_tsc
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["xmt_tsc"] = xmt_tsc
			match = True
		elif entity.get_cid() == self.rcv_tsc_ptr.get_cid():
			# Generated after offset has been computed
			# for a particular clksync request
			rcv_tsc = entity.get_extra_data()
			pkt_id = entity.get_tag()
			if self.evts.has_key(pkt_id):
				self.evts[pkt_id]["rcv_tsc"] = rcv_tsc
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["rcv_tsc"] = rcv_tsc
			match = True
		elif entity.get_cid() == self.ntp_offset_ptr.get_cid():
			# Generated after offset has been computed
			# for a particular clksync request
			ntp_offset = float(entity.get_extra_data())
			pkt_id = entity.get_tag()
			if self.evts.has_key(pkt_id):
				self.evts[pkt_id]["ntp_offset"] = ntp_offset
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["ntp_offset"] = ntp_offset
			match = True
		elif entity.get_cid() == self.ntp_delay_ptr.get_cid():
			# Generated after delay has been computed
			# for a particular clksync request
			ntp_delay = float(entity.get_extra_data())
			pkt_id = entity.get_tag()
			if self.evts.has_key(pkt_id):
				self.evts[pkt_id]["ntp_delay"] = ntp_delay
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["ntp_delay"] = ntp_delay
			match = True
		elif entity.get_cid() == self.ntp_raw_delay_ptr.get_cid():
			# Generated after raw_delay has been computed
			# for a particular clksync request
			ntp_raw_delay = float(entity.get_extra_data())
			pkt_id = entity.get_tag()
			if self.evts.has_key(pkt_id):
				self.evts[pkt_id]["ntp_raw_delay"] = ntp_raw_delay
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["ntp_raw_delay"] = ntp_raw_delay
			match = True
		elif entity.get_cid() == self.ntp_start_ptr.get_cid():
			# Generated after offset has been computed
			# for a particular clksync request
			ntp_start = entity.get_extra_data()
			pkt_id = entity.get_tag()
			if self.evts.has_key(pkt_id):
				self.evts[pkt_id]["ntp_start"] = ntp_start
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["ntp_start"] = ntp_start
			match = True
		elif entity.get_cid() == self.ntp_end_ptr.get_cid():
			# Generated after offset has been computed
			# for a particular clksync request
			ntp_end = entity.get_extra_data()
			pkt_id = entity.get_tag()
			if self.evts.has_key(pkt_id):
				self.evts[pkt_id]["ntp_end"] = ntp_end
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["ntp_end"]
			match = True
		elif entity.get_cid() == self.ntp_xmt_ptr.get_cid():
			# Generated after offset has been computed
			# for a particular clksync request
			ntp_xmt = entity.get_extra_data()
			pkt_id = entity.get_tag()
			if self.evts.has_key(pkt_id):
				self.evts[pkt_id]["ntp_xmt"] = ntp_xmt
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["ntp_xmt"] = ntp_xmt
			match = True
		elif entity.get_cid() == self.ntp_recv_ptr.get_cid():
			# Generated after offset has been computed
			# for a particular clksync request
			ntp_recv = entity.get_extra_data()
			pkt_id = entity.get_tag()
			if self.evts.has_key(pkt_id):
				self.evts[pkt_id]["ntp_recv"] = ntp_recv
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["ntp_recv"] = ntp_recv
			match = True
		elif entity.get_cid() == self.ntp_t1_t0_ptr.get_cid():
			# Generated after offset has been computed
			# for a particular clksync request
			ntp_t1_t0 = float(entity.get_extra_data())
			pkt_id = entity.get_tag()
			if self.evts.has_key(pkt_id):
				self.evts[pkt_id]["ntp_t1_t0"] = ntp_t1_t0
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["ntp_t1_t0"] = ntp_t1_t0
			match = True
		elif entity.get_cid() == self.ntp_t2_t3_ptr.get_cid():
			# Generated after offset has been computed
			# for a particular clksync request
			ntp_t2_t3 = float(entity.get_extra_data())
			pkt_id = entity.get_tag()
			if self.evts.has_key(pkt_id):
				self.evts[pkt_id]["ntp_t2_t3"] = ntp_t2_t3
			else:
				self.evts[pkt_id] = {}
				self.evts[pkt_id]["ntp_t2_t3"] = ntp_t2_t3
			match = True
		elif entity.get_cid() == self.sync_end_tsc_ptr.get_cid():
			self.chosen_end_tscs.append(entity.get_extra_data())
			match = True
		elif entity.get_cid() == self.adj_ptr.get_cid():
			match = True
		elif entity.get_cid() == self.delay_ptr.get_cid():
			match = True

		if not match or (match and not self.consume):
			self.send_output("default", entity)
			return
	
	def finalize(self):

		# The number of polls ntpdate does to determine an offset
		# We use this to calculate averages of a given call to ntpdate
		ntpdate_num = 8
		ntpdate_count = 0
		ntpdate_min_offset = None
		ntpdate_max_offset = None
		ntpdate_avg_offset = 0

		for pkt_id in self.evts.iterkeys():
			ntpdate_count = ntpdate_count + 1
			ntpdate_avg_offset = ntpdate_avg_offset + self.evts[pkt_id]["ntp_offset"]

			if ntpdate_min_offset is None or self.evts[pkt_id]["ntp_offset"] < ntpdate_min_offset:
				ntpdate_min_offset = self.evts[pkt_id]["ntp_offset"]
			if ntpdate_max_offset is None or self.evts[pkt_id]["ntp_offset"] > ntpdate_max_offset:
				ntpdate_max_offset = self.evts[pkt_id]["ntp_offset"]

			if self.evts[pkt_id]["end_tsc"] in self.chosen_end_tscs:
				print "NTPDATE chose packet: ", pkt_id

				print "Kernel rcv events"
				for evt in self.evts[pkt_id]["kern_rcv_evts"]:
					print "saddr:\t", evt["saddr"],
					print "\tdaddr:\t", evt["daddr"]
					print "start_ts:\t", evt["start_ts"]
					print "rx_ts:\t\t", evt["rx_ts"]
					print "tx_ts:\t\t", evt["tx_ts"]
					print "end_ts:\t\t", evt["end_ts"]
					print "xtime_tv_sec:\t", evt["xtime_tv_sec"]
					print "xtime_tv_nsec:\t", evt["xtime_tv_nsec"]
					print "xtime_tsc:\t", evt["xtime_tsc"]
					print "tsc_khz:\t", evt["tsc_khz"], "\n"

				print "Kernel xmt events"
				for evt in self.evts[pkt_id]["kern_xmt_evts"]:
					print "saddr:\t", evt["saddr"],
					print "\tdaddr:\t", evt["daddr"]
					print "start_ts:\t", evt["start_ts"]
					print "rx_ts:\t\t", evt["rx_ts"]
					print "tx_ts:\t\t", evt["tx_ts"]
					print "end_ts:\t\t", evt["end_ts"]
					print "xtime_tv_sec:\t", evt["xtime_tv_sec"]
					print "xtime_tv_nsec:\t", evt["xtime_tv_nsec"]
					print "xtime_tsc:\t", evt["xtime_tsc"]
					print "tsc_khz:\t", evt["tsc_khz"], "\n"

				print "User client rcv evt"
				print "saddr:\t", self.evts[pkt_id]["user_client_rcv_evt"]["saddr"],
				print "\tdaddr:\t", self.evts[pkt_id]["user_client_rcv_evt"]["daddr"]
				print "start_ts:\t", self.evts[pkt_id]["user_client_rcv_evt"]["start_ts"]
				print "rx_ts:\t\t", self.evts[pkt_id]["user_client_rcv_evt"]["rx_ts"]
				print "tx_ts:\t\t", self.evts[pkt_id]["user_client_rcv_evt"]["tx_ts"]
				print "end_ts:\t\t", self.evts[pkt_id]["user_client_rcv_evt"]["end_ts"]
				print "xtime_tv_sec:\t", self.evts[pkt_id]["user_client_rcv_evt"]["xtime_tv_sec"]
				print "xtime_tv_nsec:\t", self.evts[pkt_id]["user_client_rcv_evt"]["xtime_tv_nsec"]
				print "xtime_tsc:\t", self.evts[pkt_id]["user_client_rcv_evt"]["xtime_tsc"]
				print "tsc_khz:\t", self.evts[pkt_id]["user_client_rcv_evt"]["tsc_khz"], "\n"

				print "User client info"
				print "tv_sec:\t\t", self.evts[pkt_id]["get_client_nfo_evt"]["tv_sec"]
				print "tv_nsec:\t", self.evts[pkt_id]["get_client_nfo_evt"]["tv_nsec"]
				print "tsc:\t\t", self.evts[pkt_id]["get_client_nfo_evt"]["tsc"]
				print "tsckhz:\t\t", self.evts[pkt_id]["get_client_nfo_evt"]["tsckhz"]
				print "shift:\t\t", self.evts[pkt_id]["get_client_nfo_evt"]["shift"]
				print "mult:\t\t", self.evts[pkt_id]["get_client_nfo_evt"]["mult"]
				print "irq:\t\t", self.evts[pkt_id]["get_client_nfo_evt"]["irq"], "\n"

				print "NTPDATE: T1-T0: %11.11f" % (self.evts[pkt_id]["ntp_t1_t0"] * (10 ** 6))
				print "NTPDATE: T2-T3: %11.11f" % (self.evts[pkt_id]["ntp_t2_t3"] * (10 ** 6))
				print "NTPDATE: Raw Delay: %11.11f" % (self.evts[pkt_id]["ntp_raw_delay"] * (10 ** 6))
				print "NTPDATE: Delay: %11.11f" % (self.evts[pkt_id]["ntp_delay"] * (10 ** 6))
				print "Offset applied: %11.11f" % (self.evts[pkt_id]["ntp_offset"] * (10 ** 6))
			
			if ntpdate_count % ntpdate_num == 0:
				ntpdate_avg_offset = ntpdate_avg_offset / ntpdate_num
				print "Average offset from ntpdate: %11.11f" % (ntpdate_avg_offset * (10 ** 6))
				print "Minimum offset from ntpdate: %11.11f" % (ntpdate_min_offset * (10 ** 6))
				print "Maximum offset from ntpdate: %11.11f" % (ntpdate_max_offset * (10 ** 6)), "\n"
				ntpdate_count = 0
				ntpdate_min_offset = None
				ntpdate_max_offset = None
				ntpdate_avg_offset = 0
