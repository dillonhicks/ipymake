""" conversion.py

@author: Devin Turner
@summary: This module contains filters which convert one form of data stream 
entities into other forms. For example, a stream of events may be converted into
a stream of intervals as appropriate to the meaning of the events in the stream.

   
"""

#Merely added comments to original conversion.py

from datastreams.postprocess import filtering, entities
from datastreams import namespaces

class event_to_histogram(filtering.Filter):
    """Converts a stream of event entities to histograms.
    
    This filter supports creating distributions from event streams where 
    individual data elements are contained within single events. For example,
    events which record the number of bytes submitted to a write operation or
    returned by a read operation. Other examples include the size of messages
    coming into or out of network interfaces, and the size of disk I/O operations
    in device drivers. 
    
    The settings for the histogram include the upper and lower bound and the 
    number of buckets used to represent the distribution. From this information,
    the bucket size can be calculated. Conceptually, when a given entity flows
    through this filter, its data is examined to see into which bucket it falls,
    and the corresponding bucket is incremented. 
    
    In its current implementation, the raw data is accumulated in a list, and
    only when the entity stream is complete is that list of data inserted into
    the histogram and a histogram entity produced. This seems to be required for
    two reasons: (1) If the user does not know the upper and lower bounds of the
    data, or is unwilling to specify them ahead of time, then accumulating
    the entire data set in order to determine the upper and lower bounds
    and thus to configure the histogram, and (2) Because many histogram
    APIs in graphing packages assume that a vector of raw data will be 
    submitted, and it is likely that this filter was written in imitation
    of them. 
    
    Future development should probably include a variant on this filter that
    can take lower and upper bound specification and insert directly into the
    histogram without creating a copy of very large data sets internally. 
    
    """

    expected_parameters = {
        "event" : {
            "types" : "string",
            "doc" : "Family/entity name of event to get data from",
            "required" : True,
        },
        "histogram" : {
            "types" : "string",
            "doc" : "Family/entity name of histogram to output",
            "required" : True,
        },
        "data" : {
            "types" : "invocation",
            "default" : ("tag",{}),
            "invodef" : {
                "tag" : {},
                "extra_data" : {
                    "item" : {
                        "types" : "list",
                        "listdef" : {
                            "types" : "string"
                        },
                        "default" : []
                    }
                },
                "time" : {
                    "units" : {
                        "types" : "string",
                        "default" : "ns",
                    }
                }
            }
        },
        "lowerbound" : {
            "types" : "real",
            "doc" : "Lower bound of histogram. Leave blank to auto-compute",
        },
        "upperbound" : {
            "types" : "real",
            "doc" : "Upper bound of histogram. Leave blank to auto-compute",
        },
        "buckets" : {
            "types" : "integer",
            "doc" : "Number of buckets in histogram",
            "required" : True,
        },
        "consume" : {
            "types" : "boolean",
            "doc" : "Whether to delete matching entities after processing",
            "default" : False
        },
    }

    output_names = ["default", "histograms"]

    def initialize(self):
        self.vals = []
        self.datasource, self.dataparam = self.params["data"]
        self.event_ptr = self.get_ns_pointer(self.params["event"])
        self.consume = self.params["consume"]
        self.hist_spec = self.get_ns_pointer(self.params["histogram"])

    
    def process(self, entity):
        #If the this entity is not of the type we are looking for, do not filter it
        if entity.get_cid() != self.event_ptr.get_cid():
            self.send_output("default", entity)
            return

        #Checking if the event contains extra data
        if self.datasource == "tag":
            self.vals.append(entity.get_tag())
        elif self.datasource == "extra_data":
            ed = entity.get_extra_data()
            for key in self.dataparam["item"]:
                ed = ed[key]
            self.vals.append(ed)

        elif self.datasource == "time":
            self.vals.append(entity.get_log_time(self.dataparam["units"]))
        
        if not self.consume:
            self.send_output("default",entity)

    #Once we have processed all the entities, we need to convert the events we found into histograms
    def finalize(self):
        #If we found no matching events, we are done
        if not self.vals:
            self.warn("No matching entities found")
            return

        self.info(`len(self.vals)` + " events converted into histogram "+
                self.params["histogram"])

        #Configuring the histogram
        if "lowerbound" not in self.params:
            mn = min(self.vals)
        else:
            mn = self.params["lowerbound"]

        if "upperbound" not in self.params:
            mx = max(self.vals)
            # add a bit of extra headroom so max value doesn't get
            # marked as overflow
            bsize = (float(mx) - float(mn)) / self.params["buckets"]
            mx = mx + (bsize / 100)

        else:
            mx = self.params["upperbound"]

        #Creating the histogram specified by input
        hist = entities.Histogram(self.hist_spec.get_cid(), None,
                mn, mx, self.params["buckets"])

        #Add the events into the histogram
        for v in self.vals:
            hist.add_value(v)
        
        self.vals = []

        #Output the histogram
        self.send_output("histograms", hist)


class dski_event_to_interval(filtering.Filter):
    """In order to match start and end events, the normal event to interval filter
    (above) uses the tag values. However, some events do not use the tag value, 
    and so that filter will simply not work. In particular, the DSKI events use 
    the PID. Thus, this filter simply matches the start and end events by using 
    their PID values. """
    
    expected_parameters = {
        "start_event" : {
            "types" : "string",
            "doc" : "Family/event name of start event",
            "required" : True
        },
        "end_event" : {
            "types" : "string",
            "doc" : "Family/event name of end event",
            "required" : True
        },
        "interval" : {
            "types" : "string",
            "doc" : "Family/event name of interval",
            "required" : True
        },
        "consume" : {
            "types" : "boolean",
            "doc" : "Whether to delete matching entities after processing",
            "default" : False
        },
        "ignore_missing" : {
            "types" : "boolean",
            "doc" : "Ignore missing start/end events",
            "default" : False,
        },
    }
    
    def initialize(self):
        self.start_ptr = self.get_ns_pointer(self.params["start_event"])
        self.end_ptr = self.get_ns_pointer(self.params["end_event"])
        self.int_ptr = self.get_ns_pointer(self.params["interval"])
        
        self.consume = self.params["consume"]
        
        self.starts = {}
    
    def process(self, entity):
        match = False
    
        #If it is a start event, add it to the dictionary
        if entity.get_cid() == self.start_ptr.get_cid():
            self.starts[entity.get_pid()] = entity
            match = True
        
        #If it is an end event, check for a match
        if entity.get_cid() == self.end_ptr.get_cid():
            if self.starts:
                match = True
                
                pid = entity.get_pid()
                
                if pid not in self.starts:
                    if not self.params["ignore_missing"]:
                        self.warn("Event with PID " + `entity.get_pid()` + " did not have a matching start event.")
                else:
                    start_entity = self.starts[entity.get_pid()]
                    start_time = start_entity.get_log_time()
                    end_time = entity.get_log_time()
                    
                    del self.starts[pid]
                
                    interval = entities.Interval(
                            self.int_ptr.get_cid(),
                            start_time, end_time, pid)
                    self.send(interval)
            
        #If the entity is not the right one, or we are not consuming events, output it as normal
        if (not match) or (match and not self.consume):
            self.send_output("default", entity)
    
    def finalize(self):
        pass

class event_to_interval(filtering.Filter):
    """Converts event entities to intervals."""

    expected_parameters = {
        "start_event" : {
            "types" : "string",
            "doc" : "Family/event name of start event",
            "required" : True
        },
        "start_machine" : {
            "types" : "string",
            "doc" : "Machine the start event occurred on"
        },
        "end_machine" : {
            "types" : "string",
            "doc" : "Machine the end event occurred on"
        },
        "end_event" : {
            "types" : "string",
            "doc" : "Family/event name of end event",
            "required" : True
        },
        "interval" : {
            "types" : "string",
            "doc" : "Family/event name of interval",
            "required" : True
        },
        "consume" : {
            "types" : "boolean",
            "doc" : "Whether to delete matching entities after processing",
            "default" : False
        },
        "tag_match" : {
            "types" : "boolean",
            "doc" : "Reject pairs that don't have matching tags",
            "default" : True,
        },
        "ignore_missing" : {
            "types" : "boolean",
            "doc" : "Ignore missing start/end events",
            "default" : False,
        },
    }

    output_names = ["default", "intervals"]

    def initialize(self):
        self.start_ptr = self.get_ns_pointer(
            self.params["start_event"])
        self.end_ptr = self.get_ns_pointer(
            self.params["end_event"])
        self.int_ptr = self.get_ns_pointer(
            self.params["interval"])
        self.consume = self.params["consume"]
        self.mode = 0
        self.tag_check = self.params["tag_match"]
        
        self.start_time = {}
        self.reject = {}

    def process(self, event):
        match = False

        #If the entity is the start event of the interval
        if event.get_cid() == self.start_ptr.get_cid():
            match = True
    
            start_time = event.get_log_time()
            
            if self.tag_check:
                tag = event.get_tag()
            else:
                tag = 0
            
            if tag in self.reject:
                self.warn("UH OH! start event occurred after end event for tag "+`tag`)
                del self.reject[tag]

            #Checks if the event ran on the correct machine
            if "start_machine" in self.params and event.get_machine() != self.params["start_machine"]:
                match = False

            #If it did, add it to the list
            if match:
                self.start_time[tag] = start_time
    
        #If the entity is the end event of the interval 
        if event.get_cid() == self.end_ptr.get_cid():
            match = True

            end_time = event.get_log_time()

            if self.tag_check:
                tag = event.get_tag()
            else:
                tag = 0

            #Checks if the event ran on the correct machine
            if "end_machine" in self.params and event.get_machine() != self.params["end_machine"]:
                match = False

            #If it did, check if it has a corresponding start event
            if match:
                if tag not in self.start_time:
                    if not self.params["ignore_missing"]:
                        self.warn("Missing start event for tag "+`tag`)
                    self.reject[tag] = end_time
                else:
                    start_time = self.start_time[tag]
                    del self.start_time[tag]

                    #Create a corresponding interval and output it
                    i = entities.Interval(
                        self.int_ptr.get_cid(),
                        start_time, end_time, tag)
                    self.send_output("intervals", i)

        #If the entity is not the right one, or we are not consuming events, output it as normal
        if (not match) or (match and not self.consume):
            self.send_output("default", event)
        

class interval_to_histogram(filtering.Filter):
    """Converts interval entities to histograms."""

    expected_parameters = {
        "interval" : {
            "types" : "string",
            "doc" : "Family/entity name of interval to convert",
            "required" : True
        },
        "histogram" : {
            "types" : "string",
            "doc" : "Family/entity name of generated histogram",
            "required" : True,
        },
        "lowerbound" : {
            "types" : "real",
            "doc" : "Lower bound of histogram. Leave blank to auto-compute",
        },
        "upperbound" : {
            "types" : "real",
            "doc" : "Upper bound of histogram. Leave blank to auto-compute",
        },
        "buckets" : {
            "types" : "integer",
            "doc" : "Number of buckets in histogram",
            "required" : True,
        },
        "units" : {
            "types" : "string",
            "doc" : "Interval time units to use",
            "default" : "ns"
        },
        "consume" : {
            "types" : "boolean",
            "doc" : "Whether to delete intervals after processing",
            "default" : False
        }
    }

    output_names = ["default","histograms"]

    def initialize(self):
        self.vals = []
        self.interval_ptr = self.get_ns_pointer(self.params["interval"])
        self.units = self.params["units"]
        self.consume = self.params["consume_intervals"]

    def process(self, entity):
        #If entity is not the correct interval, output it and exit
        if entity.get_cid() != self.interval_ptr.get_cid():
            self.send_output("default", entity)
            return

        #Store the duration of the interval 
        d = entity.get_duration(self.units)
        self.vals.append(d)

        #If not set to consume, output the original interval
        if not self.consume:
            self.send_output("default", entity)

    #Once we have found all the intervals, create histogram and output it
    def finalize(self):
        if not self.vals:
            self.warn("No matching intervals found")
            return

        self.info(`len(self.vals)` + " intervals converted into histogram "+
                self.params["histogram"])

        #Configure the histogram
        if "lowerbound" not in self.params:
            mn = min(self.vals)
        else:
            mn = self.params["lowerbound"]

        if "upperbound" not in self.params:
            mx = max(self.vals)
            # add a bit of extra headroom so max value doesn't get
            # marked as overflow
            bsize = (float(mx) - float(mn)) / self.params["buckets"]
            mx = mx + (bsize / 100)
        else:
            mx = self.params["upperbound"]

        hist_spec = self.namespace[self.params["histogram"]]

        #Create the histogram according to specifications
        hist = entities.Histogram(hist_spec.get_id(), None,
                mn, mx, self.params["buckets"])

        #Add the duration of the intervals into the histogram
        for v in self.vals:
            hist.add_value(v)

        self.vals = []

        #Output the histogram
        self.send_output("histograms", hist)
