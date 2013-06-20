from pykusp import doubledict
import copy
from pykusp.location import kusproot
from pykusp import configfile
import glob

# some important constants
# FIXME: it would be nice to somehow link these with
# linux/datastreams/datastream_common.h, perhaps a C
# extension
EVENTTYPE = 0
COUNTERTYPE = 1
INTERVALTYPE = 4
HISTOGRAMTYPE = 3
OBJECTTYPE = 2
INTERNALEVENTTYPE = 7

ENTITYTYPES = {
	EVENTTYPE : "event",
	COUNTERTYPE: "counter",
	INTERVALTYPE: "interval",
	HISTOGRAMTYPE: "histogram",
	OBJECTTYPE: "object",
	INTERNALEVENTTYPE: "internal event"
}

admin_filename = kusproot+"/share/dstream_admin.ns"
ns_spec = configfile.get_spec(kusproot+"/share/ns.cspec")



def get_admin_ns():
	"""retrieve the administrative namespace"""
	ans = read_namespace_files(admin_filename)
	for ent in ans.values():
		ent.admin_flag = True
	return ans


def read_namespace_files(filenames):
	"""read a set of namespace files and return a merged
	namespace containing all of them.

	you may supply a string filename or a list of filenames.

	the glob module will be used to expand any wildcards,
	similar to UNIX shells."""

	if type(filenames) is str:
		filenames = [filenames]

	filelist = []
	for filename in filenames:
		filelist.extend(glob.glob(filename))
	filenames = filelist

	retval = Namespace()

	for filename in filenames:
		nscfg = configfile.parse_config(filename,
				ns_spec)
		ns = construct_namespace(nscfg)
		retval.merge(ns)

	return retval

def verify_namespace_config(nscfg):
	"""verify the structure of a configfile namespace specification,
	and return the verified datastructure

	always use the return value!"""
	return configfile.check_config(nscfg, ns_spec)

def construct_namespace(nscfg):
	ns = Namespace()
	for fname, fcfg in nscfg.iteritems():
		for ename, einvo in fcfg["entities"].iteritems():
			etype, ecfg = einvo
			eid = long(ecfg["id"])
			if eid < 0:
				eid = None
			if etype == "event":
				ent = EventSpec(fname, ename, ecfg["desc"],
					ecfg["extra_data"], eid)
			elif etype == "counter":
				ent = CounterSpec(fname, ename, 
						ecfg["desc"], eid)
			elif etype == "interval":
				ent = IntervalSpec(fname, ename,  
						ecfg["desc"], eid)
			elif etype == "histogram":
				ent = HistogramSpec(fname, ename,
					ecfg["desc"], ecfg["units"], eid)
			elif etype =="internal event":
				ent = InternalEventSpec(fname, ename, ecfg["desc"],
						ecfg["extra_data"], eid)
			ns.add_entity(ent)
	return ns


class EntitySpec:
	"""specification for an entity"""
	def __init__(self, family, name, description, id=None, admin_flag=False):
		self.name = name
		self.description = description
		self.family = family
		self.id = id
		self.admin_flag = admin_flag

	def is_admin(self):
		return self.admin_flag

	def get_type(self):
		raise Exception("abstract")

	def get_id(self):
		return self.id

	def get_name(self):
		return self.name

	def get_description(self):
		return self.description

	def get_family(self):
		return self.family

	def get_info_field(self):
		return ""


	def __str__(self):
		return "["+ENTITYTYPES[self.get_type()]+"("+`self.get_id()`+"):"+self.get_family()+"/"+self.get_name()+"]"

	def __repr__(self):
		return self.__str__()

	def get_string(self, preserve_id = False):
		result = (""+self.get_name()+" = "+
			ENTITYTYPES[self.get_type()]+"(\n" +
			'\tdesc = "'+self.get_description()+'"\n')
		if preserve_id:
			result = result + "\tid = "+`int(self.get_id())`+"\n"
		result = result + ")\n"
		return result

class EventSpec(EntitySpec):
	def __init__(self, family, name, description, edf, id=None, admin_flag=False):
		EntitySpec.__init__(self, family, name, description, id, admin_flag)
		self.edf = edf

	def get_edf(self):
		return self.edf

	def get_info_field(self):
		return self.get_edf()

	def get_type(self):
		return EVENTTYPE
	
	def get_string(self, preserve_id = False):
		result = (""+self.get_name()+" = event(\n" +
			'\tdesc = "'+self.get_description()+'"\n')
		if self.get_edf():
			result = result + '\textra_data = "'+self.get_edf()+'"\n'
		if preserve_id:
			result = result + "\tid = "+`int(self.get_id())`+"\n"
		result = result + ")\n"
		return result

	def clone(self):
		c = EventSpec(self.family, self.name, self.description, self.edf, self.id, self.admin_flag)
		return c

class InternalEventSpec(EntitySpec):
	def __init__(self, family, name, description, edf, id=None, admin_flag=False):
		EntitySpec.__init__(self, family, name, description, id, admin_flag)
		self.edf = edf

	def get_edf(self):
		return self.edf

	def get_info_field(self):
		return self.get_edf()

	def get_type(self):
		return INTERNALEVENTTYPE
	
	def get_string(self, preserve_id = False):
		result = (""+self.get_name()+" = Internal event(\n" +
			'\tdesc = "'+self.get_description()+'"\n')
		if self.get_edf():
			result = result + '\textra_data = "'+self.get_edf()+'"\n'
		if preserve_id:
			result = result + "\tid = "+`int(self.get_id())`+"\n"
		result = result + ")\n"
		return result

	def clone(self):
		c = InternalEventSpec(self.family, self.name, self.description, self.edf, self.id, self.admin_flag)
		return c

class HistogramSpec(EntitySpec):
	def __init__(self, family, name, description, units, id=None, admin_flag=False):
		EntitySpec.__init__(self, family, name, description, id, admin_flag)
		self.units = units

	def clone(self):
		c = HistogramSpec(self.family, self.name, self.description, self.units, self.id, self.admin_flag)
		return c

	def get_info_field(self):
		return self.get_units()

	def get_units(self):
		return self.units

	def get_type(self):
		return HISTOGRAMTYPE

	def get_string(self, preserve_id = False):
		result = (""+self.get_name()+" = histogram(\n" +
			'\tdesc = "'+self.get_description()+'"\n'
			'\tunits = "'+self.get_units()+'"\n')

		if preserve_id:
			result = result + "\tid = "+`int(self.get_id())`+"\n"
		result = result + ")\n"
		return result


class CounterSpec(EntitySpec):
	
	def clone(self):
		c = CounterSpec(self.family, self.name, self.description, self.id, self.admin_flag)
		return c

	def get_type(self):
		return COUNTERTYPE

class IntervalSpec(EntitySpec):

	def clone(self):
		c = IntervalSpec(self.family, self.name, self.description, self.id, self.admin_flag)
		return c

	def get_type(self):
		return INTERVALTYPE

 

class Namespace(doubledict.MultiDict):
	def __init__(self):
		doubledict.MultiDict.__init__(self, [str, long])
		# this is intentionally high to protect the admin namespace
		self.free_index = 1024L

	def get_all_ids(self):
		return self.maps[1].keys()


	def get_entity(self, fname, ename):
		k = fname + "/" + ename
		return self[k]

	def get_family(self, fname):
		elist = []
		for x,y in self.keys():
			fn, ename = x.split("/")
			if fn == fname:
				elist.append(self[x])
		return elist

	def find_free_id(self):
		while (self.free_index in self.get_all_ids()):
			self.free_index = self.free_index + 1
		return self.free_index

	def add_entity(self, ent):
		if ent.get_id() == None:
			ent.id = self.find_free_id()

		self[ent.get_family()+"/"+ent.get_name(),
				ent.get_id()] = ent
	

	def check_ids(self):
		for k,v in self.items():
			if v.get_id() not in self:
				print self
				print "ID",v.get_id(),"SHOULD BE",k
				raise Exception()

	def get_families(self):
		fd = {}
		for x, y in self.keys():
			fname, ename = x.split("/")
			if fname in fd:
				fd[fname][ename] = self[y]
			else:
				fd[fname] = {ename:self[y]}
		return fd

	def to_configfile(self, preserve_id=True):
		fd = self.get_families()
		result = ""
		for fname, fdict in fd.items():
			result = result + "<" + fname + ">\n"
			for ename, ent in fdict.items():
				result = result + ent.get_string(preserve_id)
			result = result + "\n"

		return result

	def merge(self, other_ns):
		conflicts = {}
		diff = Namespace()

		for k, ent in other_ns.items():
			name_tuple, eid = k
			fam_name, ent_name = name_tuple.split("/")
			
			if name_tuple in self:
				# same entity in this namespace
				new_id = self.maps[0][name_tuple][1]
				if new_id != eid:
					conflicts[eid] = new_id
			elif eid in self:
				# same id, but not same entity
				new_id = self.find_free_id()
				new_ent = other_ns[eid].clone()
				new_ent.id = new_id
				self[name_tuple, new_id] = new_ent
				diff[name_tuple, new_id] = new_ent
				conflicts[eid] = new_id
			else:
				new_ent = other_ns[eid]
				self[name_tuple, eid] = new_ent
				diff[name_tuple, eid] = new_ent
		
		return conflicts, diff
				





