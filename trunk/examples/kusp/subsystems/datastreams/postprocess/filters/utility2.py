#It probably is possible to contain the filter_by filters in one filter
#May want to have all the filter_by filters within one file

#Need to change much of the documentation here to correspond with Sphinx docs


from datastreams.postprocess import filtering
from datastreams.postprocess import entities
from datastreams import namespaces
import sys
import os
import copy
import time

class split_outputs(filtering.Filter):
    """This filter splits the output stream, based on the specified 
    output names. The whole datastream is sent to each of the output
    pipelines."""

    expected_parameters = {
        "outputs" : {
            "types" : "list",
            "doc" : "List of outputs to send output to",
            "listdef" : {
                "types" : "string"
            },
            "required" : True
        }
    }

    def initialize(self):
        self.output_names.extend(self.params["outputs"])
    
    def process(self, entity):
        self.send(entity)
    
    def finalize(self):
        pass

class filter_by_events(filtering.Filter):
    """Filters +/- by event IDs."""

    expected_parameters = {
        "events" : {
            "types" : "list",
            "doc" : "List of event names",
            "listdef" : {
                "types" : "string"
            },
            "default" : []
        },
        "discard" : {
            "types" : "boolean",
            "doc" : "If True, the filter discards all instances of the listed events. \
                If False, the filter retains all instances of the listed events, \
                discarding all others.",
            "default" : False
        }
    }
    

    def initialize(self):
        self.discard = self.params["discard"]
        self.event_ptrs = []
        self.entities_in = []
        self.entities_out = []

        for name in self.params["events"]:
            self.event_ptrs.append(self.get_ns_pointer(name))

    def process(self, entity):

        #If the entity matches one of the input events, add it to the "in" list
        for ptr in self.event_ptrs:
            if entity.get_cid() == ptr.get_cid():
                print entity
                self.entities_in.append(entity)
        
        #If it didn't match any, add it to the "out" list
        if (not self.entities_in) or self.entities_in[-1] != entity:
            self.entities_out.append(entity)
                

    def finalize(self):
        
        #If discard, we are only sending entities that did not match
        if self.discard:
            while self.entities_out:
                self.send(self.entities_out.pop(0))

        #If not discard, we send entities that matched the given event IDs
        else:
            while self.entities_in:
                self.send(self.entities_in.pop(0))

class filter_by_tag(filtering.Filter):
    """Filters +/- by event tag values."""

    expected_parameters = {
        "tag_values" : {
            "types" : "list",
            "doc" : "Tag values to filter by",
            "listdef" : {
                "types" : "integer"
            },
            "default" : []
        },
        "discard" : {
            "types" : "boolean",
            "doc" : "If True, the filter discards all events with the given tag values. If False, the filter retains all events with the given tag values.",
            "default" : False
        }
    }

    def initialize(self):
        self.tags = self.params["tag_values"]
        self.discard = self.params["discard"]
        
        self.entities_in = []
        self.entities_out = []
        
    def process(self, entity):
        
        #If entity is not a histogram (histograms have no tag):
        if entity.get_type() != 3:
            #If entity's tag value matches one of the given tag value, add it to "in" list
            if entity.get_tag() in self.tags:
                self.entities_in.append(entity)

            #If not, add it to the "out" list
            else:
                self.entities_out.append(entity)

    def finalize(self):
        #If discard is true, send the entities whose tag values did not match
        if self.discard:
            while self.entities_out:
                self.send(self.entities_out.pop(0))

        #If discard is false, send the entities whose tag values did match
        else:
            while self.entities_in:
                self.send(self.entities_in.pop(0))

        

class filter_by_time(filtering.Filter):
    """Filters +/- by time intervals."""

    #FIXME.Devin: Investigate constraints of types of things and why at the
    #moment the type of the time coordinate has to be real. However, conversion
    #to PLY based configuration files may change the situation.
    expected_parameters = {
        "time_intervals" : {
            "types" : "list",
            "doc" : "List of time intervals",
            "listdef" : {
                "types" : "list",
                "doc" : "Interval lists",
                "listdef" : {
                    "types" : ["integer", "long"],
                    "doc" : "start and end"
                }                    
            },
            "default" : []
        },
        "time_key" : {
            "types" : "string",
            "doc" : "Time coordinate to use for filtering",
            "default" : "tsc"
        },
        "discard" : {
            "types" : "boolean",
            "doc" : "If True, the filter discards all events inside the listed time intervals. If False, the filter retains all events within the listed time intervals.",
            "default" : False
        }
    }

    def initialize(self):

        #The key in the time_intervals dictionary is the start time, and the value is the end time
        self.time_intervals = self.params["time_intervals"]
        self.time_key = self.params["time_key"]
        self.discard = self.params["discard"]        

        self.entities_in = []
        self.entities_out = []
    
    def process(self, entity):
        
        # time is the time of the entity according to the given time unit
        time = entity.get_log_time()[self.time_key].get_value()

        #Go through list and access each 2-value list
        #If the variable time is between any of these pairs, it goes in the "in" list
        for li in self.time_intervals:
            start = li[0]
            end = li[1]
            if time >= start and time <= end:
                self.entities_in.append(entity)

        #If it was not added (no match), add it to the "out" list
        if (not self.entities_in) or self.entities_in[-1] != entity:
            self.entities_out.append(entity)
        
    def finalize(self):
        #If discard is true, send the entities whose tag values did not match
        if self.discard:
            while self.entities_out:
                entity = self.entities_out.pop(0)
                self.send(entity)

        #If discard is false, send the entities whose tag values did match
        else:
            while self.entities_in:
                entity = self.entities_in.pop(0)
                self.send(entity)

class filter_btwn_events(filtering.Filter):
    """Filters +/- events between given start and end events."""

    expected_parameters = {
        "start_event" : {
            "types" : "string",
            "doc" : "Start event for filtering",
            "default" : "-"
        },
        "end_event" : {
            "types" : "string",
            "doc" : "End event for filtering",
            "default" : "-"
        },
        "discard" : {
            "types" : "boolean",
            "doc" : "If true, filter out only events within the given interval",
            "default" : False
        }
    }

    def initialize(self):

        self.switch = 0

        if self.params["start_event"] != "-":
            self.start_ptr = self.get_ns_pointer(self.params["start_event"])
            if self.params["end_event"] != "-":
                self.end_ptr = self.get_ns_pointer(self.params["end_event"])
        #If nothing, user error
        else:
            self.warn("No parameters given to filter_by_events.")

        self.discard = self.params["discard"]
        
    
    def process(self, entity):

        #If inverted, send all events not between start and end events
        if self.discard:
            #If we have not come across the start event yet, check if we have found it
            if self.switch == 0:
                if entity.get_cid() == self.start_ptr.get_cid():
                    #Set switch to 1, and stop sending entities
                    self.switch = 1
                else:
                    #If still not start event, output entity
                    self.send(entity)
            #If switch = 1, check if it is end event and do not send entities
            elif self.switch == 1:
                if entity.get_cid() == self.end_ptr.get_cid():
                    #If it is end event, turn switch back for the rest of the datastream
                    self.switch == 2
            else:
                self.send(entity)

        #If not inverted, send all events between start and end events
        else:
            #If we haven't come across start event yet, check if we have found it
            if self.switch == 0:
                if entity.get_cid() == self.start_ptr.get_cid():
                    #If we have, set switch to 1 and begin sending events
                    self.switch = 1
                    self.send(entity)
                else:
                    return
            elif self.switch == 1:
                #If we have found the end event, turn the switch off and send the final event
                if entity.get_cid() == self.end_ptr.get_cid():
                    self.switch = 2
                self.send(entity)
            else:
                #switch is 2, send no more events
                return
                    
class filter_by_interval(filtering.Filter):
    """Filters +/- entities inside a given interval."""
    
    #I have tried to make this capable of filtering on multiple intervals.
    #However, because of the fact that intervals can be placed anywhere, while
    #referencing any time (including times before it), we must filter the entities
    #after discovering the intervals of time.
    
    expected_parameters = {
        "interval" : {
            "types" : "string",
            "doc" : "Interval to filter by",
            "default" : "-"
        },
        "discard" : {
            "types" : "boolean",
            "doc" : "If true, filter out only events within the given interval",
            "default" : False
        }
    }

    def initialize(self):
        self.int_ptr = self.get_ns_pointer(self.params["interval"])
        self.discard = self.params["discard"]
        self.entities = []
        self.times = {}

    def process(self, entity):
        #If the entity is the inverval entity
        if self.int_ptr.get_cid() == entity.get_cid():
            #Get the start and end times for filtering
            self.times[entity.get_start_time("tsc").get_value()] = entity.get_end_time("tsc").get_value()
        #Else, append to entities list 
        else:
            self.entities.append(entity)

    def finalize(self):
        
        #If discard, filter out events within the intervals
        if self.discard:
            for entity in self.entities:
                for start, end in self.times.iteritems():
                    if entity.get_tsc() < start or entity.get_tsc() > end:
                        if self.int_ptr.get_cid() != entity.get_cid():
                            self.send_output("default", entity)
                            break
        #If not discard, only keep entities within the intervals
        else:
            for entity in self.entities:
                for start, end in self.times.iteritems():
                    if entity.get_tsc() >= start and entity.get_tsc() <= end:
                        if self.int_ptr.get_cid() != entity.get_cid():
                            self.send_output("default", entity)
                            break
                
class filter_by_machine(filtering.Filter):
    """Filters +/- entities processed on a specific machine."""

    expected_parameters = {
        "machine" : {
            "types" : "string",
            "doc" : "Machine to filter by",
            "required" : True
        },
        "discard" : {
            "types" : "boolean",
            "doc" : "If true, filter out only events that occured on this machine",
            "default" : False
        }
    }

    def initialize(self):
        self.machine = self.params["machine"]
        self.discard = self.params["discard"]

    def process(self, entity):
    
        #If discard, send all events that did NOT occur on this machine
        if self.discard:
            if entity.get_machine() != self.machine:
                self.send(entity)    
        #Else, send only those that were on this machine
        else:
            if entity.get_machine() == self.machine:
                self.send(entity)    

    
        
class sink(filtering.Filter):
    """Does not send any information further in the pipeline."""

    def process(self, entity):
        pass

class null(filtering.Filter):
    """Does nothing to the datastream; merely passes it along."""

    def process(self, entity):
        self.send(entity)

class TSC_conversion(filtering.Filter):
    """Converts TSC-based timestamps to nanoseconds, using data from clock
    administrative events. The filter will keep track of tsc-to-nanosecond 
    correspondence for multiple machines."""

    #Unfinished

    expected_parameters = {
        "redo_clock" : {
            "types" : "boolean",
            "doc" : "Whether to recompute timestamps for entities that already have a nanosecond value",
            "default" : False
        },
        "consume" : {
            "types" : "boolean",
            "doc" : "Whether it should consume clock administrative events",
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

class extra_data(filtering.Filter):
    """Prints out extra data of a list of events in a neat order."""
    #Work in progress
    #I need some binary files with extra data events to test this
    
    expected_parameters = {
        "output" : {
            "types" : "string",
            "doc" : "Output file to send narration text",
            "default" : "-"
        },
        "events" : {
            "types" : "list",
            "doc" : "List of events to count",
            "listdef" : {
                "types" : "string"
            },
            "default" : []
        },
    }
    
    def initialize(self):
        pass
    
    def process(self, entity):
        if entity.get_extra_data() != None:
            print entity.get_extra_data()
        
    def finalize(self):
        pass

class narrate(filtering.Filter):
    """Outputs string representation of the datastream to a file."""
    #Unfinished with regards to histogram

    expected_parameters = {
        "output" : {
            "types" : "string",
            "doc" : "Output file to send narration text",
            "default" : "-"
        },
        "divisor" : {
            "types" : "real",
             "doc" : "Value to divide converted timestamps by",
             "default" : 1
        },
        "line_every_n_us" : { 
            "types" : "integer",
            "doc" : "place a line every n microseconds",
            "default" : 0 
        },
        "print_extra_data" : {
            "types" : "boolean",
            "doc" : "Print extra data associated with events",
            "default" : False
        },
        "print_description" : {
            "types" : "boolean",
            "doc" : "Print description associated with events",
            "default" : True
        },
        "ignore_time" : {
            "types" : "boolean",
            "doc" : "Ignore all time related operations",
            "default" : False
        },
        "absolute_time" : {
            "types" : "boolean",
            "doc" : "Format timestamps as time-of-day",
            "default" : False
        },
        "show_admin" : {
            "types" : "boolean",
            "doc" : "Show admin events",
            "default" : False
        }
    }

    etypemap = {
        namespaces.INTERVALTYPE : "I",
        namespaces.COUNTERTYPE  : "C",
        namespaces.OBJECTTYPE   : "O",
        namespaces.HISTOGRAMTYPE: "H",
        namespaces.EVENTTYPE    : "E"
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

        #Accumulate data regarding entity in a string, linestr, and output it to the file
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

    pass
        

class count(filtering.Filter):
    """Counts the number of times certain events occur."""

    expected_parameters = {
        "events" : {
            "types" : "list",
            "doc" : "List of events to count. If empty, count total number of \
                     entities.",
            "listdef" : {
                "types" : "string"
            },
            "default" : []
        },
        "output" : {
            "types" : "string",
            "doc" : "Output file to send count information",
            "default" : "-",
        },    
    }
    

    def initialize(self):
        self.event_ptrs = {}
        
        self.count = 0

        if self.params["events"] == []:
            self.count_all = True
        else:
            self.count_all = False
        
        #Create a list of event namespace pointers
        for event in self.params["events"]:
            self.event_ptrs[self.get_ns_pointer(event)] = [0, event]

        if self.params["output"] == "-":
            self.outfile = sys.stdout
        else:
            self.outfile = open(self.params["output"], "w")


    def process(self, entity):
        self.count = self.count + 1
        for event in self.event_ptrs:
            if entity.get_cid() == event.get_cid():
                #If it is a match, increment count
                self.event_ptrs[event][0] = self.event_ptrs[event][0] + 1
        self.send(entity)
                

    def finalize(self):
    
        if self.count_all == False:
            #Output count of each event 
            for event in self.event_ptrs:
                num = self.event_ptrs[event][0]
                linestr = "Event " + str(self.event_ptrs[event][1])
                linestr = linestr + " occurred " + `num`+ " times." + "\n"
                self.outfile.write(linestr)
        else:
            linestr = "There were " + `self.count` + " entities in the pipeline: " + `self.get_pipeline().get_name()` + ".\n"
            self.outfile.write(linestr)
            

        #Close output file
        if self.outfile != sys.stdout:
            self.outfile.close()
            

        
        

        
            
