from datastreams.postprocess import filtering
from datastreams.postprocess import entities
import discovery.oca_definitions
from datastreams import namespaces
from datastreams.postprocess import syscall

class execution_interval_histogram(filtering.Filter):
	"""
	Creates execution intervals from SWITCH_TO and SWITCH_FROM OCA events
	"""	
	expected_parameters = {
		"exec_name" : {
			"types" : "string",
			"doc" : "Process name to create intervals for",
			"required" : True,
		},
		"histo_type" : {
			"types" : "string",
			"doc" : "Type of execution interval to create",
			"constraints" : ["unpreempted", "glommed", "both", "glom_count"],
			"required" : True,
		},
		"histo_name" : {
			"types" : "string",
			"doc" : "Family/event name of histogram to create",
			"required" : True,
		},
		"buckets" : {
			"types" : "integer",
			"doc" : "Number of buckets in histogram",
			"default" : 10,
		},
		"units" : {
			"types" : "string",
			"doc" : "Units to compute execution intervals in",
			"default" : "ns",
		},
		"consume" : {
			"types" : "boolean",
			"doc" : "Whether to delete matching entities after processing",
			"default" : False
		},
	}
	
	def initialize(self):
		self.OCA_ptr     = self.get_ns_pointer("OCA/ACTIONS")	
		self.exec_name   = self.params["exec_name"]
		self.val_type    = self.params["histo_type"]
		self.hist_ptr    = self.get_ns_pointer(self.params["histo_name"])
		self.buckets     = self.params["buckets"]
		self.consume     = self.params["consume"]
		self.units       = self.params["units"]
		self.start_time  = None
		self.unp_time    = 0
		self.glom_time   = 0
		self.total_time  = 0
		self.is_glom_val = False
		self.val         = 0
		self.values      = []

	def process(self, entity):
		
		#
		# For glommed histo, take the first switch_to time and throw away subsequent
		# switch_to's until until we have a switch_from that blocks.
		# Corrolary to histo_2: histogram showing number of executions until we get
		# an execution interval that blocks.
		# Recreate histograms with special SDF's. histo 1 and histo 2 should be the
		# same under the SDF's because X should always run until it blocks.
		#
	
		# Does not match non OCA events
		if not entity.get_cid() == self.OCA_ptr.get_cid():
			self.send_output("default", entity)
			return	
		
		log_time = entity.get_log_time()
		data = entity.get_extra_data()

		# Do not match events that are not switch to or switch from events
		# or are not for the process we are emitting intervals for
		#
		if (not data[OCA_TYPE] == OCA_SWITCH_TO \
		and not data[OCA_TYPE] == OCA_SWITCH_FROM) \
     		or not data[OCA_ARG_EXEC_NAME] == self.exec_name:
			self.send_output("default", entity)
			return

		# Can context switch events occur out of order?
		if data[OCA_TYPE] == OCA_SWITCH_TO:
			self.start_time = log_time[self.units].get_value()
		elif data[OCA_TYPE] == OCA_SWITCH_FROM and not data[OCA_ARG_PREEMPTED]:
			if self.start_time == None:
				print "WARNING: Got OCA_SWITCH_FROM without corresponding start time",
				print "OCA_PID: %d" % data[OCA_ARG_PID]
				return
	
			if self.val_type == "glom_count":
				self.val += 1
			else:
				self.val += (log_time[self.units].get_value() - self.start_time)
			
			# Add the value to be graphed.
			# unpreempted - Omit execution intervals glommed together
			# glommed - Omit execution intervals that block after one 
			# both - graph both
			# glom_count - Graph of how many non blocking intervals were
			# 	       glommed together to create glommed intervals
			#
			if self.val_type == "unpreempted" and not self.is_glom_val:
				self.values.append(self.val)
			elif self.val_type == "glommed" and self.is_glom_val:
				self.values.append(self.val)
			elif self.val_type == "both":
				self.values.append(self.val)
			elif self.val_type == "glom_count" and self.is_glom_val:
				self.values.append(self.val)

			self.start_time = None
			self.is_glom_val= False
			self.val = 0
		else:
			# OCA_SWITCH_FROM that was preempted
			if self.start_time == None:
				print "WARNING: Got OCA_SWITCH_FROM without corresponding start time",
				print "OCA_PID: %d" % data[OCA_ARG_PID]
				return

			self.is_glom_val= True
			if self.val_type == "glom_count":
				self.val += 1
			else: 
				self.val += (log_time[self.units].get_value() - self.start_time)

			self.start_time = None

		if not self.consume:
			self.send_output("default", entity)

	def finalize(self):
		if not self.values:
			print "WARNING: No execution intervals found"
			return

		mn = min(self.values)
		mx = max(self.values)
		# add a bit of extra headroom so max value doesn't get
		# marked as overflow
		bsize = (float(mx) - float(mn)) / self.buckets
		mx = mx + (bsize / 100)

		hist = entities.Histogram(self.hist_ptr.get_cid(), None, \
			    mn, mx, self.buckets)

		for i in self.values:
			hist.add_value(i)
	
		self.send_output("default", hist)
	
class execution_stats (filtering.Filter):
	
	expected_parameters = {
		"exec_name" : {
			"types" : "string",
			"doc" : "Process name to create intervals for",
			"required" : True,
		},
		"title" : {
			"types" : "string",
			"doc" : "String to preface stats with",
			"required" : True,
		},
		"filename" : {
			"types" : "string",
			"doc" : "Filename to dump stats into",
			"default" : "-",
		},
		"append" : {
			"types" : "boolean",
			"doc" : "Append to the given file",
			"default" : False
		},
		"units" : {
			"types" : "string",
			"doc" : "Units to compute execution intervals in",
			"default" : "ns",
		},
		"consume" : {
			"types" : "boolean",
			"doc" : "Whether to delete matching entities after processing",
			"default" : False
		},
	}
	
	def initialize(self):
		self.OCA_ptr     = self.get_ns_pointer("OCA/ACTIONS")	
		self.exec_name   = self.params["exec_name"]
		self.title       = self.params["title"]
		self.consume     = self.params["consume"]
		self.units       = self.params["units"]
		self.start_time  = None
		self.unp_vals    = 0
		self.glom_vals   = 0
		self.total_vals  = 0
		self.unp_execs   = 0
		self.blk_execs   = 0
		self.total_execs = 0
		self.unp_time    = 0
		self.glom_time   = 0
		self.total_time  = 0
		self.is_glom_val = False

		if self.params["filename"] == "-":
			self.outfile = sys.stdout
		else:
			if self.params["append"]:
				self.outfile = open(self.params["filename"], "a")
			else:
				self.outfile = open(self.params["filename"], "w")

	def process(self, entity):
		
		# Does not match non OCA events
		if not entity.get_cid() == self.OCA_ptr.get_cid():
			self.send_output("default", entity)
			return	
		
		log_time = entity.get_log_time()
		data = entity.get_extra_data()

		# Do not match events that are not switch to or switch from events
		# or are not for the process we are emitting intervals for
		#
		if (not data[OCA_TYPE] == OCA_SWITCH_TO \
		and not data[OCA_TYPE] == OCA_SWITCH_FROM) \
     		or not data[OCA_ARG_EXEC_NAME] == self.exec_name:
			self.send_output("default", entity)
			return

		if data[OCA_TYPE] == OCA_SWITCH_TO:
			self.start_time = log_time[self.units].get_value()
		elif data[OCA_TYPE] == OCA_SWITCH_FROM and not data[OCA_ARG_PREEMPTED]:
			if self.start_time == None:
				print "WARNING: Got OCA_SWITCH_FROM without corresponding start time",
				print "OCA_PID: %d" % data[OCA_ARG_PID]
				return

			if not self.is_glom_val:
				self.unp_time += (log_time[self.units].get_value() - self.start_time)
				self.unp_vals += 1
			else:
				self.glom_time += (log_time[self.units].get_value() - self.start_time)
				self.glom_vals += 1
	
			self.blk_execs += 1
			self.total_execs += 1
			self.total_vals += 1
			self.total_time += (log_time[self.units].get_value() - self.start_time)
			self.start_time = None
			self.is_glom_val = False
		else:
			# OCA_SWITCH_FROM that was preempted
			if self.start_time == None:
				print "WARNING: Got OCA_SWITCH_FROM without corresponding start time",
				print "OCA_PID: %d" % data[OCA_ARG_PID]
				return

			
			self.unp_execs += 1
			self.total_execs += 1
			self.glom_time += (log_time[self.units].get_value() - self.start_time)
			self.total_time += (log_time[self.units].get_value() - self.start_time)
			self.is_glom_val = True
			self.start_time = None

		if not self.consume:
			self.send_output("default", entity)

	def finalize(self):

		pct_unp_execs = 100 * float(self.unp_execs) / self.total_execs
		pct_blk_execs = 100 * float(self.blk_execs) / self.total_execs
		pct_unp_vals = 100 * float(self.unp_vals) / self.total_vals
		pct_glom_vals = 100 * float(self.glom_vals) / self.total_vals
		pct_unp_time = 100 * float(self.unp_time) / self.total_time
		pct_glom_time = 100 * float(self.glom_time) / self.total_time

		print >> self.outfile, "%s\n" % self.title
		print >> self.outfile, "Total Execs:\t\t%d" % self.total_execs
		print >> self.outfile, "Unpreempted Execs:\t%d" % self.unp_execs
		print >> self.outfile, "Pct. Unpreempted Execs:\t%.2f" % pct_unp_execs
		print >> self.outfile, "Blocked Execs:\t\t%d" % self.blk_execs
		print >> self.outfile, "Pct. Blocked Execs:\t%.2f" % pct_blk_execs
		print >> self.outfile, "Total Vals:\t\t%d\nTotal Time(ns):\t\t%d" \
				% (self.total_vals, self.total_time)
		print >> self.outfile, "Unpreempted Vals\t%d\nUnpreempted Time(ns):\t%d" \
				% (self.unp_vals, self.unp_time)
		print >> self.outfile, "Pct. Unpreempted Vals\t%.2f\nPct. Unpreempted Time:\t%.2f" \
				% (pct_unp_vals, pct_unp_time)
		print >> self.outfile, "Glommed Vals:\t\t%d\nGlommed Time(ns):\t%d" \
				% (self.glom_vals, self.glom_time)
		print >> self.outfile, "Pct. Glommed Vals\t%.2f\nPct. Glommed Time:\t%.2f\n\n" \
				% (pct_glom_vals, pct_glom_time)

class server_info(filtering.Filter):
	expected_parameters = {
		"server_name" : {
			"types" : "string",
			"doc" : "Server exec name to analyze",
			"required" : True,
		},
		"stats_title" : {
			"types" : "string",
			"doc" : "String to preface stats with",
			"required" : True,
		},
		"filename" : {
			"types" : "string",
			"doc" : "Filename to dump stats into",
			"default" : "-",
		},
		"units" : {
			"types" : "string",
			"doc" : "Units to compute execution intervals in",
			"default" : "ns",
		},
		"comp_read_bytes_histo" : {
			"types" : "string",
			"doc" : "Family/event name of histogram to create",
			"default" : "",
		},
		"comp_read_bytes_buckets" : {
			"types" : "integer",
			"doc" : "Buckets in histogram to create",
			"default" : 10,
		},
		"comp_read_count_histo" : {
			"types" : "string",
			"doc" : "Family/event name of histogram to create",
			"default" : "",
		},
		"comp_read_count_buckets" : {
			"types" : "integer",
			"doc" : "Buckets in histogram to create",
			"default" : 10,
		},
		"comp_sent_bytes_histo" : {
			"types" : "string",
			"doc" : "Family/event name of histogram to create",
			"default" : "",
		},
		"comp_sent_bytes_buckets" : {
			"types" : "integer",
			"doc" : "Buckets in histogram to create",
			"default" : 10,
		},
		"all_read_bytes_histo" : {
			"types" : "string",
			"doc" : "Family/event name of histogram to create",
			"default" : "",
		},
		"all_read_bytes_buckets" : {
			"types" : "integer",
			"doc" : "Buckets in histogram to create",
			"default" : 10,
		},
		"all_read_count_histo" : {
			"types" : "string",
			"doc" : "Family/event name of histogram to create",
			"default" : "",
		},
		"all_read_count_buckets" : {
			"types" : "integer",
			"doc" : "Buckets in histogram to create",
			"default" : 10,
		},
		"unread_bytes_histo" : {
			"types" : "string",
			"doc" : "Family/event name of histogram to create",
			"default" : "",
		},
		"unread_bytes_buckets" : {
			"types" : "integer",
			"doc" : "Buckets in histogram to create",
			"default" : 10,
		},
		"consume" : {
			"types" : "boolean",
			"doc" : "Whether to delete matching entities after processing",
			"default" : False
		},
	}

	def initialize(self):
		self.OCA_ptr                = self.get_ns_pointer("OCA/ACTIONS")	
		self.server_name            = self.params["server_name"]
		self.stats_title            = self.params["stats_title"]
		self.consume                = self.params["consume"]	
		self.units		    = self.params["units"]
		self.server_pid             = -1
		self.server_socks	    = {}
		self.client_socks	    = {}
		self.unrelated_clients      = []
		self.server_bytes_read      = {}
		self.server_bytes_wrote     = {}
		self.other_bytes_read       = {}
		self.other_bytes_wrote      = {}
		self.comp_read_bytes_val    = 0
		self.comp_read_count_val    = 0
		self.comp_sent_bytes_val    = 0
		self.all_read_bytes_val     = 0
		self.all_read_count_val     = 0
		self.comp_read_bytes_values = []
		self.comp_read_count_values = []
		self.comp_sent_bytes_values = []
		self.all_read_bytes_values  = []
		self.all_read_count_values  = []
		self.start_time             = None
		self.total_execs            = 0
		self.total_time             = 0
		self.total_vals             = 0
		#self.all_wrote_bytes_val = 0
		#self.all_wrote_count_val = 0
		#self.pending_server_work = {}

		if self.params["filename"] == "-":
			self.outfile = sys.stdout
		else:
			self.outfile = open(self.params["filename"], "w")
		
		self.comp_read_bytes_histo  = None
		self.comp_read_count_histo  = None
		self.comp_sent_bytes_histo  = None
		self.all_read_bytes_histo   = None
		self.all_read_count_histo   = None
		self.unread_bytes_histo     = None

		if self.params["comp_read_bytes_histo"]:
			self.comp_read_bytes_histo = \
				self.get_ns_pointer(self.params["comp_read_bytes_histo"]) 
		if self.params["comp_read_bytes_histo"]:
			self.comp_read_count_histo = \
				self.get_ns_pointer(self.params["comp_read_count_histo"]) 
		if self.params["comp_read_bytes_histo"]:
			self.comp_sent_bytes_histo = \
				self.get_ns_pointer(self.params["comp_sent_bytes_histo"]) 
		if self.params["comp_read_bytes_histo"]:
			self.all_read_bytes_histo = \
				self.get_ns_pointer(self.params["all_read_bytes_histo"])
		if self.params["comp_read_bytes_histo"]:
			self.all_read_count_histo = \
				self.get_ns_pointer(self.params["all_read_count_histo"])
		if self.params["unread_bytes_histo"]:
			self.all_read_count_histo = \
				self.get_ns_pointer(self.params["unread_bytes_histo"])
		
		self.comp_read_bytes_buckets  = self.params["comp_read_bytes_buckets"]
		self.comp_read_count_buckets  = self.params["comp_read_count_buckets"]
		self.comp_sent_bytes_buckets  = self.params["comp_sent_bytes_buckets"]
		self.all_read_bytes_buckets   = self.params["all_read_bytes_buckets"]
		self.all_read_count_buckets   = self.params["all_read_count_buckets"]
		self.unread_bytes_buckets     = self.params["unread_bytes_buckets"]

	def process(self, entity):
		
		# Does not match non OCA events
		if not entity.get_cid() == self.OCA_ptr.get_cid():
			self.send_output("default", entity)
			return	
		
		log_time = entity.get_log_time()
		data = entity.get_extra_data()

		if data[OCA_TYPE] == OCA_SWITCH_TO \
		and data[OCA_ARG_PID] == self.server_pid:
			self.start_time = log_time[self.units].get_value()
			self.comp_read_bytes_val = 0
			self.comp_read_count_val = 0
			self.all_read_bytes_val = 0
			self.all_read_count_val = 0
			#self.all_wrote_bytes_val = 0
			#self.all_wrote_count_val = 0

			self.comp_sent_bytes_values.append(self.comp_sent_bytes_val)

		elif data[OCA_TYPE] == OCA_SWITCH_FROM \
		and data[OCA_ARG_PID] == self.server_pid:
			#
			# start_time gets set when we first discover the server
			# We should not expect this error as the result of a 
			# bootstrapping problem
			#
			if self.start_time == None:
				print "WARNING: Server got OCA_SWITCH_FROM without", \
					" corresponding OCA_SWITCH_TO"
				return
			
			self.comp_sent_bytes_val = 0
			self.total_execs += 1
			self.total_vals += 1
			self.total_time += (log_time[self.units].get_value() \
			       		- self.start_time)
			
			self.comp_read_bytes_values.append(self.comp_read_bytes_val)
			self.comp_read_count_values.append(self.comp_read_count_val)
			self.all_read_bytes_values.append(self.all_read_bytes_val)
			self.all_read_count_values.append(self.all_read_count_val)	

			self.start_time = None

		elif data[OCA_TYPE] == OCA_SOCKET_ACCEPT \
		and data[OCA_ARG_PID] == self.server_pid:
			#
			# If the server is finishing a connection, add the
			# connection ID (server system/inode IDs, client
			# system/inode IDs) to our list of known connection
			# IDs if its not specifically known to be an unrelated
			# connection
			#
			sock_id = data[OCA_ARG_SOCK_ID]
			if not sock_id[1] in self.unrelated_clients:
				self.server_socks[sock_id[0]] = sock_id[1]
				self.client_socks[sock_id[1]] = sock_id[0]

				#
				# If we have accumulated work before the accept,
				# add this work to the last sent_bytes interval
				#
				if self.other_bytes_wrote.has_key(sock_id[1]):
					#
					# It is possible the client end had already sent
					# some data to the server (in anticipation of the
					# server accpeting) without the server having
					# already accepted. This data should be counted as
					# data sent to the server by our computation.  The 
					# assumption here is, the last time the server 
					# blocked was on this accept call. Therefore, this
					# data is added to the last interval of data sent
					# to the server when the computation was switched to
					#
					self.comp_sent_bytes_values[-1] += \
						self.other_bytes_wrote[sock_id[1]]

					#self.pending_server_work[sock_id[0]] = \
					#	self.other_bytes_wrote[sock_id[1]]
					#else:
					#self.pending_server_work[sock_id[0]] = 0

		elif data[OCA_TYPE] == OCA_UNRELATED_CLIENT_CONN:
			#
			# XXX: We should probably have two classes of processes
			# added to the discovered group. 1) Processes that are
			# part of the computation and may also add other processes
			# they are related to to the group. 2) Processes that
			# are part of the computation, but do not add to the group
			# when they connect to other processes
			#
			self.unrelated_clients.append(data[OCA_ARG_PC_ID])

		elif data[OCA_TYPE] == OCA_READ \
		or data[OCA_TYPE] == OCA_READV \
		or data[OCA_TYPE] == OCA_SOCKET_RECV_FROM \
		or data[OCA_TYPE] == OCA_SOCKET_RECV_MSG:

			read_id = data[OCA_ARG_PC_ID]
			size = data[OCA_ARG_SIZE]

			if size < 0:
				# Don't handle error cases
				return
			
			if data[OCA_ARG_PID] == self.server_pid:
				if not self.server_bytes_read.has_key(read_id):
					self.server_bytes_read[read_id] = 0
				self.server_bytes_read[read_id] += size
					
				if self.server_socks.has_key(read_id):
					self.comp_read_bytes_val += size
					self.comp_read_count_val += 1
					#self.pending_server_work[read_id] -= size

				self.all_read_bytes_val += size
				self.all_read_count_val += 1
			else:
				if not self.other_bytes_read.has_key(read_id):
					self.other_bytes_read[read_id] = 0
				self.other_bytes_read[read_id] += size

		elif data[OCA_TYPE] == OCA_WRITE \
		or data[OCA_TYPE] == OCA_WRITEV \
	  	or data[OCA_TYPE] == OCA_SOCKET_SEND_TO \
		or data[OCA_TYPE] == OCA_SOCKET_SEND_MSG:

			write_id = data[OCA_ARG_PC_ID]
			size = data[OCA_ARG_SIZE]

			if size < 0:
				# Don't handle error cases
				return
			
			if data[OCA_ARG_PID] == self.server_pid:
				if not self.server_bytes_wrote.has_key(write_id):
					self.server_bytes_wrote[write_id] = 0
				self.server_bytes_wrote[write_id] += size	

				#self.all_wrote_bytes_val += size
				#self.all_wrote_count_val += 1
			else:
				if not self.other_bytes_wrote.has_key(write_id):
					self.other_bytes_wrote[write_id] = 0

				self.other_bytes_wrote[write_id] += size

				if self.client_socks.has_key(write_id):
					self.comp_sent_bytes_val += size
					#self.pending_server_work[self.client_socks[write_id]] += size

		elif data[OCA_TYPE] == OCA_SOCKET_ADD:
			if data[OCA_ARG_EXEC_NAME] == self.server_name:
				self.server_pid = data[OCA_ARG_PID]
				self.start_time = log_time[self.units].get_value()
				self.comp_sent_bytes_values.append(0)

		if not self.consume:
			self.send_output("default", entity)
	
	def finalize(self):

		print >> self.outfile, "Known socket connections\n"
		for (server, client) in self.server_socks.items():
			print >> self.outfile, "Server: (%s, %d) Client (%s, %d)" \
				% (server[0], server[1], client[0], client[1])

		total_server_read  = self.sum_dict(self.server_bytes_read)
		total_server_wrote = self.sum_dict(self.server_bytes_wrote)
		comp_server_read   = self.sum_dict(self.server_bytes_read, self.server_socks)
		comp_server_wrote  = self.sum_dict(self.server_bytes_wrote, self.server_socks)
		comp_client_read   = self.sum_dict(self.other_bytes_read, self.client_socks)
		comp_client_wrote  = self.sum_dict(self.other_bytes_wrote, self.client_socks)

		comp_read_bytes_histo = self.get_hist(self.comp_read_bytes_histo, \
							self.comp_read_bytes_values, \
				       			self.comp_read_bytes_buckets)
		comp_read_count_histo = self.get_hist(self.comp_read_count_histo, \
							self.comp_read_count_values,\
							self.comp_read_count_buckets)
		comp_sent_bytes_histo = self.get_hist(self.comp_sent_bytes_histo, \
							self.comp_sent_bytes_values, \
							self.comp_sent_bytes_buckets)
		all_read_bytes_histo = self.get_hist(self.all_read_bytes_histo, \
							self.all_read_bytes_values,\
				       			self.all_read_bytes_buckets)
		all_read_count_histo = self.get_hist(self.all_read_count_histo, \
							self.all_read_count_values, \
				       			self.all_read_count_buckets)
		
		if comp_read_bytes_histo:
			self.send_output("default", comp_read_bytes_histo)
		if comp_read_count_histo:
			self.send_output("default", comp_read_count_histo)
		if comp_sent_bytes_histo:
			self.send_output("default", comp_sent_bytes_histo)
		if all_read_bytes_histo:
			self.send_output("default", all_read_bytes_histo)
		if all_read_count_histo:
			self.send_output("default", all_read_count_histo)

		comp_read_pct = 100 * float(comp_server_read) / total_server_read
		comp_wrote_pct = 100 * float(comp_server_wrote) / total_server_wrote
		
		print >> self.outfile, self.stats_title
		print >> self.outfile, "\nComp sent to server:\t%d" % comp_client_wrote
		print >> self.outfile, "Comp server read:\t%d" % comp_server_read
		print >> self.outfile, "Total server read:\t%d" % total_server_read
		print >> self.outfile, "Server read comp pct:\t%.2f" % comp_read_pct

		print >> self.outfile, "Comp server wrote:\t%d" % comp_server_wrote
		print >> self.outfile, "Comp read from server:\t%d" % comp_client_read
		print >> self.outfile, "Total server wrote:\t%d" % total_server_wrote
		print >> self.outfile, "Server wrote comp pct:\t%.2f" % comp_wrote_pct

		#
		# Server was on CPU when DSKI shut down
		#
		if self.start_time != None:
			self.comp_sent_bytes_val = 0
			self.total_execs += 1
			self.total_vals += 1
			
			self.comp_read_bytes_values.append(self.comp_read_bytes_val)
			self.comp_read_count_values.append(self.comp_read_count_val)
			self.all_read_bytes_values.append(self.all_read_bytes_val)
			self.all_read_count_values.append(self.all_read_count_val)	

			self.start_time = None

		unread_bytes = []
		read_all_vals = 0
		if self.comp_read_bytes_values and self.comp_sent_bytes_values:
			if len(self.comp_read_bytes_values) != \
      				len(self.comp_sent_bytes_values):
				print "ERROR: Number of intervals between server", \
					" executions is not equal to the number of", \
					" server execution intervals"

			for i in range(len(self.comp_read_bytes_values)):
				val = self.comp_sent_bytes_values[i] \
					- self.comp_read_bytes_values[i]
				unread_bytes.append(val)
				if val == 0:
					read_all_vals += 1

		unread_bytes_histo = self.get_hist(self.unread_bytes_histo, \
							unread_bytes, \
				       			self.unread_bytes_buckets)

		read_all_pct = 100 * float(read_all_vals) / total_server_read
		print >> self.outfile, "Read all pct:\t\t%.2f" % read_all_pct
	
	def sum_dict(self, dict_to_sum, restrict_dict=None):
		sum = 0
		for sock in dict_to_sum.iterkeys():
			if not restrict_dict:
				sum += dict_to_sum[sock]
			else:
				if sock in restrict_dict.iterkeys():
					sum += dict_to_sum[sock]	
		return sum

	def get_hist(self, hist_ptr, values, buckets): 
		if not values or not hist_ptr:
			return None

		mn = min(values)
		mx = max(values)
		# add a bit of extra headroom so max value doesn't get
		# marked as overflow
		bsize = (float(mx) - float(mn)) / buckets
		mx = mx + (bsize / 100)

		hist = entities.Histogram(hist_ptr.get_cid(), None, \
			    mn, mx, buckets)

		for i in values:
			hist.add_value(i)
	
		return hist	


class syscall_info(filtering.Filter):
		
	expected_parameters = {
		"filename" : {
			"types" : "string",
			"doc" : "Filename to dump stats into",
			"default" : "-",
		},
	}

	def initialize(self):
		self.OCA_ptr = self.get_ns_pointer("OCA/ACTIONS")	
		self.procs = {}
		self.syscalls = {}

		if self.params["filename"] == "-":
			self.outfile = sys.stdout
		else:
			self.outfile = open(self.params["filename"], "w")

	def process(self, entity):

		if self.OCA_ptr.get_cid() == entity.get_cid():
			data = entity.get_extra_data()

			if data[OCA_TYPE] == OCA_SYSCALL:
				syscall = data[OCA_ARG_SYSCALL] 
				pid = data[OCA_ARG_PID]
			
				if not self.procs.has_key(pid):
					self.procs[pid] = {}
					self.procs[pid][OCA_ARG_EXEC_NAME] = \
							data[OCA_ARG_EXEC_NAME]
					self.procs[pid]["Num_Uses"] = {}

				if not self.syscalls.has_key(syscall):
					self.syscalls[syscall] = 1
				else:
					self.syscalls[syscall] += 1

				if not self.procs[pid]["Num_Uses"].has_key(syscall):
					self.procs[pid]["Num_Uses"][syscall] = 1
				else:
					self.procs[pid]["Num_Uses"][syscall] += 1
			elif data[OCA_TYPE] == OCA_EXEC:
				pid = data[OCA_ARG_PID]
				self.procs[pid][OCA_ARG_EXEC_NAME] = \
					data[OCA_ARG_EXEC_NAME]
			else:
				self.send_output("default", entity)
				return

	def finalize(self):

		print >> self.outfile, "System Call Report\n"
		print >> self.outfile, "System Call Used:\t\t\t# of Uses:"
		
		for (sc, uses) in self.syscalls.items():
			name = syscall.systab[sc][0]
			if len(name) < 8:
				tabs = '\t\t\t\t\t'
			elif len(name) < 16:
				tabs = '\t\t\t\t'
			elif len(name) < 24:
				tabs = '\t\t\t'
			elif len(name) < 32:
				tabs = '\t\t'
			else:
				tabs = '\t'

			print >> self.outfile, "%s%s%d" % (name, tabs, uses)

		for (pid, sc_data) in self.procs.items():
			print >> self.outfile, "\nInfo for T%d execing %s" % \
				(pid, sc_data[OCA_ARG_EXEC_NAME])
			print >> self.outfile, "System Call Used:\t\t# of Uses:"
			for (sc, uses) in sc_data["Num_Uses"].items():
				name = syscall.systab[sc][0]
				if len(name) < 8:
					tabs = '\t\t\t\t\t'
				elif len(name) < 16:
					tabs = '\t\t\t\t'
				elif len(name) < 24:
					tabs = '\t\t\t'
				elif len(name) < 32:
					tabs = '\t\t'
				else:
					tabs = '\t'

				print >> self.outfile, "%s%s%d" % (name, tabs, uses)


class print_OCA_stream(filtering.Filter):
	""" 
	This filter prints OCA event dictionaries in a nice format
	as they are received
	"""
	expected_parameters = {
		"outfile" : {
			"types"   : "string",
			"doc"     : "File to output printed information to.",
			"default" : "-",
		},
	}

	def initialize(self):

		self.OCA_actions_ptr = self.get_ns_pointer("OCA/ACTIONS")	
		if self.params["outfile"] == "-":
			self.outfile = sys.stdout
		else:
			self.outfile = open(self.params["outfile"], "w")
			
	def process(self,entity):
		
		if entity.get_cid() == self.OCA_actions_ptr.get_cid():
			dict = entity.get_extra_data()
			print >> self.outfile, dict[OCA_TYPE]
			for key in dict.iterkeys():
				if key is not OCA_TYPE:
					print >> self.outfile, "\t",key,"\t",
					if len(key) < 15:
						print >> self.outfile, "\t",
					if len(key) < 7:
						print >> self.outfile, "\t",
					print >> self.outfile, dict[key]
			print >> self.outfile, ""

		self.send_output("default", entity)

class switch_from_histo(filtering.Filter):
	""" 
	This filter creates time histograms from OCA events.
	"""
	expected_parameters = {
		"process_name" : {
			"types" : "string",
			"doc" : "Process name to make a time_slice_histogram for",
			"required" : True,
		},
		"xticks" : {
			"types" : "integer",
			"doc" : "number of tick marks on x-axis",
			"default" : 10,
		},
		"outfile" : {
			"types" : "string",
			"doc" : "base filename to print to",
		},
		"consume" : {
			"types" : "boolean",
			"doc" : "Whether to delete matching entities after processing",
			"default" : False,
		},
	}

	def initialize(self):
		"""
		Initialize
		"""
		
		self.OCA_actions_ptr = self.get_ns_pointer("OCA/ACTIONS")	
		self.consume = self.params["consume"]
		self.process_name = self.params["process_name"]

		self.OCA_actions = [
			OCA_SWITCH_FROM
		]

		self.ss_dict = {}
		self.total_swaps = 0
		
		if self.params["outfile"] == "-":
			self.outfile = sys.stdout
		else:
			self.outfile = open(self.params["outfile"], "w")

	def process(self,entity):	
		"""
		Process
		"""

		match = False
		data = entity.get_extra_data()
	
		if not entity.get_cid() == self.OCA_actions_ptr.get_cid():
			self.send_output("default", entity)
			return	

		if not data.has_key(OCA_TYPE):
			raise Exception("switch_state_histogram: OCA action without an OCA type")

		if data[OCA_TYPE] in self.OCA_actions:
			if data[OCA_ARG_EXEC_NAME] == self.process_name:
				if self.ss_dict.has_key(data[OCA_ARG_SWITCH_STATE]):
					self.ss_dict[data[OCA_ARG_SWITCH_STATE]] += 1
				else:
					self.ss_dict[data[OCA_ARG_SWITCH_STATE]] = 1

				self.total_swaps += 1
				match = True

		if not match or (match and not self.consume):
			self.send_output("default", entity)
			return
		
	def finalize(self):
		"""
		finalize
		"""

		print >> self.outfile, "Switch state info for %s:\n" % self.process_name	
		print >> self.outfile, "Total swap outs:\t%d" % self.total_swaps
		#print >> self.outfile, self.ss_dict

		print >> self.outfile, "Switch State Histogram:"
		print >> self.outfile, "STATE:\t\t\tOCC:\t\tPCT:"
		for state in self.ss_dict.keys():
			occ = self.ss_dict[state]
			pct = float(occ) / self.total_swaps
			if len(state) < 15: 
				print >> self.outfile, "%s\t\t%d\t\t%f" % (state, occ, pct)
			else:
				print >> self.outfile, "%s\t%d\t\t%2.2f" % (state, occ, pct)

# XXX: Shouldn't this be in discovery_pre_process.py ???
#
class OCA_Conversion(filtering.Filter):

	"""This filter expects that the OCA event is included in the current
	namespace. You must include this in your post-processing configuration
	file. This OCA Datastream Event is Family=DSCVR, Name=OCA"""

	def initialize(self):
		# oca event which will be synthesized by this filter
		self.oca_event = self.get_ns_pointer("DSCVR/OCA")

		# events which this filter knows how to turn into OCAs
		self.mutex_unlock = self.get_ns_pointer("SCHED_PROXY/UNLOCK_MUTEX")
		self.mutex_block = self.get_ns_pointer("SCHED_PROXY/BLOCK_ON_MUTEX")
		self.mutex_steal = self.get_ns_pointer("SCHED_PROXY/STEAL_MUTEX")
		self.mutex_proxy_lock = self.get_ns_pointer("SCHED_PROXY/MUTEX_PROXY_LOCKED")
		self.mutex_proxy_unlock = self.get_ns_pointer("SCHED_PROXY/MUTEX_PROXY_UNLOCK")
		self.mutex_lock = self.get_ns_pointer("SCHED_PROXY/LOCK_MUTEX")

	def process(self, entity):
		cid = entity.get_cid()
		ed = entity.get_extra_data()

		# Each OCA_TYPE in the switch statement must define __oca_type
		# The __oca_args is an optional dictionary containing the
		# arguments specific to the OCA_TYPE. If no arguments are
		# associated with an OCA_TYPE __oca_args should be set to its
		# default value, an empty dictionary: {}
		#
		__oca_type = None
		__oca_args = {}

		# Match the current entity with an event for which this filter
		# can construct an associated OCA Event
		#
		if cid == self.mutex_unlock.get_cid():
			__oca_type = OCA_MUTEX_UNLOCK
			__oca_args = {
				OCA_ARG_CURRENT_PID : ed['current_pid'],
				OCA_ARG_PENDOWNER_PID : ed['pendowner_pid'],
				OCA_ARG_LOCK_ADDRESS : ed['lock_addr'],
			}
		elif cid == self.mutex_block.get_cid():
			__oca_type = OCA_MUTEX_BLOCK
			__oca_args = {
				OCA_ARG_CURRENT_PID : ed['current_pid'],
				OCA_ARG_LOCK_ADDRESS : ed['lock_addr'],
			}
		elif cid == self.mutex_steal.get_cid():
			__oca_type = OCA_MUTEX_STEAL
			__oca_args = {
				OCA_ARG_CURRENT_PID : ed['current_pid'],
				OCA_ARG_PENDOWNER_PID : ed['pendowner_pid'],
				OCA_ARG_LOCK_ADDRESS : ed['lock_addr'],
			}
		elif cid == self.mutex_lock.get_cid():
			__oca_type = OCA_MUTEX_LOCK
			__oca_args = {
				OCA_ARG_CURRENT_PID : ed['current_pid'],
				OCA_ARG_LOCK_ADDRESS : ed['lock_addr'],
			}
		elif cid == self.mutex_proxy_lock.get_cid():
			__oca_type = OCA_MUTEX_PROXY_LOCK
			__oca_args = {
				OCA_ARG_CURRENT_PID : ed['current_pid'],
				OCA_ARG_OWNER_PID : ed['owner_pid'],
				OCA_ARG_LOCK_ADDRESS : ed['lock_addr'],
			}
		elif cid == self.mutex_proxy_unlock.get_cid():
			__oca_type = OCA_MUTEX_PROXY_UNLOCK
			__oca_args = {
				OCA_ARG_CURRENT_PID : ed['current_pid'],
				OCA_ARG_OWNER_PID : ed['owner_pid'],
				OCA_ARG_LOCK_ADDRESS : ed['lock_addr'],
			}

		else:
			self.send(entity)
			return

		if not __oca_type:
			raise Exception

		oca_record = {OCA_TYPE : __oca_type}
		oca_record.update(__oca_args)
		new_oca_event = entities.Event(self.oca_event.get_cid(),
				entity.get_log_time(), entity.get_tag(), oca_record)
		self.send(new_oca_event)



# The following needs to be revisited at some point in the future
# In it's current form, it's not very useful.

class dscvr_info(filtering.Filter):

	"""
	expected_parameters = {
		"consume" : {
			"types" : "boolean",
			"doc" : "Whether to delete matching entities after processing",
			"default" : False
		},
	}

	def initialize(self):

		self.init_evt = self.get_ns_pointer("DSCVR/INIT")
		self.fork_evt = self.get_ns_pointer("DSCVR/FORK")
		self.signal_evt = self.get_ns_pointer("DSCVR/SIGNAL")
		self.shmget_evt = self.get_ns_pointer("DSCVR/SHMGET")
		self.shmat_evt = self.get_ns_pointer("DSCVR/SHMAT")
		self.ext_dat_evt = self.get_ns_pointer("DSCVR/EXT_DAT")
		self.setlkw_evt = self.get_ns_pointer("DSCVR/SETLKW")
		self.consume = self.params["consume"]

	def process(self, entity):

		match = False
		data = {}

		if entity.get_cid() == self.init_evt.get_cid():
			match = True
			print "The initial process in the group is: ", entity.get_tag()
			print ''

		if entity.get_cid() == self.fork_evt.get_cid():
			match = True
			data = entity.get_extra_data()
			print "Got dscvr fork event: "
			print "Group: ", data["group"]
			print "Parent task: ", data["parent_task"]
			print "Added task: ", data["added_task"]
			#print "ID: ", data["id"]
			print ''

		elif entity.get_cid() == self.signal_evt.get_cid():
			match = True
			data = entity.get_extra_data()
			print "Got dscvr signal event: "
			print "Group: ", data["group"]
			print "Signal sent by: ", data["parent_task"]
			print "Added task: ", data["added_task"]
			#print "ID: ", data["id"]
			print ''

		elif entity.get_cid() == self.shmget_evt.get_cid():
			match = True
			data = entity.get_extra_data()
			print "Got dscvr shmget event: "
			print "Group: ", data["group"]
			print "Current task: ", data["parent_task"]
			print "Added SHMID: ", data["id"]
			print ''

		elif entity.get_cid() == self.shmat_evt.get_cid():
			match = True
			data = entity.get_extra_data()
			print "Got dscvr shmat event: "
			print "Group: ", data["group"]
			#print "Parent task: ", data["parent_task"]
			print "Attached to SHMID: ", data["id"]
			print "Added task: ", data["added_task"]
			print ''
                 
		elif entity.get_cid() == self.ext_dat_evt.get_cid():
			match =True
			data = entity.get_extra_data()

			#print data["group"]
			print  "Task", data["parent_task"]," was added to the group", data["group"], "because it called ext_dat on a named pipe inode id ", data["added_task"]
			print "Task ", data["added_task"], "was added to the group", data["group"], "because it called ext_dat on a named pipe with id ", data["id"]

			print ''
			#print "got dscvr named pipe event: "
			#print "Group: ",data["group"]
			#print "Group: ", data["group"]
			#print "Added task: ", data["added_task"]
			#print "Parent task: ", data["parent_task"]
			#print "ID: ", data["id"]
		
    		elif entity.get_cid() == self.setlkw_evt.get_cid():
                        match =True
                        data = entity.get_extra_data()
                        print "Task ", data["parent_task"], "was added to the group", data["group"], "because it called setlkw on a file with inode id ", data["added_task"]

                        print "Task ", data["added_task"], "was added to the group", data["group"], "because it called setlkw on a file with id ", data["id"]

                        print ''
                        #print "got dscvr file locking event: "
                        #print "Group: ",data["group"]
                        #print "Group: ", data["group"]
                        #print "Added task: ", data["added_task"]
                        #print "Parent task: ", data["parent_task"]
                        #print "ID: ", data["id"] 

		if not match or (match and not self.consume):
			self.send_output("default", entity)
	"""
	pass

class one_page(filtering.Filter):

	"""
	expected_parameters = {
		"Parent_pid" : {
			"types" : "integer",
			"doc" : "pid of the parent process",
			"default" : ""
		}
		
	}

	def initialize(self):
		# This is logged in the do_fork() within kernel/fork.c when the process or a thread has forked off a thread
		self.fork_ptr = self.get_ns_pointer("FORK/DO_FORK")
		# This is logged in the fifo_open() within the fs/fifo.c when the process or a thread has opened a named pipe
		self.namepipe_ptr = self.get_ns_pointer("FIFO_CREATION/FIFO")
		# This is logged in the do_fcntl() within fs/fcntl.c when the process or a thread has locked a file
		self.filelock_ptr = self.get_ns_pointer("FILELOCK/LOCK")
		# This is logged in the send_signal() within the kernel/signal.c when the process or a thread has sent a signal
		self.signal_ptr = self.get_ns_pointer("SIGNAL/SEND_SIGNAL")
		# This is logged in the DO_PIPE() within fs/pipe.c when the process or a thread has opened a pipe for reading or writing
		self.pipe_read_ptr = self.get_ns_pointer("DSCVR/PIPE_OPEN_READ_FD")
		# This is logged in the do_shmat() within ipc/shm.c when the process or a thread has attached to a shared memory
		self.shmem_ptr = self.get_ns_pointer("SHMEM/SHMAT")

		

		self.Threads = []
		self.Threads.append(self.params["Parent_pid"])

		self.signals_parent =0
		self.signals_child =0

		self.is_fork = False
		self.is_namepipe = False
		self.is_signals = False
		self.is_filelock = False
		self.is_pipe = False
		self.is_shmem = False

		
		
	def process(self,entity):

		if entity.get_cid() == self.fork_ptr.get_cid():
			self.i = 0;
			self.j = 0;
			self.is_fork = True
			if len(self.Threads) > 0:
				for pid in self.Threads:
					if entity.get_tag() != pid:
						self.i = self.i+1
					elif entity.get_pid() != pid:
						self.j = self.j+1
				if self.i == len(self.Threads): 		
					self.Threads.append(entity.get_tag())
				if self.j == len(self.Threads):
					self.Threads.append(entity.get_pid())
		
		elif entity.get_cid() == self.namepipe_ptr.get_cid():
			self.is_namepipe = True
			
		elif entity.get_cid() == self.filelock_ptr.get_cid():
			self.is_filelock = True
			
		elif entity.get_cid() == self.signal_ptr.get_cid():
						
			if len(self.Threads) > 0:
				for pid in self.Threads:
					if entity.get_tag() == pid:
						self.signals_child = self.signals_child+1
					
					if entity.get_pid() == pid:
						self.signals_parent = self.signals_parent+1
				
		elif entity.get_cid() == self.shmem_ptr.get_cid():
			self.is_shmem = True
			
		elif entity.get_cid() == self.pipe_read_ptr.get_cid():
			self.is_pipe = True
		
			
	def finalize(self):


		print "     " 
		print "     "
		print "Tests Run : Result"
		print "     "
	
		if self.is_fork:
		 	print "Fork : yes"
						
		else: 
			print "Fork : No" 
		
		if self.is_namepipe:
		 	print "Namepipe : yes"
		else:
			print "Namepipe : No" 
	
		if self.is_filelock:
		 	print "File-locking  : yes"
		else:
			print "File-locking : No" 

		if  self.signals_child > 0 or self.signals_parent > 0:
			
		 	print "Signals : yes"
		else:
			print "Signals : No" 

		if self.is_shmem:
		 	print "Shared Memory : yes"
		else:
			print "Shared Memory : No" 

		if self.is_pipe:
		 	print "Pipes : yes"
		else:
			print "Pipes : No" 

		print "   "
	"""
	pass


		
# This filter is used for processing information from the raw logging file and converting them into a format 
# that could be understood by the networkX filter, so that we could get a 'N' page summary 

class N_page(filtering.Filter):
	"""
	def initialize(self):

		# This ptr holds the namespace pointer of "DSCVR/INIT" DSUI Event. We use this 
		# instrumentation point to pass the pid of the traced cmd by the traceme tool 

		self.root_thread_ptr = self.get_ns_pointer("DSCVR/INIT")

		# This ptr holds the namespace pointer of "FORK/DO_FORK" DSKI Event. We use this 
		# instrumentation point to pass the pid of the child process forked by the traced_cmd 

		self.fork_ptr = self.get_ns_pointer("FORK/DO_FORK")

		# This ptr holds the namespace pointer of "SIGNAL/SEND_SIGNAL" DSKI Event. we use this 
		# instrumentation point to get to know about the pid of the receiver thread to which the 
		# sender thread is sending the signal and also to get the signal number that is being sent

		self.signal_ptr = self.get_ns_pointer("SIGNAL/SEND_SIGNAL")
		
		# We use these three instrumentation point to get the pid of the dsui threads forked off 
		# by the traced cmd

		self.dsui_signal_thread_ptr = self.get_ns_pointer("DSCVR/DSUI_SIGNAL_THREAD")
		self.dsui_logging_thread_ptr = self.get_ns_pointer("DSCVR/DSUI_LOGGING_THREAD")
		self.dsui_buffer_thread_ptr = self.get_ns_pointer("DSCVR/DSUI_BUFFER_THREAD")

		# This List holds the pids of all the dsui threads being forked off as part of the 
		# traced cmd

		self.dsui_threads = []
		
		# This List holds the pids of all the threads forked off by the traced_cmd and also the 
		# pid of the traced_cmd as well
		
		self.Threads = []

		# This List holds all the signal actions that had took place within the traced_cmd process,
		# Each action in this list is represented by a list that has these information within them, 
		# sender_pid, Receiver_pid and signal number

		self.signal_action_list = []

		# This List holds all the fork actions that had took place within the traced_cmd process,
		# Each action in this list is represented by a list that has these information within them,
		# Parent_pid, Child_pid 

		self.fork_action_list = []

		# This holds the object of the class naming_subsytem()
		
		self.naming_subsystem_object = naming_subsystem()

	def process(self,entity):
		
		# i check here whether the entity is of type root thread ptr if yes then i add the pid of 
		# the root thread to my threads list, i get the pid of the root thread as a tag attached 
		# to the root thread instrumentation point within the traceme tool

		if entity.get_cid() == self.root_thread_ptr.get_cid():
			self.Threads.append(entity.get_tag())
		
		# I check here whether the entity is a fork action if yes then i add the pid of the child 
		# to the threads list and then i create a temporary list that will hold the parent_pid and 
		# the child_pid, after populating this list i add this temporary list to the fork_action_list

		if entity.get_cid() == self.fork_ptr.get_cid():
			self.Threads.append(entity.get_tag())
			forklist=[]
			parent_pid = entity.get_pid()
			child_pid = entity.get_tag()
			forklist.append(parent_pid)
			forklist.append(child_pid)
			self.fork_action_list.append(forklist)

		# I check here whether the entity is a signal action if yes then i check whether the signal
		# is sent by the threads that we care about if yes then i create a temporary list that will
		# hold the sender_pid, the receiver_pid and also the signal number,
		# after populating this list i add this temporary list to the signal_action_list
			
		if entity.get_cid() == self.signal_ptr.get_cid():
			siglist = []
			for pid in self.Threads:
				if entity.get_pid() == pid:
					signal_num = entity.get_extra_data()
					receiver_pid = entity.get_tag()
					sender_pid = entity.get_pid()
					siglist.append(sender_pid)
					siglist.append(receiver_pid)		
					siglist.append(signal_num)
					self.signal_action_list.append(siglist)

		# These checks are for identifying the dsui threads forked off by the traced cmd

		if entity.get_cid() ==  self.dsui_signal_thread_ptr.get_cid():
			self.dsui_threads.append(entity.get_tag());

		if entity.get_cid() ==  self.dsui_logging_thread_ptr.get_cid():
		        self.dsui_threads.append(entity.get_tag());

		if entity.get_cid() ==  self.dsui_buffer_thread_ptr.get_cid():
		        self.dsui_threads.append(entity.get_tag());

			
	def finalize(self):
		
		print "\nNumber of Threads : ", len(self.Threads)
		print "\nNumber of DSUI Threads : ",len(self.dsui_threads)
		print "\nfork actions : ",len(self.fork_action_list)
		print "\nsignal actions : ", len(self.signal_action_list)

		# I call the create_mapping function defined in the naming subsystem by passing the threads
		# list which holds the pids of all the threads forked off by the traced_cmd and also the dsui 
		# threads list which represents the list of pids that DSUI forks, this function 
		# maps the pids to their respective names

		self.naming_subsystem_object.create_mapping(self.Threads,self.dsui_threads)

		# This call just prints the mapped names and their pids

		self.naming_subsystem_object.printing_dictionaries()

		print "\nFork actions List before mapping the pids to their corresponding thread names:"
		for list in self.fork_action_list:
		      print list
		print "\nSignal actions List before mapping the pids to their corresponding thread names:"
		for list in self.signal_action_list:
		      print list
	
		# This call replaces the pids in the fork_action_list to their thread names

		self.fork_action_list=self.naming_subsystem_object.mapping_pids_to_Thread_names_in_action_lists(self.fork_action_list)

		# This call replaces the pids in the signal_action_list to their thread names

		self.signal_action_list=self.naming_subsystem_object.mapping_pids_to_Thread_names_in_action_lists(self.signal_action_list)

		print "\nFork actions List :"
		for list in self.fork_action_list:
			print list
		print "\nSignal actions List :"	
		for list in self.signal_action_list:
			print list
		
		print "finished"		
	"""
	pass

# This class is defined to take care the job of naming the threads that are being forked off by the traced_cmd 
# we map pids to thread names, such as 1234 : 'T1' and also we map thread names to pids say 'T1' : 1234
# we also do the job of mapping pids to thread names in the action lists that we pass to a function in this class

class naming_subsystem:

	"""
	def __init__(self):
		We are initializing the two dictionaries that we are going to use in our naming subsystem,
		one for mapping pids to name and the other for mapping names to pids

		self.pid_to_name = {}
		self.name_to_pid = {}
		
	def create_mapping(self,threads,dsui_threads):
		This function maps the pids that we get in a list to their thread names in one dictionary 
		and also does maps the thread names to its pids in a different dictionary

		i = 0 
		for pid in threads:

			i=i+1
		# creating the name to be given to the thread pid

		        self.thread_name = "T"+str(i)
		# Checking whether the pid forked off by the traced cmd is the same as one of the dsui 
		# threads if so then replace the name given to them in the above line with the name as given below

			if dsui_threads[0] == pid:
				self.thread_name = "DSUI_T1"
			if dsui_threads[1] == pid:
				self.thread_name = "DSUI_T2"
			if dsui_threads[2] == pid:
				self.thread_name = "DSUI_T3"
				
		# map the pid to the thread name generated
			self.pid_to_name[pid] = self.thread_name
		# map the thread name to the pid in another dictionary
			self.name_to_pid[self.thread_name] = pid

	def get_name_to_pid(self,name):
		This returns the pid of the thread, when we specify the name of the thread as argument,
		example we send in 'T1' as argument and we get the pid of associated with that thread name

		return self.name_to_pid[name]

	def get_pid_to_name(self,pid):
		This returns the name given to the thread, when we specify the pid of the thread as argument,
		example we send in 1234 as argument and we get the thread name associated with that pid

		return self.pid_to_name[pid]	

	def printing_dictionaries(self):
		This is just a utility function that displays the two dictionaries that we created in our naming subsystem

		print " "
		print "Pids to name dictionary content :",self.pid_to_name
		print " "	
		print "Name to Pid dictionary content :",self.name_to_pid

	def mapping_pids_to_Thread_names_in_action_lists(self,action_list):
		We map the pids in the action lists that are generated to their corresponding thread names

		for list in action_list:
			parent_pid_in_list = list[0]
			child_pid_in_list = list[1]
			parent_name = self.get_pid_to_name(parent_pid_in_list)
			child_name = self.get_pid_to_name(child_pid_in_list)
			list[0] = parent_name
			list[1] = child_name
	
		return action_list
	"""
	pass

