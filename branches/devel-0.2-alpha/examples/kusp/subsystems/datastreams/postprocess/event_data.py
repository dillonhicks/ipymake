import array
import struct
from datastreams import namespaces
import cPickle
import socket
import copy
import sys
import imp
import zlib
import operator
import syscall

from ppexcept import *

class ExtraDataDecoder:
	def __init__(self, modnames=[]):
		selfmod = sys.modules[__name__]
		self.mdict = copy.copy(selfmod.__dict__)

		self.data_cache = {}
		self.inc_data_cache = {}

		for modname in modnames:
			self.add_local_module(modname)

	def decode_chunk(self, binary):
		format = "IIIII"
		fsize = struct.calcsize(format)

		edcbin = binary[:fsize]
		data = binary[fsize:]

		z = struct.unpack(format, edcbin)
		owner_seq, owner_cid, seq, total_len, data_len = z
		key = (owner_cid, owner_seq)
		if key not in self.inc_data_cache:
			val = {"length" : total_len, "chunks" : [], "recvd" : 0}
			self.inc_data_cache[key] = val
		else:
			val = self.inc_data_cache[key]

		val["chunks"].append((seq, data))
		val["recvd"] = val["recvd"] + data_len
		if val["recvd"] == val["length"]:
			del self.inc_data_cache[key]
			self.data_cache[key] = val


	def decode(self, edfname, binary):
		if edfname[0] == "~":
			return struct.unpack(edfname[1:], binary)
		try:
			edf = self.mdict[edfname]
		except KeyError, ke:
			print "ERROR: Undefined extra data function "+`edfname`
			return None
		return self.mdict[edfname](binary)


	def get_cached_data(self, cid, seq):
		d = self.data_cache[(cid, seq)]
		del self.data_cache[(cid, seq)]


 		length = d["length"]
 		chunks = d["chunks"]
 		# sort by first element, the sequence number
 		chunks = sorted(chunks, key=operator.itemgetter(0))
 
  		r = ""
 		for seq, data in chunks:
 			r = r + data
 			length = length - len(data)
 
 		if length != 0:
 			return None
		return r

	def has_cached_data(self, cid, seq):
		return (cid, seq) in self.data_cache.keys()

	def add_local_module(self, modname):
		try:
			if modname.endswith(".py"):
			#	print "Opening extra data module file "+`modname`
				a = open(modname)
				m = imp.load_module(modname[:-3], a, 
						modname, ('.py', 'r', imp.PY_SOURCE))
			else:
			#	print "Importing extra data module "+`modname`
				m = __import__(modname)
				components = modname.split('.')
   				for comp in components[1:]:
					m = getattr(m, comp)
		except Exception, e:
			raise ConstructionException("Invalid extra data module "+modname+": "+str(e))
		self.mdict.update(m.__dict__)

	

# primitive types
def print_string(binary):
	length = len(binary)	
	format=`length`+"s"
	string = struct.unpack(format,binary)
	string = string[0]

	return string

def print_double(binary):
	format="d"

	ids=struct.unpack(format, binary)
	value = ids[0]
	
	return value

def print_float(binary):
	format = "f"
	
	ids = struct.unpack(format, binary)
	value = ids[0]
	return value

def print_int(binary):
	format="i"
	ids=struct.unpack(format, binary)
	value = ids[0]
	
	return value

def print_unsigned_int(binary):
	format="I"

	ids=struct.unpack(format, binary)
	value = ids[0]

	return value

def print_long(binary):
	format="l"

	ids=struct.unpack(format, binary)
	retval = ids[0]
	return retval

def print_unsigned_long(binary):
	format="L"

	ids=struct.unpack(format, binary)
	value = ids[0]

	return value

def print_process_info(binary):
	format="512sI"
	ids= struct.unpack(format, binary)
	d = {
		"process_name" : ids[0].split('\x00')[0],
		"process_id"   : ids[1]
	}
	return d

def print_long_long(binary):
	ids = struct.unpack("q", binary)
	return ids[0]

def print_unsigned_long_long(binary):
	ids = struct.unpack("Q", binary)
	return ids[0]

def print_pickle(binary):
	return cPickle.loads(print_string(binary))


# administrative data

def get_namespace_fragment(binary):
	d = struct.unpack("48s48s48s48sII", binary)
	d2 = {
		"family_name" : d[0].split('\x00')[0],
		"entity_name" : d[1].split('\x00')[0],
		"desc" : d[2].split('\x00')[0],
		"edf" : d[3].split('\x00')[0],
		"type" : d[4],
		"aid" : d[5]
		}
	return d2


def get_namespace(binary):
	# skip over the uncompressed size field

	q = struct.calcsize("L")

	osize = binary[:q]
	binary = binary[q:]
	
	osize = struct.unpack("L", osize)[0]
	if osize:
		binary = zlib.decompress(binary)

	ent_fmt = "49s161s49s49s49siiPP"
	ent_len = struct.calcsize(ent_fmt)
	fam_fmt = "49s161si5iiPPPPPP"
	fam_len = struct.calcsize(fam_fmt)
	ns_fmt = "iiiPP"
	ns_len = struct.calcsize(ns_fmt)

	pos = 0

	z = struct.unpack(ns_fmt, binary[pos:pos+ns_len])
	pos = pos + ns_len
	ns = namespaces.Namespace()
	num_families = z[1]
	instance_id = z[2]

	for i in range(num_families):
		z = struct.unpack(fam_fmt, binary[pos:pos+fam_len])
		pos = pos + fam_len
		fid = z[2] #+ (instance_id << 16)

		if fid == 0:
			admin = True
		else:
			admin = False

		fam_name = z[0].strip('\x00')
		num_entities = z[8]
		for j in range(num_entities):
			z = struct.unpack(ent_fmt, binary[pos:pos+ent_len])
			pos = pos + ent_len
			etype = z[6]
			ename = z[0].strip('\x00')
			edesc = z[1].strip('\x00')
			eid = z[5]


			cid = long((instance_id << (16+3+6)) +
					(fid << (6+3)) +
					(etype << 6) +
					eid)


			if etype == 0:
				e = namespaces.EventSpec(fam_name, ename, edesc, z[2].strip('\x00'), 
						cid, admin)
			elif etype == 1:
				e = namespaces.CounterSpec(fam_name, ename, edesc, cid, admin)
			elif etype == 3:
				e = namespaces.HistogramSpec(fam_name, ename, 
						edesc, z[4].strip('\x00'), cid, admin)
			elif etype == 4:
				e = namespaces.IntervalSpec(fam_name, ename, edesc, cid, admin)
			else:
				raise Exception("unsupported entity type")
			ns.add_entity(e)

	return ns

		
	

def print_clksync_info(binary):
	format = "illQQiPIIi"
	
	z = struct.unpack(format, binary)
	
	d = {"tv_sec":z[1],
		 "tv_nsec":z[2],
		 "tsc":z[3],
		 "tsckhz":z[4],
		 "shift":z[7],
		 "mult":z[8],
		 "irq":z[9]}
    
	return d

def print_ntp_pkt_info(binary):
	format = "BBBbLLIIIIIIIIIIQQQQllQLLLI"

	# The struct holds some data at the
	# end we could care less about

	formatsize = struct.calcsize(format)
	binary = binary[:formatsize]

	z = struct.unpack(format, binary)

	d = {"start_ts" : z[16],
		"rx_ts" : z[17],
		"tx_ts" : z[18],
		"end_ts" : z[19],
		"xtime_tv_sec" : z[20],
		"xtime_tv_nsec" : z[21],
		"xtime_tsc" : z[22],
		"tsc_khz" : z[23],
		"saddr":socket.inet_ntoa(struct.pack('>L',z[24])),
		"daddr":socket.inet_ntoa(struct.pack('>L',z[25])),
		"pkt_id" : z[26]
	}

	return d

def get_counter(binary):
	format = "IiQQ"

	z = struct.unpack(format, binary)
	
	d = {
			"raw_cid" : z[0],
			"count" : z[1],
			"first_update" : z[2],
			"last_update" : z[3]
	}
	return d

def get_dscvr_info(binary):
	format = "256siiii"

	z = struct.unpack(format, binary)
	d = {
		"type" :	z[0].split('\0')[0],
		"data" :	[]
	}

	d["data"].append(z[1])
	d["data"].append(z[2])
	d["data"].append(z[3])
	d["data"].append(z[4])
	
	return d

def get_read_write_info(binary):
	format = "L32s512siii"

	z = struct.unpack(format,binary)
	d={
		"inode_id"	: z[0],
		"sys_id"	: z[1].split('\0')[0],
		"filename"	: z[2].split('\0')[0],
		"fd"		: z[3],
		"size"		: z[4],
		"return"	: z[5]
	}

	return d

def get_read_write_data(binary):
	length = len(binary)	
	format=`length`+"s"
	string = struct.unpack(format,binary)
	string = string[0].strip("\x00")

	return string

def get_dup_info(binary):
	format = "L32s512siii"

	z = struct.unpack(format, binary)
	d = {
		"inode_id"	: z[0],
		"sys_id"	: z[1].split('\0')[0],
		"filename"	: z[2].split('\0')[0],
		"old_fd"	: z[3],
		"new_fd"	: z[4],
		"mode"		: z[5]
	}

	return d

def get_pipe_info(binary):
	format = "L32s512siiHH"

	z = struct.unpack(format,binary)
	d = {
		"inode_id"	: z[0],
		"sys_id"	: z[1].split('\0')[0],
		"filename"	: z[2].split('\0')[0],
		"read_fd"	: z[3],
		"write_fd"	: z[4],
		"r_mode"	: z[5],
		"w_mode"	: z[6]
	}

	return d

def get_shmat_info(binary):
	format = "iiLL32sl"
	z = struct.unpack(format,binary)
	d = {
		"flags"		: z[0],
		"shmid"		: z[1],
		"shmaddr"	: z[2],
		"inode_id"	: z[3],
		"sys_id"	: z[4].split('\0')[0],
		"err"		: z[5],
	}
	
	return d

def get_shmdt_info(binary):
	format = "LL32si"
	z = struct.unpack(format,binary)
	d = {
		"shmaddr"	: z[0],
		"inode_id"	: z[1],
		"sys_id"	: z[2].split('\0')[0],
		"ret"		: z[3]
	}

	return d

def get_shmget_info(binary):
	format = "iIiL32si"
	z = struct.unpack(format,binary)

	d = {
		"flags"		: z[0],
		"size"		: z[1],
		"key"		: z[2],
		"inode_id"	: z[3],
		"sys_id"	: z[4].split('\0')[0],
		"ret"		: z[5]
	}

	return d

def get_open_close_info(binary):
	
	format = "L32s512siHH"
	z = struct.unpack(format,binary)
	d={
		"inode_id"	: z[0],
		"sys_id"	: z[1].split('\0')[0],
		"filename"	: z[2].split('\0')[0],
		"fd"		: z[3],
		"mode"		: z[4],
	}
	
	return d


def get_fifo_info(binary):
	format ="L32s512si"

	z = struct.unpack(format,binary)

	d= {
		"inode_id"	: z[0],
		"sys_id"	: z[1].split('\0')[0],
		"filename"	: z[2].split('\0')[0],
		"mode"		: z[3]
	}

	return d

def get_ptrace_info(binary):
	format = "llllll"

	z = struct.unpack(format, binary)

	d = {
		"request" 	: z[0],
		"pid" 		: z[1],
		"parent_pid"	: z[2],
		"addr" 		: z[3],
		"data" 		: z[4],
		"ret" 		: z[5]
	}

	return d

def get_interval(binary):
	format = "IQ"

	z = struct.unpack(format, binary)
	d = {
		"raw_cid" : z[0],
		"start_time" : z[1]
	}
	return d


# For getting information about dup and dup2 system call : Discovery purposes

#def get_dup_info(binary):
#
#	format = "iiL32s"
#
#	z = struct.unpack(format, binary)
#	d = {
#		"old_fd" : z[0],
#		"new_fd" : z[1],
#		"inode_id" : z[2],
#		"sys_id" : z[3].split('\0')[0]
#	}
#
#	return d

# for getting information about file locking and file unlocking : Discovery purposes



def get_flock_info(binary):
	format = "L32s512sIi"

	z = struct.unpack(format,binary)

	d= {
		"inode_id"	: z[0],
		"sys_id"	: z[1].split('\0')[0],
		"filename"	: z[2].split('\0')[0],
		"cmd"		: z[3],
		"fd"		: z[4]
	}

	return d


def get_histogram_group(binary):

	format = "IIiqqqqqiqQQIPIP"

	#format = "IqqqqqIiqIQQQIiiiiiiPPP"
	#format = "=iiiiiiiiiLIQQI"
	formatsize = struct.calcsize(format)

	hist_bin = binary[:formatsize]
	bucket_bin = binary[formatsize:]

	z = struct.unpack(format, hist_bin)

	d = {
			"raw_cid" : long(z[0]),
			"min_seen" : z[6],
			"max_seen" : z[7],
			"upperbound" : z[3],
			"lowerbound" : z[4],
			"range" : z[5],
			"num_buckets" : z[1],
			"num_events" : z[8],
			"sum" : z[9],
			"first_update" : z[10],
			"last_update" : z[11],
			"underflow" : z[12],
			"overflow" : z[14],
	}
	bucket_fmt = "I"*(d["num_buckets"])

	z = struct.unpack(bucket_fmt, bucket_bin)
	d["buckets"] = array.array("I", z)
	return d

def print_timespec(binary):

	format = "ll"

	#unpack data
	z = struct.unpack(format, binary)

        #get valuess
	d = {"tv_sec":z[0],
		 "tv_nsec":z[1]}

	return d


#used for balanced-pipeline dsui data structure

def print_bpdata(binary):
	format = "i20si"
	ids = struct.unpack(format, binary)
	bpdata = {
		"node_id":ids[0],
		"pl_name":ids[1].rstrip('\x00'),
		"message_id":ids[2],
	}
	return bpdata


# kernel structures

def get_netdata(binary):
	format = "HHLLLi"
	ids = struct.unpack(format, binary)
	netdata = {
		"sport"    :ids[0],
		"dport"    :ids[1],
		"sequence" :ids[2],
		"daddr"    :socket.inet_ntoa(struct.pack('>L',ids[3])),
		"saddr"    :socket.inet_ntoa(struct.pack('>L',ids[4])),
		"pid"      :ids[5],
	}
	return netdata

def get_ip_netdata(binary):
	format = "HHLLLHHHiL"
	ids = struct.unpack(format, binary)
	netdata = {
		"sport":ids[0],
		"dport":ids[1],
		"sequence":ids[2],
		"daddr":socket.inet_ntoa(struct.pack('>L',ids[3])),
		"saddr":socket.inet_ntoa(struct.pack('>L',ids[4])),
		"ip_id":ids[5],
		"frag_off":ids[6],
		"mf":(ids[7] != 0),
		"pid":ids[8],
		"addr2":socket.inet_ntoa(struct.pack('>L',ids[9])),
	}
	return netdata

def get_socket_info(binary):
	format = "HHLLLL32sL32siiii"
	ids = struct.unpack(format, binary)
	netdata = {
		"sport"    :ids[0],
		"dport"    :ids[1],
		"sequence" :ids[2],
		"daddr"    :socket.inet_ntoa(struct.pack('>L',ids[3])),
		"saddr"    :socket.inet_ntoa(struct.pack('>L',ids[4])),
		#"sun_path" :ids[5].strip('\00'),
		#"this_sk"  :ids[5],
		#"peer_sk"  :ids[6],
		"known_inode" :ids[5],
		"known_sys_id" :ids[6].strip('\x00'),
		"inode_id" :ids[7],
		"sys_id"   :ids[8].strip('\x00'),
		"fd"       :ids[9],
		"mode"     :ids[10],
		"ret"      :ids[11],
		"family"   :ids[12]
	}
	return netdata

def get_select_bits(binary):
	format = "LLLLLL"
	ids = struct.unpack(format, binary)
	data = {
		"in"      : ids[0],
		"out"     : ids[1],
		"ex"      : ids[2],
		"res_in"  : ids[3],
		"res_out" : ids[4],
		"res_ex"  : ids[5]
	}
	return data

def get_schedule_layout(binary):
	layout_format = "llll"
	layout_size = struct.calcsize(layout_format)
	pos = 0
	
	sched_layout = []

	for i in range(interval_size[0]):
		x = struct.unpack (layout_format,binary[pos:pos+layout_size])
		pos = pos + layout_size
	
		single_layout = {
			"begin_sec" : x[0],
			"begin_nsec" : x[1],
			"end_sec" : x[2],
			"end_nsec" : x[3]
		}
		sched_layout.append(single_layout)

	return sched_layout

def get_schedule_info(binary):
	sched_format = "26s34siiPll"

	sched_info = struct.unpack(sched_format,binary)

	xserver_layout = { 
		"begin_sec" : sched_info[5],
		"begin_nsec" : sched_info[6]
	}
	
	interval_size.append(sched_info[2])

	schedule_info = {
		"schedule_name" : 	sched_info[0].strip('\x00'),
		"member_name"	:	sched_info[1].strip('\x00'),
		"layout_size"	:	sched_info[2],
		"cpu"			:	sched_info[3],
		"xserver_layout":	xserver_layout
	}

	#print schedule_info

	return schedule_info

interval_size = []


def print_syscall(bin):
	format = "LLLLLLL"
	ids = struct.unpack(format, bin)

	name, func = syscall.systab[ids[0]]

	data = {
		"name" : name,
		"nr" : ids[0],
		"params" : None,
		"raw_params" : ids[1:]
	}

	#if func != None:
	#	if type(func) is list:
	#		ret = {}
	#		for i in range(len(func)):
	#			ret[func[i]] = ids[i+1]

	#		data["params"] = ret
	#	else:
	#		data = func(data)

	return data

def print_cred(bin):
	format = "ii256s"
	ids = struct.unpack(format, bin)

	data = {
		"UserId" : ids[0],
		"EUserId": ids[1],
		"Filename": ids[2]
	}

	return data
	
def print_binprm(bin):
	data = {}

	return data

def print_stat64(bin):
	format = "Q4BLIILLQ4BqLQLLLILLQ"
	ids = struct.unpack(format, bin)

	return ids
