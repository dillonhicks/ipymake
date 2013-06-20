"""Filters to convert entities from one type into another"""

from datastreams.postprocess import filtering, entities

#########################################################
#         Event To Histogram Filter                     #
#########################################################    
class event_to_histogram(filtering.Filter):
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
        if entity.get_cid() != self.event_ptr.get_cid():
            self.send_output("default", entity)
            return

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


    def finalize(self):
        if not self.vals:
            self.warn("No matching entities found")
            return

        self.info(`len(self.vals)` + " events converted into histogram "+
                self.params["histogram"])

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

        hist = entities.Histogram(self.hist_spec.get_cid(), None,
                mn, mx, self.params["buckets"])

        for v in self.vals:
            hist.add_value(v)
        
        self.vals = []

        self.send_output("histograms", hist)



#########################################################
#                                             Event To Interval Filter                                                                       #
#########################################################   
class event_to_interval(filtering.Filter):
    expected_parameters = {
        "start_event" : {
            "types" : "string",
            "doc" : "Family/event name of start event",
            "required" : True
        },
        "start_machine" : {
            "types" : "string",
        },
        "end_machine" : {
            "types" : "string",
        },
        "end_event" : {
            "types" : "string",
            "doc" : "Family/event name of end event",
            "required" : True
        },
        "interval" : {
            "types" : "string",
            "doc" : "Family/event name of end event",
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
            "default" : False,
            "doc" : "Don't complain about missing start / end events",
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

        # looking for start event
        if event.get_cid() == self.start_ptr.get_cid():
            start_time = event.get_log_time()
            
            if self.tag_check:
                tag = event.get_tag()
            else:
                tag = 0
            
            if tag in self.reject:
                self.warn("UH OH! start event occurred after end event for tag "+`tag`)
                del self.reject[tag]
            match = True

            if "start_machine" in self.params and event.get_machine() != self.params["start_machine"]:
                match = False

            if match:
                self.start_time[tag] = start_time
    
        # looking for end event
        if event.get_cid() == self.end_ptr.get_cid():
            end_time = event.get_log_time()
                
            match = True
            if self.tag_check:
                tag = event.get_tag()
            else:
                tag = 0

            if "end_machine" in self.params and event.get_machine() != self.params["end_machine"]:
                match = False

            if match:
                if tag not in self.start_time:
                    if not self.params["ignore_missing"]:
                        self.warn("Missing start event for tag "+`tag`)
                    self.reject[tag] = end_time
                else:
                    start_time = self.start_time[tag]
                    del self.start_time[tag]
                    i = entities.Interval(
                        self.int_ptr.get_cid(),
                        start_time, end_time, tag)
                    self.send_output("intervals", i)
        
        if (not match) or (match and not self.consume):
            self.send_output("default", event)

#########################################################
#                                      Interval To Histogram Filter                                                                       #
#########################################################        
#FIXME: Combine with the graph.interval_histogram.

#FIXME: Replace self.vals with   something similar to 
#     "hist = entities.Histogram(0, None, mn, mx, self.params["buckets"]) (LINE 323).
#     This is possibly creating a more overhead than needed by making two data 
#     structures that contain the same data. 
class interval_to_histogram(filtering.Filter):
    """ This interval to histogram takes a series of interval 
    entities and places them into a Histogram Entity instance.  Note 
    that there is an interval to histogram filter in graph.py that takes 
    a series of intervals as input and produces a gnuplot graph. 
    Probably these two filters could be combined with the addition 
    of some parameters.
    """
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
        "consume_intervals" : {
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
        if entity.get_cid() != self.interval_ptr.get_cid():
            self.send_output("default", entity)
            return

        d = entity.get_duration(self.units)
        self.vals.append(d)
        if not self.consume:
            self.send_output("default", entity)

    def finalize(self):
        if not self.vals:
            self.warn("No matching intervals found")
            return

        self.info(`len(self.vals)` + " intervals converted into histogram "+
                self.params["histogram"])

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

        hist = entities.Histogram(hist_spec.get_id(), None,
                mn, mx, self.params["buckets"])

        for v in self.vals:
            hist.add_value(v)

        self.vals = []

        self.send_output("histograms", hist)

#########################################################        
            
