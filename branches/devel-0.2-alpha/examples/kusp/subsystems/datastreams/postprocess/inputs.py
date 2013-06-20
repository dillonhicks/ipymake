import entities
from datastreams import namespaces
#from datastreams import dsui
import struct
import event_data
import cPickle
from ppexcept import *
import os
from select import poll, POLLIN
import time

magic_format = "I"
magic_size = struct.calcsize(magic_format)

rawmagic = 0x1abcdef1
raw2magic = 0x2abcdef2
picklemagic = 0xdeadbeef
xmlmagic = struct.unpack(magic_format, struct.pack("=4s","<!--"))


class InputSource:
    def __init__(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def get_dependency(self):
        return None

    def open(self):
        raise Exception("abstract")

    def read(self):
        raise Exception("abstract")

    def close(self):
        raise Exception("abstract")

    def seek(self, num):
        raise InputSourceException("Input source does not support seeking")

    def get_progress(self):
        return 0.0

def determine_file_type(filename):
    f = open(filename, "rb")

    bin = f.read(magic_size);
    f.close()

    magic = struct.unpack(magic_format, bin)[0]

    if magic == rawmagic:
        return "raw"
    if magic == raw2magic:
        return "raw2"
    elif magic == picklemagic:
        return "pickle"
    elif magic == xmlmagic:
        return "xml"
    else:
        raise PostprocessException("Unable to determine file type of file "+filename)


class RawInputSource(InputSource):
    """reads raw binary files written by DSKI/DSUI. hackish but works."""
    def __init__(self, filename, local_edf_modules, infile=None, endless=False):
        InputSource.__init__(self, filename)
        self.local_ns = namespaces.get_admin_ns()
        self.ns_event = self.local_ns["DSTREAM_ADMIN_FAM/NAMESPACE"].get_id()
        self.histevent = self.local_ns["DSTREAM_ADMIN_FAM/EVENT_HISTOGRAM"].get_id()
        self.counterevent = self.local_ns["DSTREAM_ADMIN_FAM/EVENT_COUNTER"].get_id()
        self.intervalevent = self.local_ns["DSTREAM_ADMIN_FAM/EVENT_INTERVAL"].get_id()
        self.ns_frag_event = self.local_ns["DSTREAM_ADMIN_FAM/NAMESPACE_FRAGMENT"].get_id()
        self.chunkevent = self.local_ns["DSTREAM_ADMIN_FAM/DATA_CHUNK"].get_id()
        self.formats = {
            "event" : "QIIIIi",
        }
        self.sizes = {}
        for k, v in self.formats.iteritems():
            self.sizes[k] = struct.calcsize(v)
        self.filename = filename
        self.decoder = event_data.ExtraDataDecoder(local_edf_modules)
        self.header = None
        self.infile = infile
        self.position = 0
        self.totalsize = None
        self.waiting_chunks = []
        self.endless = endless

    def get_progress(self):
        if self.totalsize:
            return (float(self.position) / float(self.totalsize)) * 100
        else:
            return 0.0

    def declare_entity(self, fname, ename, desc, edf, etype, aid):
        
        ns = namespaces.Namespace()
        eid = 0
        
        if etype == namespaces.EVENTTYPE:
            espec = namespaces.EventSpec(fname, ename, desc, edf, aid)
        elif etype == namespaces.COUNTERTYPE:
            espec = namespaces.CounterSpec(fname, ename, desc, aid)
        elif etype == namespaces.INTERVALTYPE:
            espec = namespaces.IntervalSpec(fname, ename, desc, aid)
        elif etype == namespaces.HISTOGRAMTYPE:
            espec = namespaces.HistogramSpec(fname, ename, desc, edf, aid)
	elif etype == namespaces.INTERNALEVENTTYPE:
	    espec = namespaces.InternalEventSpec(fname, ename, desc, edf, aid)

        ns.add_entity(espec)

        # merge this created namespace (that just defines one entity)
        # with our local namespace, which will give us proper id numbers
        # for family and entity

        conf, new_ns = self.local_ns.merge(ns)

        return new_ns

                    
    def read(self):
        retval = entities.PipelineEnd()
        try:
            retval = self.__read()
        except PostprocessException, e:
            print self.name, "file corruption: ", e
            
        return retval
    
    def __read(self):
        #The name of the machine the data was collected on
        machine = self.header["hostname"]

        #dsui.event("INPUTS","RAW_INPUT_READ");
        while True:
            for evt in self.waiting_chunks:
                cid = evt.get_cid()
                seq = evt.get_sequence()
                if self.decoder.has_cached_data(cid, seq):
                    self.waiting_chunks.remove(evt)
                    evt.extra_data = self.decoder.get_cached_data(cid, seq)
                    return evt

            event_binary = self.infile_read(self.sizes["event"])
            if len(event_binary) < self.sizes["event"]:
                # end of stream reached
                if self.endless:
                    # XXX hack for online postprocessing
                    continue
                else:
                    return entities.PipelineEnd()

            event_record = struct.unpack(self.formats["event"],
                event_binary)
            tsc, seq, aid, tag, pid, datalen = event_record
            
           # print "decoded record", event_record, long(aid)
            try:
                cid = long(aid)
                event_spec = self.local_ns[cid]
            except KeyError:
               print self.local_ns.to_configfile()
               print self.local_ns.keys()
               raise InputSourceException("Unknown composite id "+
                        `cid`)

            timeval = {
                "tsc" : entities.TimeMeasurement("tsc", tsc,
                    machine, 0, 0),
                "sequence" : entities.TimeMeasurement("sequence",
                    seq, self.filename, 0, 0)
            }

            edf_name = event_spec.get_edf()

            wait_flag = False
            if datalen > 0:
                extra_data_binary = self.infile_read(datalen)
            elif edf_name and self.decoder.has_cached_data(cid, seq):
                extra_data_binary = self.decoder.get_cached_data(cid, seq)
            elif edf_name:
                extra_data_binary = None
                if datalen == -1:
                    wait_flag = True


            if cid == self.chunkevent:
                self.decoder.decode_chunk(extra_data_binary)
                continue
    
            if edf_name and (extra_data_binary != None):
                try:
                    extra_data = self.decoder.decode(edf_name, 
                            extra_data_binary)
                except Exception, ex:
                    print "Failed to decode extra data for",self.local_ns[cid]
                    raise
            else:
                extra_data = None


            if cid == self.counterevent:
                entity = entities.Counter(
                    extra_data["raw_cid"], 
                    timeval, 
                    extra_data["count"],
                    entities.get_tsc_measurement(
                        extra_data["first_update"],
                        machine),
                    entities.get_tsc_measurement(
                        extra_data["last_update"],
                        machine), pid)
            elif cid == self.histevent:
                entity = entities.Histogram(
                    extra_data["raw_cid"],
                    timeval,
                    extra_data["lowerbound"], extra_data["upperbound"],
                    extra_data["num_buckets"], pid)
                entity.populate(extra_data["underflow"],
                        extra_data["overflow"],
                        extra_data["sum"],
                        extra_data["num_events"],
                        extra_data["min_seen"],
                        extra_data["max_seen"],
                        extra_data["buckets"])
            elif cid == self.intervalevent:
                starttime = {
                    "tsc" : entities.TimeMeasurement("tsc", 
                        extra_data["start_time"], machine, 0, 0),
                }
                entity = entities.Interval(
                        extra_data["raw_cid"],
                        starttime, timeval, tag, pid);
            else: # event
                if cid == self.ns_frag_event:
                    ns_frag = self.declare_entity(
                        extra_data["family_name"],
                        extra_data["entity_name"],
                        extra_data["desc"],
                        extra_data["edf"],
                        extra_data["type"],
                        long(extra_data["aid"]))
                    return entities.Event(self.ns_event, timeval, tag, ns_frag, pid)
                elif cid == self.ns_event:
                    raise Exception ("your input file is too old")
                    c, new_ns = self.local_ns.merge(extra_data)
                    
                    for z in new_ns.values():
                        self.aid_index[z.get_id()] = z.get_id()
                    for old_cid, new_cid in c.items():
                        self.aid_index[old_cid] = new_cid


                entity = entities.Event(cid, timeval, tag, extra_data, pid)
            
            
            entity.namespace = self.local_ns

            if wait_flag:
                self.waiting_chunks.append(entity)
                continue

            return entity

    def open(self):
        if not self.infile:
            self.totalsize = os.stat(self.filename).st_size
            self.infile = open(self.filename, "rb")
            
        self.read_binary_header()

    def infile_read(self, size):
        self.position = self.infile.tell()
        return self.infile.read(size)

    def read_binary_header(self):
        fmt = "IIIIII80s"
        header_binary = self.infile_read(struct.calcsize(fmt))
        h = struct.unpack(fmt, header_binary);

        self.header = {
            "sz_int" : h[1],
            "sz_long" : h[2],
            "sz_short" : h[3],
            "sz_long_long" : h[4],
            "sz_ptr" : h[5],
            "hostname" : h[6].strip('\x00'),
        }

    def close(self):
        if self.waiting_chunks:
            print self.filename,"ERROR",(len(self.waiting_chunks)),"events were held back due to missing/incomplete extra data"
            for e in self.waiting_chunks:
                print e

        self.infile.close()
        pass



# used to generate unique names for socket input sources, since there
# will be multiple ones for SMP hosts
socket_dictionary = {}

class SocketRawInputSource(RawInputSource):
    def __init__(self, host, port, local_edf):
        if host not in socket_dictionary:
            socket_dictionary[host] = 0
        else:
            socket_dictionary[host] = socket_dictionary[host] + 1

        id = socket_dictionary[host]
        RawInputSource.__init__(self, `host`+"-"+`id`, local_edf)
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    def open(self):
        print "Connecting to",self.host,self.port
        self.sock.connect((self.host, self.port))
        print "Connected"
        self.infile = self.sock.makefile('r')
        read_binary_header()

    def __del__(self):
        self.close()

    def close(self):
        self.infile.close()
        self.sock.close()
        

from datastreams import dski
        
class OnlineRawInputSource(RawInputSource):

    def open(self):
        if not self.infile:
            self.totalsize = os.stat(self.filename).st_size
            self.infile = open(self.filename, "rb")
            
        
        self.pollobj = poll()
        self.pollobj.register(self.infile.fileno(), POLLIN)
        
        ctx = dski.dski_context(None)
        self.local_ns.merge(ctx.ns)
        ctx.close()

        self.header = {}

        self.header["hostname"] = "localhost"

        self.ns_sent = False

    def read(self):
        if not self.ns_sent:
            self.ns_sent = True
            return entities.Event(self.ns_event, 
                    entities.get_zero_timedict(), 
                    2337, self.local_ns)
        return RawInputSource.read(self)

    def infile_read(self, size):
        ret = self.infile.read(size)
        if not ret:
            v = self.pollobj.poll(1000)
            return self.infile.read(size)
        else:
            return ret


class PickleInputSource(InputSource):
    """reads 'cooked' binary files written by postprocess2"""
    def __init__(self, filename):
        InputSource.__init__(self, filename)
        self.filename = filename
            
    def read(self):
        try:
            e = self.unpickler.load()
        except:
            e = entities.PipelineEnd()
        return e

    def open(self):
        self.infile = open(self.filename, "rb")
        
        # skip the magic number
        self.infile.read(magic_size)

        self.unpickler = cPickle.Unpickler(self.infile)
        pass

    def close(self):
        self.infile.close()
        pass


class XMLInputSource(InputSource):
    def __init__(self, filename):
        InputSource.__init__(self, filename)
        self.filename = filename
        raise Exception("XML input unimplemented")

    def open(self):
        pass

    def close(self):
        pass

    def read(self):
        pass


class PipelineInputSource(InputSource):
    def __init__(self, pipename, outputname, queue_param, pipe_index, our_pipe):
        n = pipename+"/"+outputname+"->"+our_pipe.get_name()
        InputSource.__init__(self, n)
        
        
        self.other_pipe_name = pipename
        self.output_name = outputname
        
        self.pipe = our_pipe
        self.node = our_pipe.get_node()

        self.input_queue = None
        self.queue_param = queue_param

        self.pipe_index = pipe_index

        self.deps = None

    def get_dependency(self):
        return self.deps

    def read(self):
        e = self.input_queue.get()
        return e
    
    def close(self):
        pass

    def open(self):
        if self.node.has_pipeline(self.other_pipe_name):
            p = self.node.get_pipeline(self.other_pipe_name)
            self.input_queue = p.connect(self.get_name(), 
                    self.output_name, 
                    self.queue_param, self.pipe_index)
            self.deps = self.other_pipe_name
            return

        # do CORBA magic....
        pass


def ns_id_generator():
    v = 1
    while True:
        yield v
        v = v + 1

ns_id_gen = ns_id_generator()

class NamespaceInputSource(InputSource):
    """Used to inject user-supplied namespaces"""
    def __init__(self, ns):
                
        InputSource.__init__(self, "ns"+`ns_id_gen.next()`)

        self.local_ns = namespaces.get_admin_ns()
        self.nsevent = self.local_ns["DSTREAM_ADMIN_FAM/NAMESPACE"].get_id()
        if type(ns) is str or type(ns) is list:
            self.ns = namespaces.read_namespace_files(ns)
        else:
            v = namespaces.verify_namespace_config(ns)
            self.ns = namespaces.construct_namespace(v)
    
    def open(self):
        pass

    def close(self):
        pass

    def read(self):
        if not self.ns:
            return entities.PipelineEnd()

        e = entities.Event(self.nsevent, entities.get_zero_timedict(),
            0, self.ns)
        
        self.ns = None
        return e



        

