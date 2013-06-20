import array
import math
from datastreams import namespaces

def get_tsc_measurement(tsc, machine):
	return {"tsc":TimeMeasurement("tsc", tsc, machine, 0, 0)}

def get_zero_timedict():
	return {"tsc":TimeMeasurement("tsc", 0, "generated", 0, 0),
		"sequence":TimeMeasurement("sequence", 0, "generated", 0, 0),
		"ns":TimeMeasurement("ns", 0, "global", 0, 0)}



class TimeMeasurement:
	"""represents a specific time measurement"""
	def __init__(self, units, value, clocksource, low_err, high_err):
		self.value = value
		self.units = units
		self.clocksource = clocksource
		self.low_err = low_err
		self.high_err = high_err

	def __repr__(self):
		return "<"+self.clocksource+":"+self.units+":"+`self.value`+">"
	def get_units(self):
		return self.units

	def get_value(self):
		return self.value

	def get_clocksource(self):
		return self.clocksource

	def get_low_err(self):
		return self.low_err

	def get_high_err(self):
		return self.high_err

	def get_envelope(self):
		return (self.value + self.low_err, 
				self.value + self.high_err)

PIPELINE_ERROR = 1
PIPELINE_EOF = 2

# FIXME: just make these admin events

class PipelineItem:
	message = 0
	namespace = None
	pass

class PipelineError(PipelineItem):
	message = PIPELINE_ERROR
	pass

class PipelineEnd(PipelineItem):
	message = PIPELINE_EOF
	pass


class Entity(PipelineItem):
	def __init__(self, cid, logtime_dict, pid=0):
		if (cid == -1):
			raise Exception("Bad -1 cid, cannot create entity")

		if type(cid) is not long:
			cid = long(cid)
			#raise Exception("cid must be long")
		self.cid = cid
		self.pid = pid
		if logtime_dict:
			self.time = {"log":logtime_dict}
		else:
			self.time = {"log": get_zero_timedict()}
		
		self.namespace = None

	def __repr__(self):
		if not self.namespace:
			return "Entity "+`self.get_cid()`
		else:
			return "["+self.get_family_name()+"/"+self.get_name()+"]"


	# FIXME: this is still a hack and i am unhappy with it
	def __cmp__(self, other):
		td1 = self.get_log_time()
		td2 = other.get_log_time()


		for u in ["ns", "tsc", "sequence"]:
			if u in td1 and u in td2:
				ns1 = td1[u]
				ns2 = td2[u]

				if ns1.get_clocksource() == "generated":
					return -1
				if ns2.get_clocksource() == "generated":
					return 1

				if ns1.get_clocksource() == ns2.get_clocksource():
					return cmp(ns1.get_value(), ns2.get_value())
		return 0

	def get_pid(self):
		return self.pid

	def get_time_dict(self):
		return self.time

	def get_cid(self):
		return self.cid
	
	def get_type(self):
		raise Exception("unimplemented")

	def has_time_object(self, timetype, units):
		return timetype in self.time and units in self.time[timetype]

	def get_time_object(self, timetype, units):
		return self.time[timetype][units]

	def add_time_object(self, timetype, units, obj):
		if timetype not in self.time:
			self.time[timetype] = {}
		self.time[timetype][units] = obj

	def get_times(self):
		return self.time

	# three convenience methods
	def get_log_time(self, units=None):
		if not units:
			return self.time["log"]
		else:
			return self.time["log"][units].get_value()

	def get_tsc(self):
		return self.time["log"]["tsc"].get_value()

	def get_machine(self):
		return self.time["log"]["tsc"].get_clocksource()

	def get_sequence(self):
		return self.time["log"]["sequence"].get_value()

	def get_nanoseconds(self):
		return self.time["log"]["ns"].get_value()


	# these values are looked up in the entity definition
	def get_name(self):
		if self.namespace:
			return self.namespace[self.cid].get_name()
		else:
			return "unknown"

	def get_description(self):
		if self.namespace:
			return self.namespace[self.cid].get_description()
		else:
			return "unknown"

	def get_family_name(self):
		if self.namespace:
			return self.namespace[self.cid].get_family()
		else:
			return "unknown"


	def is_admin(self):
		if self.namespace:
			return self.namespace[self.cid].is_admin()
		else:
			return False

	# a pointer to the namespace for convenience. should not
	# be serialized!
	def set_namespace(self, ns):
		self.namespace = ns
		if self.cid not in ns:
			print self.get_extra_data()
			raise Exception, "INVALID NAMESPACE"

	def clear_cache(self):
		"""should be called before Entity is pickled"""
		self.namespace = None


class Interval(Entity):
	def __init__(self, cid, start_time, end_time, tag=None, pid=0):
		Entity.__init__(self, cid, end_time, pid)
		self.time["start"] = start_time
		self.time["end"] = end_time
		self.tag = tag


	def change_tag(self, new_tag):
		n = Interval(self.cid, None, None, new_tag)
		n.time = self.time
		return n

	def change_cid(self, new_cid):
		n = Interval(new_cid, None, None, self.tag)
		n.time = self.time
		return n

	def get_type(self):
		return namespaces.INTERVALTYPE

	def get_tag(self):
		return self.tag

	def get_start_time(self, units="ns"):
		return self.time["start"][units]

	def get_end_time(self, units="ns"):
		return self.time["end"][units]

	def get_duration(self, units="ns"):
		return (self.get_end_time(units).get_value() - 
				self.get_start_time(units).get_value())
	



class Event(Entity):
	def __init__(self, cid, logtime, tag, extra_data, pid=0):
		Entity.__init__(self, cid, logtime, pid)
		self.tag = tag
		self.extra_data = extra_data
	
	def get_type(self):
		return namespaces.EVENTTYPE

	def get_tag(self):
		return self.tag

	def change_tag(self, new_tag):
		n = Event(self.cid, None, new_tag, self.extra_data)
		n.time = self.time
		return n

	def change_cid(self, new_cid):
		n = Event(new_cid, None, self.tag, self.extra_data)
		n.time = self.time
		return n

	def get_extra_data(self):
		return self.extra_data

	def get_edf_name(self):
		if self.namespace:
			return self.namespace[self.cid].get_edf()
		else:
			return "unknown"

	def change_extra_data(self, new_extra_data):
		n = Event(self.cid, None, self.tag, new_extra_data)
		n.time = self.time
		return n

class Counter(Entity):
	def __init__(self, cid, logtime, count, first_update, last_update, pid=0):
		Entity.__init__(self, cid, logtime, pid)
		self.time["first"] = first_update
		self.time["last"] = last_update
		self.count = count
	
	def change_cid(self, new_cid):
		n = Counter(new_cid, None, self.count, None, None)
		n.time = self.time
		return n

	def get_type(self):
		return namespaces.COUNTERTYPE

	def get_first_update(self):
		return self.time["first"]

	def get_last_update(self):
		return self.time["last"]

	def get_count(self):
		return self.count

class Histogram(Entity):
	def __init__(self, cid, logtime, lowerbound, upperbound, num_buckets, pid=0):
		Entity.__init__(self, cid, logtime, pid)
		self.overflow = 0
		self.underflow = 0
		self.lowerbound = float(lowerbound)
		self.upperbound = float(upperbound)
		self.min_seen = None
		self.max_seen = None
		self.num_buckets = num_buckets
		self.sum = 0
		self.num_events = 0

		self.bucket_range = (self.upperbound - self.lowerbound) / float(num_buckets)
		self.buckets = array.array("L", [0L for i in range(num_buckets)])

	def __str__(self):
		return `self.buckets`

	def change_cid(self, new_cid):
		n = Histogram(new_cid, None, self.lowerbound, self.upperbound, self.num_buckets)
		n.time = self.time
		n.populate(self.underflow, self.overflow, self.sum, self.num_events, self.min_seen,
				self.max_seen, self.buckets)
		return n


	def populate(self, underflow, overflow, sum, num_events, min_seen,
			max_seen, buckets):
		self.underflow = underflow
		self.overflow = overflow
		self.sum = sum
		self.num_events = num_events
		self.min_seen = min_seen
		self.max_seen = max_seen
		self.buckets = buckets

	def get_type(self):
		return namespaces.HISTOGRAMTYPE

	def get_sum(self):
		return self.sum

	def get_count(self):
		return self.num_events

	def get_mean(self):
		if self.get_count() == 0:
			return 0
		return float(self.get_sum()) / float(self.get_count())

	def get_buckets(self):
		return self.buckets

	def get_bucket(self, index):
		return self.buckets[index]

	def get_upperbound(self):
		return self.upperbound

	def get_lowerbound(self):
		return self.lowerbound

	def get_overflow(self):
		return self.overflow

	def get_underflow(self):
		return self.underflow

	def get_num_buckets(self):
		return self.num_buckets

	def get_max_value(self):
		return self.max_seen
	
	def get_min_value(self):
		return self.min_seen

	def get_bucket_range(self, bucket_num=None):
		if bucket_num != None:
			return (self.lowerbound + (bucket_num * self.bucket_range),
				self.lowerbound + ((bucket_num + 1) * self.bucket_range))
		else:
			return self.bucket_range

	def get_units(self):
		if self.namespace:
			return self.namespace[self.cid].get_units()
		else:
			return "unknown"

	def add_value(self, value):
		self.num_events = self.num_events + 1
		if self.max_seen == None or value > self.max_seen:
			self.max_seen = value

		if self.min_seen == None or value < self.min_seen:
			self.min_seen = value

		self.sum = self.sum + value

		offset = float(value) - self.lowerbound
		bucket_num = int(math.floor(offset / self.bucket_range))
	

		if bucket_num < 0:
			self.underflow = self.underflow + 1
		elif bucket_num >= self.num_buckets:
			self.overflow = self.overflow + 1
		else:
			self.buckets[bucket_num] = self.buckets[bucket_num] + 1

	
	def refactor_time(self, tsc_per_sec):
		# move this to a filter
		if self.units == "tsc":
			self.lowerbound = self.lowerbound * tsc_per_sec
			self.upperbound = self.upperbound * tsc_per_sec
			self.max_seen = self.max_seen * tsc_per_sec
			self.min_seen = self.min_seen * tsc_per_sec
			self.sum = self.sum * tsc_per_sec
			self.bucket_range = (self.upperbound - self.lowerbound) / float(self.num_buckets)
			self.units = "ns"
	




