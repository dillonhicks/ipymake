#!/usr/bin/env python


################################################################
#
# NAME:        namespace_parser.py
# AUTHOR:      Michael Frisbie
#	       Hariharan Subramanian
#              Deepti Mokkapati
#	       Karthikeyan Varadarajan	 
# DESCRIPTION: Parses Datastreams Namespace definition files
#	       and generates a python dictionary
#
################################################################

                                                                                                                                                             
import sys
import string
import pickle
import getopt
from pykusp.doubledict import *
from pykusp.configparser import *

DSTRM_EVENT = 'event'
DSTRM_OBJECT= 'object'
DSTRM_HISTOGRAM = 'histogram'
DSTRM_COUNTER = 'counter'
DSTRM_INTERVAL = 'interval'
DSTRM_TYPES = [ DSTRM_EVENT, DSTRM_OBJECT, DSTRM_HISTOGRAM, DSTRM_COUNTER, DSTRM_INTERVAL ]


def convert_to_new(old_ns_dict):
    """convert an old-style namespace dictionary to the new-style datastructure"""
    result = NSDict()
    result.metadata = {"desc":"converted from old-style config."}
    for fname in old_ns_dict:
        old_fdict = old_ns_dict[fname]
        fid = old_fdict["number"]
        family = AttributeDict()
        family.update({"event":NSDict(),
                       "counter":NSDict(),
                       "histogram":NSDict(),
                       "interval":NSDict(),
                       "object":NSDict()})
        family.metadata = {"name":fname,
                           "id":fid,
                           "shortdesc":old_fdict["description"],
                           "desc":old_fdict["long_description"]}

        itemlist = ["name","shortdesc","printf","kernelf"]
        
        for typename in family:
            counter = 0
            family[typename].metadata["greatest"] = len(old_fdict[typename]) - 1
            
            for old_entity in old_fdict[typename]:
                if old_entity:
                    entity = {}
                    ename = old_entity[0]
                    eid = counter
                    family[typename][(ename,eid)] = entity
                    entity["id"] = counter
                    for index in range(len(old_entity)):
                        entity[itemlist[index]] = old_entity[index]
                    pass
                counter = counter + 1
                pass
            pass
        result[(fname, fid)] = family
        pass
    return result

def process_entry( line, type, families ):
    """
    Process a line from the NS description file.
    This line will describe either
    a counter or a histogram at this time. The type indicates whether it is
    a DSTRM_INTERVAL, DSTRM_COUNTER or a DSTRM_HISTOGRAM. The datastructure
    families into which the entries are to be filled in is also passed as
    an argument
    """
    #
    # Split the line defining a counter or histogram at the quotes
    # this should give two tokens, one containging the description
    # and one containing everything else
    #
    first_split = string.split(line,"\"", 1)
    #
    # The first portion of the string first_split
    # contains other tokens seperated by whitespace
    # So tokenize first_split[0]
    #
    finer_split = string.split(first_split[0],None,5)
    #
    # Now accumulate the tokens into a reasonable
    # list we can work with by appending the elements
    # together in order 
    #
    eachLineList=[]
    for element in finer_split:
      eachLineList.append(element)
    #
    # It now adds to these elements the description which was 
    # generated in the first split.
    #
   
    desc_split = string.strip(first_split[1])

    desc_split = string.replace(desc_split, "\"", "")
    
    desc_split = string.strip(desc_split)
  
    eachLineList.append(desc_split)

    #
    # Get useful values into some reasonably named
    # variables
    # 
    family = eachLineList[1]
    #
    # The eachLineList[2] contains the family's number id which
    # should be removed from the namespace specification file
    #
    symbol = eachLineList[3]
    number = string.atoi(eachLineList[4])
    desc = eachLineList[5]
    #
    # We begin by finding the dictionary within the global variable
    # families which describes this specific family
    # the second index then sees how long the list for the
    # specific event type we are processing now currently is, then
    # adds "None" elements to the list until we can add the current
    # NS line we are processing at the right index.
    #
    # This loop is stupid for several reasons. First, we should probably
    # avoid the double index if we can, but that might mean wasted copying
    # so it is not guaranteed to be bad. Certainly, we should find out the
    # current length only once  and then use it as the limit of a for loop
    # to add the proper number of "None" elements.
    #
    while len(families[family][type]) <= number:
        families[family][type].append(None)

    #
    # Check to see if the element of the family element list (counter or hist)
    # is None or already set. If not set, fill it in. If already set, then it
    # is an error.
    #
    if families[family][type][number] == None:
        families[family][type][number] = [symbol, desc]
    else:
        # Not None, therefore event was
        # already set in the family.
        print "WARNING: entity %d redefined in family %s" % (number, family)


#
# Process a line from the NS description file that describes an object
# The datastructure families into which the entries are to be filled in
# is also passed as an argument
#
def process_object( line, families ):
    #
    # Split the line defining an object twice at the quotes
    # this should give three tokens, one containging the description,
    # one containing kernel_handling_function and user_pretty_print
    # function and the third containing everything else
    #
    first_split = string.split(line,"\"", 2)
    #
    # The first portion of the string first_split
    # contains other tokens seperated by whitespace
    # So tokenize first_split[0]
    #
    finer_split_one = string.split(first_split[0],None,5)
    #
    # The third portion of the string first_split
    # contains the handling functions seperated by whitespace
    # So tokenize first_split[2]
    #
    finer_split_two = string.split(first_split[2],None,1)
    #
    # Now accumulate the tokens into a reasonable
    # list we can work with by appending the elements
    # together in order 
    #
    eachLineList=[]
    for element in finer_split_one:
      eachLineList.append(element)
    #
    # It now adds to these elements the description which was 
    # generated in the first split.
    #
    eachLineList.append(string.strip(first_split[1]))
    #
    # Now append the elements in the finer_split_two
    # These are the kernelhandling function and user printing
    # function.
    #
    for element in finer_split_two:
      eachLineList.append(element)
    #
    # Get useful values into some reasonably named
    # variables
    # 
    type = DSTRM_OBJECT
    family = eachLineList[1]
#   print "family " + family
    #
    # The eachLineList[2] contains the family's number id which
    # should be removed from the namespace specification file
    #
    symbol = eachLineList[3]
#   print "symbol " + symbol
    number = string.atoi(eachLineList[4])
#   print "number " + eachLineList[4]
    desc = eachLineList[5]
#   print "desc " + desc
    print_func = eachLineList[6]
#   print "print_func " + print_func
    kernel_func = eachLineList[7]
#   print "kernel_func " + kernel_func
    #
    # We begin by finding the dictionary within the global variable
    # families which describes this specific family
    # the second index then sees how long the list for the
    # specific event type we are processing now currently is, then
    # adds "None" elements to the list until we can add the current
    # NS line we are processing at the right index.
    #
    # This loop is stupid for several reasons. First, we should probably
    # avoid the double index if we can, but that might mean wasted copying
    # so it is not guaranteed to be bad. Certainly, we should find out the
    # current length only once  and then use it as the limit of a for loop
    # to add the proper number of "None" elements.
    #
    while len(families[family][type]) <= number:
        families[family][type].append(None)
    #
    # Check to see if the element of the family element list (counter or hist)
    # is None or already set. If not set, fill it in. If already set, then it
    # is an error.
    #
    if families[family][type][number] == None:
        families[family][type][number] =[symbol, desc, print_func, kernel_func]
    else:
        # Not None, therefore event was
        # already set in the family.
        print "WARNING: event %d redefined in family %s" % (number, family)


#
# Process a line from the NS description file that describes an event
# The datastructure families into which the entries are to be filled in
# is also passed as an argument
#
def process_event( line, families ):
    #
    # Split the line defining an object twice at the quotes
    # this should give three tokens, one containging the description,
    # one containing kernel_handling_function and user_pretty_print
    # function and the third containing everything else
    #
    first_split = string.split(line,"\"", 2)
    #
    # The first portion of the string first_split
    # contains other tokens seperated by whitespace
    # So tokenize first_split[0]
    #
    finer_split_one = string.split(first_split[0],None,5)
    #
    # Now accumulate the tokens into a reasonable
    # list we can work with by appending the elements
    # together in order 
    #
    eachLineList=[]
    for element in finer_split_one:
      eachLineList.append(element)
    #
    # It now adds to these elements, the description and the
    # extra_data handling routine which were generated
    # during the first split.
    #
    eachLineList.append(string.strip(first_split[1]))
    eachLineList.append(string.strip(first_split[2]))
    #
    # Get useful values into some reasonably named
    # variables
    # 
    type = DSTRM_EVENT
    family = eachLineList[1]
    #
    # The eachLineList[2] contains the family's number id which
    # should be removed from the namespace specification file
    #
    symbol = eachLineList[3]
    number = string.atoi(eachLineList[4])
    desc = eachLineList[5]
    print_func = eachLineList[6]

    #
    # We begin by finding the dictionary within the global variable
    # families which describes this specific family
    # the second index then sees how long the list for the
    # specific event type we are processing now currently is, then
    # adds "None" elements to the list until we can add the current
    # NS line we are processing at the right index.
    #
    # This loop is stupid for several reasons. First, we should probably
    # avoid the double index if we can, but that might mean wasted copying
    # so it is not guaranteed to be bad. Certainly, we should find out the
    # current length only once  and then use it as the limit of a for loop
    # to add the proper number of "None" elements.
    #
    try:
        while len(families[family][type]) <= number:
            families[family][type].append(None)    
    except KeyError,error:
        raise ParseException, "Incorrrect/No family definition found for family:%s"%(family)
    #
    # Check to see if the element of the family element list (counter or hist)
    # is None or already set. If not set, fill it in. If already set, then it
    # is an error.
    #
    if families[family][type][number] == None:
        families[family][type][number] =[symbol, desc, print_func]
    else:
        # Not None, therefore event was
        # already set in the family.
        print "WARNING: event %d redefined in family %s" % (number, family)


#
# Another part of the code used when reading a NS file and building a
# data structure (dictionary) while reading the NS description file
#
# the argument to this routine is the file descriptor starting at the beginning of the
# NS description file
#
# The datastructure families into which the entries are to be filled in
# is also passed as an argument
#
# consider that this and build_families have similar structure, and
# could probably be combined into a single command that can build the NS dictionary
# in a single pass
#
# I know that we discussed about clarity reasons for not combining the build_families
# and build_entities. The comment able suggests something else. I am confused.
#
def build_entities( data, families ):

    result = 0
    #
    # for each line in the NS description file
    #
    for eachLine in data:
        eachLine = string.strip(eachLine)
        if eachLine == "" or eachLine[0] == '#':
	    #
	    # skip comments and blank lines
	    #
            pass
        else:
            eachLineList = string.split(eachLine, None, 1)
	    #
	    # Call the relevant processing routine for each type
	    # of family member. Note that histograms and counters are
	    # processed by the "process_entry" routine 
	    #
            if eachLineList[0] == "DSTRM_EVENT":
                process_event( eachLine, families )
            elif eachLineList[0] == "DSTRM_COUNTER":
                process_entry( eachLine, DSTRM_COUNTER, families )
            elif eachLineList[0] == "DSTRM_OBJECT":
                process_object( eachLine, families )
            elif eachLineList[0] == "DSTRM_HISTOGRAM":
                process_entry( eachLine, DSTRM_HISTOGRAM, families )
            elif eachLineList[0] == "DSTRM_INTERVAL":
                process_entry( eachLine, DSTRM_INTERVAL, families )
	    elif eachLineList[0] == "DSTRM_FAMILY":
	        #
		# Here we skip lines for family definitions because
		# the current structure of the code assumes this was
		# done in an earlier pass
		#
		pass

            else:
                result = -1
                print "Unknown Entry:", eachLineList[0]
                
    return result

def build_long_descriptions(data, families):
    long_desc_started = False
    long_desc = ""
    family = None
    
    #for each line in the data we are only interested in those
    #which start with #!. This indicates the beginning of a long comment
    #of a family or entity.

    for eachLine in data:
        #strip the line of whitespace and return as list
        eachLine = string.strip(eachLine)

        if eachLine == "" and len(eachLine) > 1:
            continue

        #skip this line if it isn't something we are interested in
        if eachLine[:2] == '#!':
            identifier = eachLine[2:].split()
            
            if long_desc_started and identifier == []:
                try:
                    families[family]["long_description"] = long_desc
                except:
                    raise ParseException, "Invalid family " + family + " found while parsing long descriptions."
                
                long_desc = ""
                long_desc_started = False
                
            elif not long_desc_started and len(identifier) > 0:
                family = identifier[0]
                long_desc_started = True

            else:
                raise ParseException, "Invalid long description tag " + eachLine + ", ending parse. To start a long description place a #! FAMILY_NAME on a line by itself. To end a long description place a #! on a line by itself."
                
        elif long_desc_started:
            long_desc = long_desc + eachLine[1:] + "\n"

    if long_desc_started:
        raise ParseException, "There was no long description close tag for family " + family + ", ending parse. To end a long description place a #! on a line by itself."

    return 0

def build_families( data,families ):
    result = 0
    for eachLine in data:
        eachLine = string.strip(eachLine)
        
        if eachLine == "" or eachLine[0] == '#':
            pass
        else:
            eachLinefirst = string.split(eachLine, None, 1)
            if eachLinefirst[0] == "DSTRM_FAMILY":
                #
                # This line tokenizes by looking for the default token
                # seperator(whitespace) in eachLine thrice. So it results
                # in four tokens
                #
                eachLineDesc = string.split(eachLine, None, 3)

                #
                # FAM 0 is reserved by the datastreams
                # for administrative purposes So raise an alarm
                # if it is a part of the namespace file
                #
                #if eachLineDesc[2] == '0':
                    #print "Error:Family number Zero is reserved for administrative purposes \n \
                    #Correct your namespace file and try again"
                    #result=-1
                    #sys.exit(result)

                #
                # This is creating an entry in the dictionary using the
                # family name as the key (element 1 in EachLineDesc)
                #
                eachLineDesc[3]=string.replace(eachLineDesc[3], "\"", "")
                eachLineDesc[3]=string.strip(eachLineDesc[3])

                families[eachLineDesc[1]] = {'family_name':eachLineDesc[1],
                                             'number':string.atoi(eachLineDesc[2]),
                                             'description': eachLineDesc[3],
                                             'long_description': "", DSTRM_EVENT: [], DSTRM_COUNTER: [], 
                                             DSTRM_OBJECT: [], DSTRM_HISTOGRAM: [], DSTRM_INTERVAL: []}
            else:
                #
                # We just ignore the entry if it dosent describe a family
                # which is true if we get here. So pass
                #
                pass
               
    return result
                                                                                                                                                             
#
# This is the published method if this Python module that takes ONE
# namespace specification file and the families datastructures
# as input and returns the python dictionary populated with the
# family level and entity level components. This method is used by
# anybody who is interested in parsing a namespace file.
#
def read_namespace_data( file, families=None ):

    if not families:
        families = {}
        pass
    
    try:
        spec=open(file,'r')
    except IOError,error:
        raise ParseException, "Error opening the file: "+file
    
    # 
    # The namespace file parsing is done in two steps
    # In the first pass of generate a datastructure that
    # contains all the family level entries
    #
    exitval=build_families(spec,families)
    #
    # Find the file rewind method in python and use
    # it instead of closing the file here
    #
    spec.close()
    
    try:
        spec=open(file,'r')
    except IOError,error:
        raise ParseException, "Error opening the file: "+file
    # 
    # In the second pass, for every family level element,
    # populate the events,counters,objects and histograms
    # specified in the datastream namespace file
    #
    exitval=build_entities(spec,families)
    spec.close()

    #
    # In the third pass, we search for long descriptions and
    # add them to the appropriate family or event.
    #

    try:
        spec = open(file, 'r')
    except IOError, error:
        raise ParseException, "Error opening the file: "+file

    exitval=build_long_descriptions(spec, families)
    spec.close()
    
    #
    # Return the python dictionary that we built parsing the list
    # of datastream namespace files.
    #
    #print families
    return families

#
# It gets a namespace dictionary as input and prints back the namespace
# specification file. It also gets the name of the new file. If the file
# name is invalid, then the default file namespace_output.dski is generated
# in local directory
#
def write_namespace_data( file, families ):

    result=0
    #
    # If None is specified as the output file name,
    # then write the output to namespace_output.dski
    # in local directory
    #
    if file == None:
        file='namespace_output.dski'

    #
    # Open the namespace specification output file
    #
    try:
        specFile=open(file,'w')
    except IOError,error:
        print "Error opening the file: ",file
        return -1
    
    #
    # Generating family level entries
    # Iterate over all families in the dictionary
    #
    for family_name in families.keys():
        
        #
        # Generate the family level entry
        #
        specFile.write("DSTRM_FAMILY\t\t%s\t\t%s\t\t\"%s\"\n" %(family_name,families[family_name]['number'],families[family_name]['description']))
    #
    # Generating the event level entries
    # Iterate over all families in the dictionary
    #
    for family_name in families.keys():	
        
        #
        # For each family, iterate over every event in that family
        #
        for event_number in range(len(families[family_name][DSTRM_EVENT])):
            #
            # If the dictionary dosent have any valid data for a particular
            # event (generally if event numbers dont start at zero), move on
            # with the next event_number
            #
            if families[family_name][DSTRM_EVENT][event_number]==None:
                continue
            #
            # Generate the event entries
            #
            specFile.write("DSTRM_EVENT\t\t")
            specFile.write("%s\t\t" %(family_name))
            specFile.write("%s\t\t" %(families[family_name]['number']))
            specFile.write("%s\t\t" %(families[family_name][DSTRM_EVENT][event_number][0]))
            specFile.write("%s\t\t" %(event_number))
            specFile.write("\"%s\"\t\t" %(families[family_name][DSTRM_EVENT][event_number][1]))
            specFile.write("%s\n\n" %(families[family_name][DSTRM_EVENT][event_number][2]))
    #
    # Generating the histogram level entries
    # Iterate over all families in the dictionary
    #
    for family_name in families.keys():
        #
        # For each family, iterate over every histogram in that family
        #
        for hist_number in range(len(families[family_name][DSTRM_HISTOGRAM])):
            #
            # If the dictionary dosent have any valid data for a particular
            # histogram (generally if histogram numbers dont start at zero), move on
            # with the next hist_number
            #
            if families[family_name][DSTRM_HISTOGRAM][hist_number]==None:
                continue
            #
            # Generate the histogram entries
            #
            specFile.write("DSTRM_HISTOGRAM\t\t")
            specFile.write("%s\t\t" %(family_name))
            specFile.write("%s\t\t" %(families[family_name]['number']))
            specFile.write("%s\t\t" %(families[family_name][DSTRM_HISTOGRAM][hist_number][0]))
            specFile.write("%s\t\t" %(hist_number))
            specFile.write("\"%s\"\n\n" %(families[family_name][DSTRM_HISTOGRAM][hist_number][1]))
    #
    # Generating the counter level entries
    # Iterate over all families in the dictionary
    #
    for family_name in families.keys():
        #
        # For each family, iterate over every counter in that family
        #
        for counter_number in range(len(families[family_name][DSTRM_COUNTER])):
            #
            # If the dictionary dosent have any valid data for a particular
            # counter (generally if counter numbers dont start at zero), move on
            # with the next counter_number
            #
            if families[family_name][DSTRM_COUNTER][counter_number]==None:
                continue
            #
            # Generate the counter entries
            #
            specFile.write("DSTRM_COUNTER\t\t")
            specFile.write("%s\t\t" %(family_name))
            specFile.write("%s\t\t" %(families[family_name]['number']))
            specFile.write("%s\t\t" %(families[family_name][DSTRM_COUNTER][counter_number][0]))
            specFile.write("%s\t\t" %(counter_number))
            specFile.write("\"%s\"\n\n" %(families[family_name][DSTRM_COUNTER][counter_number][1]))
    #
    # Generating the object level entries
    # Iterate over all families in the dictionary
    #
    for family_name in families.keys():
        #
        # For each family, iterate over every object in that family
        #
        for object_number in range(len(families[family_name][DSTRM_OBJECT])):
            #
            # If the dictionary dosent have any valid data for a particular
            # object (generally if object numbers dont start at zero), move on
            # with the next object_number
            #
            if families[family_name][DSTRM_OBJECT][object_number]==None:
                continue
            #
            # Generate the object entries
            #
            specFile.write("DSTRM_OBJECT\t\t")
            specFile.write("%s\t\t" %(family_name))
            specFile.write("%s\t\t" %(families[family_name]['number']))
            specFile.write("%s\t\t" %(families[family_name][DSTRM_OBJECT][object_number][0]))
            specFile.write("%s\t\t" %(object_number))
            specFile.write("%s\t\t" %(families[family_name][DSTRM_OBJECT][object_number][1]))
            specFile.write("%s\t\t" %(families[family_name][DSTRM_OBJECT][object_number][2]))
            specFile.write("%s\n\n" %(families[family_name][DSTRM_OBJECT][object_number][3]))
    #
    # Generating the interval level entries
    # Iterate over all families in the dictionary
    #
    #print families.keys()
    for family_name in families.keys():
        #
        # For each family, iterate over every interval in that family
        #
        #print families
#       print families[family_name]
#       print ""
        for interval_number in range(len(families[family_name][DSTRM_INTERVAL])):
            #
            # If the dictionary dosent have any valid data for a particular
            # interval (generally if interval numbers dont start at zero), move on
            # with the next interval_number
            #
            if families[family_name][DSTRM_INTERVAL][interval_number]==None:
                continue
            #
            # Generate the interval entries
            #
            specFile.write("DSTRM_INTERVAL\t\t")
            specFile.write("%s\t\t" %(family_name))
            specFile.write("%s\t\t" %(families[family_name]['number']))
            specFile.write("%s\t\t" %(families[family_name][DSTRM_INTERVAL][interval_number][0]))
            specFile.write("%s\t\t" %(interval_number))
            specFile.write("\"%s\n\n" %(families[family_name][DSTRM_INTERVAL][interval_number][1]))

    #
    # we must now output all of the descriptions that were read
    #
    for family_name in families.keys():
        #get the long description for the family
        long_desc = families[family_name]["long_description"]
        #print families[family_name].keys()
        #if long desc is None nothing had originally been given in the ns file
        if long_desc != None:
            long_desc = string.replace(long_desc, "\n", "\n#")
            specFile.write("#!%s\n#%s\n#!\n\n" % (family_name, long_desc))
            
    return result

