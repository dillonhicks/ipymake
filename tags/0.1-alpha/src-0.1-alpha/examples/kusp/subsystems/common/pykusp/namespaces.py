# AUTHOR: Andrew Boie
import sys
import glob
import os
import struct
from doubledict import *
from datastreams import namespaces as new_ns_code
from location import kusproot 


print "WARNING: Old namespace code imported. You should rewrite your script"
print "to use the new namespace datastructures."

def read_namespace(filename):
    return read_namespace_list([filename])

def read_admin_namespace():
    # next, open the Admin Namespace (if we can) and add it to the list
    admin_ns_filename = kusproot+"/share/dstream_admin.ns"
    try:
	admin_ns = convert_to_v1_datastructure(new_ns_code.get_admin_ns())
    except IOError, ex:
	print ex
        print "An error occurred when automatically trying to merge the admin namespace."
        print "You will need to specify the admin namespace location manually."
        admin_ns = NSDict()
        pass
    return admin_ns


def create_namespace():
	ns = NSDict();
	ns.metadata = {
		"desc":"Empty long description.",
                "shortdesc":"Empty single-line description."
	}

	return ns;

def create_family():
	fam = AttributeDict();
	fam["event"] = NSDict()
	fam["counter"] = NSDict()
	fam["histogram"] = NSDict()
	fam["interval"] = NSDict()
	fam["object"] = NSDict()
	fam.metadata = {
		"name":"UNDEFINED",
		"id":-1,
		"desc":"Blank long description",
		"shortdesc":"Blank single-line description",
	}

	return fam;

def add_entity(family, entity):
	family[entity["type"]][entity["name"],entity["id"]] = entity
	return

def add_family(ns, family):
	ns[family.metadata["name"], family.metadata["id"]] = family
	return

entity_typemap = {
	0 : "event",
	1 : "counter",
	2 : "object",
	3 : "histogram",
	4 : "interval"
}

def deserialize_entity(infile):
	entity_t_format = "49s81s49s49s49siPiP"
	entity_t_size = struct.calcsize(entity_t_format);
	
	bin = infile.read(entity_t_size);
	enttuple = struct.unpack(entity_t_format, bin);

	ent = {
		"name" : enttuple[0],
		"shortdesc" : enttuple[1],
		"print_func" : enttuple[2],
		"kernel_func" : enttuple[3],
		"timestd" : enttuple[4],
		"id" : enttuple[5],
		"type" : entity_typemap[enttuple[7]]
	}

	return ent

def deserialize_family(infile):
	family_t_format = "49s81s5iiPP"
	family_t_size = struct.calcsize(family_t_format);

	bin = infile.read(family_t_size);
	famtuple = struct.unpack(family_t_format, bin);

	fam = create_family();
	fam.metadata["name"] = famtuple[0]
	fam.metadata["shortdesc"] = famtuple[1]
	fam.metadata["id"] = famtuple[2]
	num_entities = famtuple[4]

	for i in range(num_families):
		entity = deserialize_entity(infile)
		add_entity(fam, entity)
	return fam


def deserialize_namespace(infile):
	namespace_t_format = "iiPP"
	namespace_t_size = struct.calcsize(namespace_t_format);

	bin = infile.read(namespace_t_size);
	nstuple = struct.unpack(namespace_t_format, bin);

	ns = create_namespace();
	num_families = nstuple[1];

	for i in range(num_families):
		fam = deserialize_family(infile);
		add_family(ns, fam)
	
	return ns


def read_namespace_list(ns_filename_listing):
    """merge a list of namespaces into a single namespace
    raises an exception if collisions detected.
    note that namespace-level metadata will be the original list
    of namespaces."""

    err = False

    filename_listing = []
    for filename in ns_filename_listing:
        filename_listing.extend(glob.glob(filename))
        pass
   
    ns = new_ns_code.get_admin_ns()
    ns.merge(new_ns_code.read_namespace_files(filename_listing))
    return convert_to_v1_datastructure(ns)


def convert_to_old_datastructure(config_dict):
    """converts a namespace datastructure into the older format used by
    some of the postprocessing code.
    """
    result1 = {}
    result2 = {}
    
    for family, fid in config_dict.keys():
        fdict = config_dict[fid]

        oldfdict = {
            'family_name':family,
            'number':fid,
            'description':fdict.metadata["shortdesc"],
            'long_description':fdict.metadata["desc"],    
        }
        
        result1[family] = oldfdict
        result2[fid] = oldfdict
        
        for type in fdict.keys():
            tdict = fdict[type]
            oldelist = []
            oldfdict[type] = oldelist

            # determine the highest entity number
            highest = -1
            for ename, eid in tdict.keys():
                if eid > highest:
                    highest = eid
                    pass
                pass

            for i in range(highest + 1):
                oldelist.append(None)
                pass
            
            for ename, eid in tdict.keys():
                entity = tdict[eid]
                itemlist = ["name","shortdesc","printf","kernelf"]
                oldelist[eid] = [None,None,None,None]
                for i in range(len(itemlist)):
                    if itemlist[i] in entity:
                        oldelist[eid][i] = entity[itemlist[i]]
                        pass
                    pass
                oldelist[eid] = tuple(oldelist[eid])
                pass
        
            pass
        pass

    return {'name':result1,
            'number':result2}

def convert_to_v1_datastructure(ns):
	oldns = create_namespace()

	for fam in ns.get_family_specs():
		key = (fam.get_name(), fam.get_fid())
		oldfam = create_family()
		
		oldfam.metadata = {
			"name" : fam.get_name(),
			"id" : fam.get_fid(),
			"shortdesc" : fam.get_description(),
			"desc" : ""
		}

		add_family(oldns, oldfam)

		for ent in fam.get_entity_specs():
			oldent = {
				"name" : ent.get_name(),
				"id" : ent.get_eid(),
				"shortdesc" : ent.get_description(),
				"type" : new_ns_code.ENTITYTYPES[ent.get_type()],
			}
			t = ent.get_type()
			if t == new_ns_code.EVENTTYPE:
				oldent["print_func"] = ent.get_edf()
			elif t == new_ns_code.HISTOGRAMTYPE:
				oldent["timestd"] = ent.get_units()
			elif t == new_ns_code.OBJECTTYPE:
				oldent["kernel_func"] = ent.get_kf()
			add_entity(oldfam, oldent)
	return oldns


