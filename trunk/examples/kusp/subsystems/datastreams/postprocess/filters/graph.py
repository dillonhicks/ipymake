""" graph.py



"""
#FIXME: Make naming of classes/function/etc follow pythonic conventions.
#            Classes should have names with capital letters and camel case.
#                I.E.: Interval_histogram -> IntervalHistogram
#            Function names should have names starting with a lower class 
#            and should follow the convention of  verb-noun.
#                I.E: 

from datastreams.postprocess import filtering, entities
import tempfile
import os
import math

#########################################################
#          Utility Functions                                                                        #
#########################################################    

def printfile(filename):
    f = open(filename)
    for l in f.readlines():
        print l 


def gnuplot_debug(cmdfile, datafile):
    print "Command file:"
    printfile(cmdfile)
    print "\nData File:"
    printfile(datafile)
    print
    
#########################################################


#########################################################
#                CLOCKSYNC FILTER                                                                     #
#########################################################
#
#FIXME.WILL: The global timeline and  clocksync related filters should go in 
#                    separate filters from graphing.py. 
#
class clksync(filtering.Filter):
    expected_parameters = {
        "name_prefix" : {
            "types" : "string",
            "doc" : "prepend to graph filenames",
            "default" : "clksync"
        }
    }

    process_admin = True
    
    def initialize(self):
        self.time_evt = self.get_ns_pointer("DSTREAM_ADMIN_FAM/TIME_STATE")
        self.offset_evt = self.get_ns_pointer("CLKSYNC/ADJUST")
        self.raw_offset_evt = self.get_ns_pointer("CLKSYNC/ADJUSTRAW")

        self.freqs = {}
        self.offsets = {}
        self.raw_offsets = {}
        self.reg_index = -1
        self.raw_index = -1
        self.not_used = 0

    
    def process(self, entity):
        machine = entity.get_machine()
        if machine not in self.freqs:
            self.freqs[machine] = []
            self.offsets[machine] = []
            self.raw_offsets[machine] = []


        if entity.get_cid() == self.time_evt.get_cid():
            data = (entity.get_nanoseconds(), entity.get_extra_data()["tsckhz"])
            self.freqs[machine].append(data)
        elif entity.get_cid() == self.offset_evt.get_cid():
            data = (entity.get_nanoseconds(), entity.get_extra_data() * 10**6)
            self.offsets[machine].append(data)
        elif entity.get_cid() == self.raw_offset_evt.get_cid():
            data = (entity.get_nanoseconds(), entity.get_extra_data() * 10**6)
            self.raw_offsets[machine].append(data)

        self.send(entity)

    #Leaving this in to make it easy to revert to a graph that only displays the offset applied
    #def make_graph(self, machine, freqs, offsets):
    def make_graph(self, machine, freqs, offsets, raw_offsets):
        
        if not freqs:
            return

        
        cmdfd, cmd_filename = tempfile.mkstemp(text=True)
        data1fd, data1_filename = tempfile.mkstemp(text=True)
        data2fd, data2_filename = tempfile.mkstemp(text=True)
        data3fd, data3_filename = tempfile.mkstemp(text=True)
        
        cmd = os.fdopen(cmdfd, "w")
        data1 = os.fdopen(data1fd, "w")
        data2 = os.fdopen(data2fd, "w")
        data3 = os.fdopen(data3fd, "w")
        
        
        zerotime = freqs[0][0]
        zerofreq = freqs[0][1]

        minfreq = zerofreq
        maxfreq = zerofreq
        for x, y in freqs:
            if y < minfreq:
                minfreq = y
            if y > maxfreq:
                maxfreq = y

        minfreq = minfreq - 1
        maxfreq = maxfreq + 1


        
        cmd.write("set terminal postscript landscape enhanced color\n")
        cmd.write('set autoscale\n')
        
        cmd.write('set y2range ['+`minfreq - zerofreq`+":"+`maxfreq - zerofreq`+"]\n")
        cmd.write('set xlabel "Time (seconds)"\n')
        cmd.write('set ylabel "Offset Applied (us)"\n')
        cmd.write('set y2label "CPU Frequency Change (KHz)"\n')
        cmd.write('set title "CLKSYNC for '+machine+'"\n')
        cmd.write('set y2tics\n')


        # we want time-of-day on the x-axis
        #cmd.write('set xdata time\n')
        #cmd.write('set timefmt "%s"\n')
        #cmd.write('set format x "%H:%M:%S"\n')
        
        cmd.write('set ytics nomirror\n')    
        cmd.write('set output "'+self.params["name_prefix"] + "_" + machine + '.ps"\n')

    
        #Leaving this in to make it easy to revert to a graph that only displays the offset applied
        #cmd.write('plot "%s" using 1:2 title "Frequency" axes x1y2 with lines, \
        #        "%s" using 1:2 title "Offset Applied" with points' %(data1_filename, data2_filename))

        cmd.write('plot "%s" using 1:2 title "Frequency" axes x1y2 with lines, \
                "%s" using 1:2 title "Offset Applied" with points, \
                "%s" using 1:2 title "Raw Offset" with points' %(data1_filename, data2_filename, data3_filename))



        for x, y in freqs:
            data1.write(`float(x - zerotime) / 10**9`+" "+`y - zerofreq`+"\n")
        for x, y in offsets:
            data2.write(`float(x - zerotime) / 10**9`+" "+`y`+"\n")
        for x, y in raw_offsets:
            data3.write(`float(x - zerotime) / 10**9`+" "+`y`+"\n")

        data1.close()
        data2.close()
        data3.close()
        cmd.close()
        # ok, run gnuplot now
        self.info("Plotting CLKSYNC graph for " + machine)
        pid = os.fork()

        if pid == 0:
            os.execlp("gnuplot","gnuplot", cmd_filename)
        os.waitpid(pid, 0)
    
        #gnuplot_debug(cmd_filename, data1_filename)

        os.remove(cmd_filename)
        os.remove(data1_filename)
        os.remove(data2_filename)
        os.remove(data3_filename)
    
    def finalize(self):
        for machine in self.freqs:
            self.make_graph(machine, self.freqs[machine], 
                            self.offsets[machine][1:], self.raw_offsets[machine][1:])
            #Leaving this in to make it easy to revert to a graph that only displays the offset applied
            #self.make_graph(machine, self.freqs[machine], self.offsets[machine][1:])
        
#########################################################




#########################################################
#                  Interval Histogram                                                                          #
#########################################################
#
#FIXME: Combine with the conversion.interval_to_histogram.
#FIXME: Replace self.vals with   something similar to 
#     "hist = entities.Histogram(0, None, mn, mx, self.params["buckets"]) (LINE 229)
#
class interval_histogram(filtering.Filter):
    """ This filter takes as input a series of intervals and distributes them to the buckets of the 
    histogram. This depends on the setting of the histogram which determines the range of the 
    histogram as a whole, the number of buckets, and thus the range of each bucket. Note that 
    in recognition of the fact that experimental data often falls outside the anticipated range, the
    histograms always have an underflow bucket, overflow bucket,  and accumulative stats that
    include maximum value and minimum value. 
    
    NOTE: There is also an interval_to_histogram filter in conversion.py which produces a 
        histogram datastream entity class instead of a gnuplot graph. The combination of the 
        two with some additional parameters seems desirable. 
    """
    expected_parameters = {
        "interval" : {
            "types" : "string",
            "doc" : "Family/event name of histogram to get data from.",
            "required" : True,
        },
        "divisor" : {
            "types" : "real",
            "doc" : "Value by which to divide data.",
            "default" : 1.0,
        },
        "xticks" : {
            "types" : "integer",
            "doc" : "Number of tick marks on x-axis.",
            "default" : 10,
        },
        "title" : {
            "types" : "string",
            "doc" : "The title of the graph.",
            "required" : True,
        },
        "xaxis_label" : {
            "types" : "string",
            "doc" : "Label for the x-axis.",
            "required" : True,
        },
        "yaxis_label" : {
            "types" : "string",
            "doc" : "Label for y axis",
            "default" : "Occurrences",
        },
        "filename" : {
            "types" : "string",
            "doc" : "base filename for graph",
        },
        "yaxis_log" : {
            "types" : "boolean",
            "default" : False,
            "doc" : "If true, the scale of the y-axis will be logarithmic."
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

    }

    def initialize(self):
        self.interval_ptr = self.get_ns_pointer(self.params["interval"])

        if "filename" not in self.params:
            self.params["filename"] = self.params["interval"].replace("/","-")
        
        if not self.params["filename"].endswith(".ps"):
            self.params["filename"] = self.params["filename"] + ".ps"

        self.vals = []


    
    def process(self, entity):
        if entity.get_cid() != self.interval_ptr.get_cid():
            self.send_output("default", entity)
            return

        d = entity.get_duration()
        self.vals.append(d)
        self.send_output("default", entity)

    def finalize(self):

        if len(self.vals) < 2:
            self.warn("Not enough matching intervals found (only 1 or 0 found)")
            return

        self.info(`len(self.vals)` + " intervals converted into histogram")

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


        hist = entities.Histogram(0, None,
                mn, mx, self.params["buckets"])

        for v in self.vals:
            hist.add_value(v)

        self.vals = []


        params = self.params
        divisor = self.params["divisor"]

        cmdfd, cmd_filename = tempfile.mkstemp(text=True)
        datafd, data_filename = tempfile.mkstemp(text=True)

        cmd = os.fdopen(cmdfd, "w")
        data = os.fdopen(datafd, "w")
        
        cmd.write("set terminal postscript landscape enhanced color\n")
        cmd.write('set xlabel "'+params["xaxis_label"]+'"\n')
        cmd.write('set title "'+params["title"]+'"\n')
        cmd.write('set boxwidth '+`(hist.get_bucket_range()/divisor)`+"\n")
        cmd.write('set autoscale\n')

        ubound = hist.get_upperbound() / divisor
        lbound = hist.get_lowerbound() / divisor

        
        # write x tick parameters
        cmd.write('set xtics (')
        xticks = params["xticks"]
        fullrange = ubound - lbound
        xtick_range = float(fullrange) / float(xticks)
        for i in range(xticks):
            xtick_num = lbound + i*xtick_range
            cmd.write(("%.2f" % xtick_num) + ",")
        cmd.write(("%.2f" % ubound) + ")\n")

        
        # write y label parameters
        if params["yaxis_log"]:
            cmd.write("set nologscale; set logscale y\n")
            # Set the y axis to start from a value less than 1 so that
            # buckets with value 1 are visible
            cmd.write("set yrange [0.7:]\n")

            cmd.write("set ylabel \"%s <log scale>\"\n"%(params["yaxis_label"]))
        else:
            cmd.write("set ylabel \"%s\"\n"%(params["yaxis_label"]))

        cmd.write('set output "'+self.params["filename"]+'"\n')

        
        cmd.write("set key title \"Min Value=%3.1f\\nMax Val=%3.1f\\nUnderflow=%d,Overflow=%d\\nAvg=%5.3f\"\n"%((hist.get_min_value() / divisor), 
                 (hist.get_max_value() / divisor), 
                 hist.get_underflow(),
                 hist.get_overflow(),
                 (hist.get_mean() / divisor)))
        cmd.write("plot '%s'  using (($1+$2)/2):3 title \"Total values : %s\" with boxes\n"%(data_filename,hist.get_count()))

        # write data file
        for i in range(hist.get_num_buckets()):
            mn, mx = hist.get_bucket_range(i)
            mn = mn / divisor
            mx = mx / divisor
            v = hist.get_bucket(i)
            data.write(`mn`+ " " +`mx`+" "+`v`+"\n")

        cmd.close()
        data.close()
        
        self.info("Plotting histogram graph for " + self.params["interval"])


        # ok, run gnuplot now
        pid = os.fork()

        if pid == 0:
            os.execlp("gnuplot","gnuplot", cmd_filename)
        os.waitpid(pid, 0)
        
        os.remove(cmd_filename)
        os.remove(data_filename)
    pass
#########################################################



#########################################################
#                                                Interval Histogram Tagged                                                             #
#########################################################
class interval_histogram_tagged(interval_histogram):
    """ This filter takes a set of Interval Entities with associated tag values.
    The tag values serve to divide the Interval Entities into separate sets.
    This filter will create a separate histogram for each of the sets distinguished
    by tag value.
    """
    def __init__(self, params):
        #hack to 'inherit' parameters
        interval_histogram.__init__(self, params)

    def initialize(self):
        self.interval_ptr = self.get_ns_pointer(self.params["interval"])

        if "filename" not in self.params:
            self.params["filename"] = self.params["interval"].replace("/","-")

        self.dict = {}
        self.filename = self.params["filename"]
        self.title = self.params["title"]

    def process(self, entity):
        if entity.get_cid() != self.interval_ptr.get_cid():
            self.send_output("default", entity)
            return

        d = entity.get_duration()
        tag = entity.get_tag()

        if self.dict.has_key(tag):
            self.dict[tag].append(d)
        else:
            self.dict[tag] = []
            self.dict[tag].append(d)

        self.send_output("default", entity)

    def finalize(self):

        for tag in self.dict.keys():
            self.vals = self.dict[tag]
            self.params["filename"] = self.filename + `tag` + ".ps"
            self.params["title"] = self.title + " for tag " + `tag`
            interval_histogram.finalize(self)
#########################################################


#########################################################
#                                                     Interval Filter                                                                              #
#########################################################
#FIXME: Find out what this filter does and put the function in the docstring. 
class interval(filtering.Filter):
    """ It is not clear what exactly is being graphed by this
    filters and requires further investigation.
    
    DEVIN: This appears to graph on (x,y). Time of occurence 
    by duration of interval
    """
    expected_parameters = {
        "interval" : {
            "types" : "string",
            "doc" : "Source interval",
            "required" : True,
        },
        "xaxis_label" : {
            "types" : "string",
            "doc" : "label for x axis",
            "default" : "Time (seconds)",
        },
        "yaxis_label" : {
            "types" : "string",
            "doc" : "y axis label",
            "default" : "Duration (milliseconds)",
        },
        "filename" : {
            "types" : "string",
            "doc" : "base filename for graph",
        },
        "yaxis_log" : {
            "types" : "boolean",
            "default" : False,
            "doc" : "If true, y-axis will be logarithmic"
        },
        "title" : {
            "types" : "string",
            "doc" : "graph title",
            "required" : True,
        },
        "xticks" : {
            "types" : "integer",
            "doc" : "number of tick marks on x-axis",
            "default" : 10,
        },
        "divisor" : {
            "types" : "integer",
            "doc" : "amount to divide y-values by",
            "default" : 1000000,
        },
        "dots" : {
            "types" : "boolean",
            "default" : False,
            "doc" : "Use points (+ marks) or dots",
        },
        "y_min" : {
            "types" : "real",
            "doc" : "Minimum value for y-axis (default auto)"
        },
        "y_max" : {
            "types" : "real",
            "doc" : "Max value for y-axis (default auto)"
        },
        "x_min" : {
            "types" : "real",
            "doc" : "Minimum value for x-axis (default auto)"
        },
        "x_max" : {
            "types" : "real",
            "doc" : "Max value for x-axis (default auto)"
        },

    }

    def initialize(self):
        self.eptr = self.get_ns_pointer(self.params["interval"])
        if "filename" not in self.params:
            self.params["filename"] = self.params["interval"].replace("/","-")
            
        if not self.params["filename"].endswith(".ps"):
            self.params["filename"] = self.params["filename"] + ".ps"

        self.vals = []
        self.base_time = -1

    def process(self, entity):
        if entity.get_cid() != self.eptr.get_cid():
            return self.send(entity)
        
        if "title" not in self.params:
            self.params["title"] = entity.get_description()

        if self.base_time == -1:
            self.base_time = entity.get_nanoseconds()

        x = float(entity.get_nanoseconds() - self.base_time) / 1000000000
        y = entity.get_duration()

        self.vals.append((x,y))

        self.send(entity)
            
    def finalize(self):
        params = self.params
        
        # open GNUPLOT output files
        cmdfd, cmd_filename = tempfile.mkstemp(text=True)
        datafd, data_filename = tempfile.mkstemp(text=True)
        cmd = os.fdopen(cmdfd, "w")
        data = os.fdopen(datafd, "w")
        
        cmd.write("set terminal postscript landscape enhanced color\n")
        cmd.write('set xlabel "'+params["xaxis_label"]+'"\n')
        cmd.write('set title "'+params["title"]+'"\n')
        cmd.write('set autoscale\n')

        if "y_min" in self.params:
            ymin = str(self.params["y_min"])
        else:
            ymin = "*"
        if "y_max" in self.params:
            ymax = str(self.params["y_max"])
        else:
            ymax = "*"

        if "x_min" in self.params:
            xmin = str(self.params["x_min"])
        else:
            xmin = "*"
        if "x_max" in self.params:
            xmax = str(self.params["x_max"])
        else:
            xmax = "*"

        cmd.write('set xrange ['+xmin+':'+xmax+']\n')
        cmd.write('set yrange ['+ymin+':'+ymax+']\n')

        # we want time-of-day on the x-axis
        # FIXME: how can we make this show fractions of a second??
        #cmd.write('set xdata time\n')
        #cmd.write('set timefmt "%s"\n')
        #cmd.write('set format x "%H:%M:%S"\n')

        # write y label parameters
        if params["yaxis_log"]:
            cmd.write("set nologscale; set logscale y\n")
            cmd.write("set ylabel \"%s <log scale>\"\n"%(params["yaxis_label"]))
        else:
            cmd.write("set ylabel \"%s\"\n"%(params["yaxis_label"]))

        cmd.write('set output "'+self.params["filename"]+'"\n')

        cmd.write("plot '%s' using 1:2 with " %(data_filename,))


        if self.params["dots"]:
            cmd.write("dots")
        else:
            cmd.write("points")

        cmd.write("\n")
        
        for x, y in self.vals[1:]:
            y = float(y) / self.params["divisor"]

            data.write(`x`+" "+`y`+"\n")

        cmd.close()
        data.close()

        self.info("Plotting interval graph "+self.params["title"]+" for "+ self.params["interval"])

        # FIXME: Forking and execi-ng here is stupid and reproducing os.system( cmd )
        # ok, run gnuplot now
        pid = os.fork()

        if pid == 0:
            os.execlp("gnuplot","gnuplot", cmd_filename)
        os.waitpid(pid, 0)
        
        print "plots",cmd_filename,data_filename

        #os.remove(cmd_filename)
        #os.remove(data_filename)
    pass
#########################################################


#########################################################
#               Aggregate Filter                                                                      #
#########################################################
class aggregate(filtering.Filter):
    expected_parameters = {
        "event" : {
            "types" : "string",
            "doc" : "Source event. Tag is x, extra data is (y, variance)",
            "required" : True,
        },
        "xaxis_label" : {
            "types" : "string",
            "doc" : "label for x axis",
            "required" : True,
        },
        "yaxis_label" : {
            "types" : "string",
            "doc" : "Label for y axis",
            "required" : True,
        },
        "filename" : {
            "types" : "string",
            "doc" : "base filename for graph",
        },
        "yaxis_log" : {
            "types" : "boolean",
            "default" : False,
            "doc" : "If true, y-axis will be logarithmic"
        },
        "title" : {
            "types" : "string",
            "doc" : "graph title",
            "required" : False,
        },
        "xticks" : {
            "types" : "integer",
            "doc" : "number of tick marks on x-axis",
            "default" : 10,
        },
        "divisor" : {
            "types" : "integer",
            "doc" : "amount to divide y-values by",
            "default" : 1,
        }

    }

    def initialize(self):
        self.eptr = self.get_ns_pointer(self.params["event"])
        if "filename" not in self.params:
            self.params["filename"] = self.params["event"].replace("/","-")
        
        if not self.params["filename"].endswith(".ps"):
            self.params["filename"] = self.params["filename"] + ".ps"
        self.min_x = None
        self.max_x = None
        self.vals = []

    def process(self, entity):
        if entity.get_cid() != self.eptr.get_cid():
            return self.send(entity)
        
        x = entity.get_tag()

        if self.min_x == None or x < self.min_x:
            self.min_x = x
        if self.max_x == None or x > self.max_x:
            self.max_x = x

        y, v = entity.get_extra_data()

        self.vals.append((x, y, v))
        if "title" not in self.params:
            self.params["title"] = entity.get_description()
        self.send(entity)

    def finalize(self):
        params = self.params
        
        # open GNUPLOT output files
        cmdfd, cmd_filename = tempfile.mkstemp(text=True)
        datafd, data_filename = tempfile.mkstemp(text=True)
        cmd = os.fdopen(cmdfd, "w")
        data = os.fdopen(datafd, "w")
        
        cmd.write("set terminal postscript landscape enhanced color\n")
        cmd.write('set xlabel "'+params["xaxis_label"]+'"\n')
        cmd.write('set title "'+params["title"]+'"\n')
        cmd.write('set autoscale\n')


        # write x tick parameters
        cmd.write('set xtics (')
        xticks = params["xticks"]
        self.min_x = self.min_x - 10
        self.max_x = self.max_x + 10
        fullrange = self.max_x - self.min_x
        xtick_range = float(fullrange) / float(xticks)
        for i in range(xticks):
            xtick_num = self.min_x + i*xtick_range
            cmd.write(("%.2f" % xtick_num) + ",")
        cmd.write(("%.2f" % self.max_x) + ")\n")    
        cmd.write("set xrange ["+`self.min_x`+":"+`self.max_x`+"]\n")
        
        # write y label parameters
        if params["yaxis_log"]:
            cmd.write("set nologscale; set logscale y\n")
            # Set the y axis to start from a value less than 1 so that
            # buckets with value 1 are visible
            cmd.write("set yrange [0.7:]\n")

            cmd.write("set ylabel \"%s <log scale>\"\n"%(params["yaxis_label"]))
        else:
            cmd.write("set ylabel \"%s\"\n"%(params["yaxis_label"]))

        cmd.write('set output "'+self.params["filename"]+'"\n')

        cmd.write("plot '%s' with yerrorbars" %(data_filename,))

        
        for x, y, v in self.vals:
            y = y / self.params["divisor"]
            v = math.sqrt(v) / self.params["divisor"]

            data.write(`x`+" "+`y`+" "+`v`+"\n")

        cmd.close()
        data.close()

        self.info("Plotting aggregate info graph for " + self.params["event"])

        # ok, run gnuplot now
        pid = os.fork()

        if pid == 0:
            os.execlp("gnuplot","gnuplot", cmd_filename)
        os.waitpid(pid, 0)
        
        os.remove(cmd_filename)
        os.remove(data_filename)
    pass

#########################################################
        

#########################################################
#                                                       Histogram Filter                                                                       #
#########################################################
class histogram(filtering.Filter):
    expected_parameters = {
        "histogram" : {
            "types" : "string",
            "doc" : "Family/event name of histogram to get data from",
            "required" : True,
        },
        "divisor" : {
            "types" : "real",
            "doc" : "Amount to divide data by",
            "default" : 1.0,
        },
        "xticks" : {
            "types" : "integer",
            "doc" : "number of tick marks on x-axis",
            "default" : 10,
        },
        "title" : {
            "types" : "string",
            "doc" : "graph title",
            "required" : False,
        },
        "xaxis_label" : {
            "types" : "string",
            "doc" : "label for x axis, leave blank to use histogram units",
        },
        "yaxis_label" : {
            "types" : "string",
            "doc" : "Label for y axis",
            "default" : "Occurrences",
        },
        "filename" : {
            "types" : "string",
            "doc" : "base filename for graph",
        },
        "yaxis_log" : {
            "types" : "boolean",
            "default" : False,
            "doc" : "If true, y-axis will be logarithmic"
        }
    }

    def initialize(self):
        self.histptr = self.get_ns_pointer(self.params["histogram"])
        if "filename" not in self.params:
            self.params["filename"] = self.params["histogram"].replace("/","-")
        
        if not self.params["filename"].endswith(".ps"):
            self.params["filename"] = self.params["filename"] + ".ps"

        self.hists = []

    def process(self, entity):
        if entity.get_cid() == self.histptr.get_cid():
            self.hists.append(entity)
            if "title" not in self.params:
                self.params["title"] = entity.get_description()
        self.send(entity)

    def finalize(self):
        if "xaxis_label" not in self.params:
            self.params["xaxis_label"] = self.namespace[self.histptr.get_cid()].get_units()

        histname = self.params["histogram"]
        if len(self.hists) == 0:
            self.warn("Warning: no graphs created for histogram "+histname)
        elif len(self.hists) == 1:
            self.info("Creating graph "+self.params["filename"] +" for "+histname)
            self.create_graph(self.hists[0], self.params["filename"])
        else:
            i = 1
            for hist in self.hists:
                self.info("Creating graph #"+`i`+" for histogram "+histname)
                self.create_graph(hist, self.params["filename"]+"_"+`i`)
    
    
    def create_graph(self, hist, filename):
        params = self.params
        divisor = self.params["divisor"]

        cmdfd, cmd_filename = tempfile.mkstemp(text=True)
        datafd, data_filename = tempfile.mkstemp(text=True)

        cmd = os.fdopen(cmdfd, "w")
        data = os.fdopen(datafd, "w")
        
        cmd.write("set terminal postscript landscape enhanced color\n")
        cmd.write('set xlabel "'+params["xaxis_label"]+'"\n')
        cmd.write('set title "'+params["title"]+'"\n')
        cmd.write('set boxwidth '+`(hist.get_bucket_range()/divisor)`+"\n")
        cmd.write('set autoscale\n')

        ubound = hist.get_upperbound() / divisor
        lbound = hist.get_lowerbound() / divisor

        
        # write x tick parameters
        cmd.write('set xtics (')
        xticks = params["xticks"]
        fullrange = ubound - lbound
        xtick_range = float(fullrange) / float(xticks)
        for i in range(xticks):
            xtick_num = lbound + i*xtick_range
            cmd.write(("%.2f" % xtick_num) + ",")
        cmd.write(("%.2f" % ubound) + ")\n")

        
        # write y label parameters
        if params["yaxis_log"]:
            cmd.write("set nologscale; set logscale y\n")
            # Set the y axis to start from a value less than 1 so that
            # buckets with value 1 are visible
            cmd.write("set yrange [0.7:]\n")

            cmd.write("set ylabel \"%s <log scale>\"\n"%(params["yaxis_label"]))
        else:
            cmd.write("set ylabel \"%s\"\n"%(params["yaxis_label"]))

        cmd.write('set output "'+filename+'"\n')

        
        cmd.write("set key title \"Min Value=%3.1f\\nMax Val=%3.1f\\nUnderflow=%d,Overflow=%d\\nAvg=%5.3f\"\n"%((hist.get_min_value() / divisor), 
                 (hist.get_max_value() / divisor), 
                 hist.get_underflow(),
                 hist.get_overflow(),
                 (hist.get_mean() / divisor)))
        cmd.write("plot '%s'  using (($1+$2)/2):3 title \"Total values : %s\" with boxes\n"%(data_filename,hist.get_count()))

        # write data file
        for i in range(hist.get_num_buckets()):
            mn, mx = hist.get_bucket_range(i)
            mn = mn / divisor
            mx = mx / divisor
            v = hist.get_bucket(i)
            data.write(`mn`+ " " +`mx`+" "+`v`+"\n")

        cmd.close()
        data.close()
        
        self.info("Plotting histogram graph for " + self.params["histogram"])


        # ok, run gnuplot now
        pid = os.fork()
        
        # This should be replaced with os.system()
        if pid == 0:
            os.execlp("gnuplot","gnuplot", cmd_filename)
        os.waitpid(pid, 0)
        
        os.remove(cmd_filename)
        os.remove(data_filename)
    pass
#########################################################





#########################################################
#              Event Filter                                                                             #
#########################################################
class event(filtering.Filter):
    expected_parameters = {
        "event" : {
            "types" : "string",
            "doc" : "Family/event name of event to get data from",
            "required" : True,
        },
        "units" : {
            "doc" : "time units for x-axis",
            "types" : "string",
            "default" : "ns"
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
                }
            }
        }
    }



