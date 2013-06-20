import configfile_mod
import copy
from location import kusproot

print "WARNING: The pykusp.configfile module is depreciated."
print "   Please update your code to use pykusp.configutility."

class ConfigfileException(Exception): pass
class ConfigfileVerifyException(Exception): pass

specspecfname = kusproot + "/share/cspec.cspec"

# mysterious function!
#
# In reference to the above comment:
# Are you kidding me? That kind of shit 
# is unacceptable. Next time do me a kindness
# and not comment it.
# -Dillon
#
def fix_ref(item):
	# problems may happen if
	# reference targets are invocations
	# that contain references
	if type(item) is dict:
		# recursively call fix_ref on each dictionary
		# item. if the result is not None, replace the value
		for k, v in item.iteritems():
			a = fix_ref(v)
			if a:
				item[k] = a
	elif type(item) is list:
		for i in range(len(item)):
			a = fix_ref(item[i])
			if a:
				item[i] = a
	elif type(item) is tuple:
		a, b = item
		
		if type(a) is dict:
			while True:
				z = a[b]
				if type(z) is tuple and type(z[0]) is dict:
					a, b = z
				else:
					break
			return a[b]
		else:
			nb = fix_ref(b)
			if nb:
				return (a, fix_ref(b))
	return None

def get_spec(filename):
	"""parse and verify a spec file, with a given filename"""
	return parse_config(filename, specspecfname)



def get_spec_from_string(spec_str):
	"""parse and verify a spec file given as a string"""
	return check_spec(parse_string(spec_str))

def to_string(config):
	"""convert a config dictionary into a string representation which can
	be read by the parser"""
	return configfile_mod.config_to_string(config)

def parse_string(config):
	"""parse a config given as a string"""
	x = configfile_mod.parse_string(config)
	fix_ref(x)
	return x

def parse_config(filename, spec=None):
	"""Parse a configfile stored in the specified filename.

	If the spec parameter is given, the parsed file will be checked against
	the spec. The spec can either be a filename or the spec dictionary itself"""
	if spec == None:
		result = configfile_mod.parse_config(filename)
	else:
		if type(spec) is str:
			result = configfile_mod.parse_config(
				filename, spec)
		else:
			result = configfile_mod.parse_config(
					filename)
			fix_ref(result)
			return check_config(result, spec)

	fix_ref(result)
	return result

def check_spec(spec_dict):
	"""verify a spec that was not read in from a file"""
	return configfile_mod.check_spec_dict(spec_dict, 
			specspecfname)


def check_config(config_dict, spec):
	"""check a config dict against a spec.
	spec can be a filename or a spec dictionary
	
	if the spec is a dictionary, it is assumed that
	it has already been verified. use check_spec if you
	need to"""
	if type(spec) is str:
		spec = get_spec(spec)
	return configfile_mod.check_dict(config_dict, spec)




# FIXME: re-write all of this
typenames = {
	str : "string",
	int : "integer",
	dict : "dictionary",
	tuple : "invocation",
	list : "list",
	long : "long",
	float : "real",
	bool : "boolean"
}


nametypes = {}
for k,v in typenames.iteritems():
	nametypes[v] = k

# this is rudimentary and needs a lot of work

def get_spec_help(outfile, spec):
	get_dictionary_help(outfile, spec["root"]["dictdef"])

def get_dictionary_help(outfile, spec, indent=0):
	for key in spec:
		keyspec = spec[key]
		if "doc" in keyspec:
			doc = keyspec["doc"]
		else:
			doc = "No documentation for this key"
		
		if "required" in keyspec and keyspec["required"]:
			required = "(Required)"
		else:
			required = "(Optional)"

		if required == "(Optional)" and "default" in keyspec:
			default = "(Default is "+`keyspec["default"]`+")"
		else:
			default = "(No default value)"
		
		outfile.write((indent*4*' ')+key+": "+required+" "+default+"\n")
		outfile.write(((indent+1)*4*' ')+doc+"\n")
		outfile.write(((indent+1)*4*' ')+"Value is of type: ")
		get_item_help(outfile, keyspec, indent+1)
		outfile.write("\n")

def get_item_help(outfile, spec, indent=0):
	ts = spec["types"]
	for t in ts:
		if t != "list":
			outfile.write(t+"\n")
		else:
			outfile.write("List of ")

		if "range" in spec:
			outfile.write((indent*4*' ')+"Values must be within interval "+`spec["range"]`+"\n")
		if "constraints" in spec:
			outfile.write((indent*4*' ')+"Values must be one of "+`spec["constraints"]`+"\n")

		if t == "dictionary":
			if "dictdef" in spec:
				get_dictionary_help(outfile, spec["dictdef"], indent)
			if "opendictdef" in spec:
				outfile.write(indent*4*' '+"Arbitrary keys must have values of format: ")
				get_item_help(outfile, spec["opendictdef"], indent + 1)
			if "dictdef" not in spec and "opendictdef" not in spec:
				outfile.write((indent*4*' ')+"Contents unspecified, see documentation")
		if t == "invocation":
			if "invodef" in spec:
				for k,v in spec["invodef"].items():
					outfile.write((indent*4*' ')+k+" parameters: \n")
					get_dictionary_help(outfile, v, indent+1)
			elif "openinvodef" in spec:
				outfile.write((indent*4*' ')+"Arbitrary invocations have parameters: \n")
				get_dictionary_help(outfile, spec["openinvodef"], indent+1)
			if "invodef" not in spec and "openinvodef" not in spec:
				outfile.write((indent*4*' ')+"Invocation semantics unspecified, see documentation")
		if t == "list":
			if "listdef" in spec:
				get_item_help(outfile, spec["listdef"], indent + 1)
			else:
				outfile.write(indent*4*' '+"unspecified contents; see documentation")

			
		
