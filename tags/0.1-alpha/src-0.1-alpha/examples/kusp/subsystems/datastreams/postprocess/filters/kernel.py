from datastreams.postprocess import filtering, entities
from datastreams import namespaces


class address(filtering.Filter):
	"""This filtering fills in missing source and destination addresses
	by using the TCP sequence number to get the data from other
	entities."""

	def initialize(self):
		self.seqdict = {}

	def process(self, entity):
		if entity.get_type() != namespaces.EVENTTYPE:
			self.send(entity)
			return
		
		seqdict = self.seqdict

		if entity.get_edf_name() == "print_netdata":
			netdata = entity.get_extra_data()
			if not netdata:
				return 
			if netdata["daddr"] == '0.0.0.0' or netdata["saddr"] ==	'0.0.0.0':
				if netdata["sequence"] in seqdict:
					saddr, daddr = seqdict[netdata["sequence"]]
					netdata["daddr"] = daddr
					netdata["saddr"] = saddr
			elif netdata["sequence"] not in seqdict:
				seqdict[netdata["sequence"]] = (
						netdata["saddr"], 
						netdata["daddr"])
		self.send(entity)
		

class port(filtering.Filter):
	"""
	This filtering examines the source and destination port of all
	events that log netdata, and removes any that don't match

	events which don't have netdata are passed through unmodified
	"""
	expected_parameters = {
		"sports":{
			"types":"list",
			"doc":"List of source ports we are interested in",     
			"listdef" : {"types":"integer",
				     "doc":"Network port"
			}
		},

		"dports":{
			"types":"list",
			"doc":"List of destination ports we are interested in",     
			"listdef" : {"types":"integer",
				     "doc":"Network port"
			}
		},
	}

	def initialize(self):
		self.sports = self.params["sports"]
		self.dports = self.params["dports"]

	def process(self, entity):
		if (entity.get_type() == namespaces.EVENTTYPE and
			entity.get_edf_name() in ["print_ip_netdata", "print_netdata"]):
			netdata = entity.get_extra_data()
			if not netdata:
				return

			if netdata["dport"] in self.dports:
				self.send(entity)
				return
				
			if netdata["sport"] in self.sports:
				self.send(entity)
				return
			return
		self.send(entity)

class xmit_interval(filtering.Filter):

	expected_parameters = {
		"start_machine" : {
			"types" : "string",
		},
		"end_machine" : {
			"types" : "string",
		},
	}

	builtin_namespace = {
		"NETWORK_DRIVER_FAM" : {
			"entities" : {
				"INTERVAL_XMIT" : ("interval", {
					"desc" : "Time between matching TX and RX events"
				})
			}
		}
	}

	def initialize(self):
		self.rxevt = self.get_ns_pointer("NETWORK_DRIVER_FAM/EVENT_E100_RX")
		self.txevt = self.get_ns_pointer("NETWORK_DRIVER_FAM/EVENT_E100_TX")
		self.intptr = self.get_ns_pointer("NETWORK_DRIVER_FAM/INTERVAL_XMIT")

		self.checktime = {}
		self.seqdict = {}

	def process(self, entity):
		self.send(entity)

	#	print entity.get_cid(), self.txevt.get_cid(), entity.get_machine()
		
		if (entity.get_cid() == self.txevt.get_cid() and 
				entity.get_machine() == self.params["start_machine"]):
			ed = entity.get_extra_data()
			seqno = (ed["sequence"], ed["ip_id"],ed["daddr"])
			txtime = entity.get_log_time()

			if seqno in self.checktime:
				rxtime = self.checktime[seqno]
				i = entities.Interval(self.intptr.get_cid(),
						txtime, rxtime, seqno)
				if i.get_duration("ns") < 0 :
					print "OMG! We have timetravel: "+`seqno`+" traveled in "+`i.get_duration("ns")`+" ns"
				del self.checktime[seqno]
		
				self.send(i)
			self.seqdict[seqno] = txtime
		elif (entity.get_cid() == self.rxevt.get_cid() and 
				entity.get_machine() == self.params["end_machine"]):
			rxtime = entity.get_log_time()
			ed = entity.get_extra_data()
			seqno = (ed["sequence"], ed["ip_id"],ed["daddr"])

			if seqno not in self.seqdict:
				self.checktime[seqno] = rxtime
				return
			txtime = self.seqdict[seqno]
			del self.seqdict[seqno]
			i = entities.Interval(self.intptr.get_cid(),
					txtime, rxtime, seqno)
			self.send(i)




