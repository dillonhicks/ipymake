from outputs import *
import os
import struct

"""
begin
	* the beginning of buffer information
	uint64 cycle_count
		* TSC at the beginning of the buffer
	uint64 freq
		* frequency of the CPUs at the beginning of the buffer.
end
	* the end of buffer information
	uint64 cycle_count
		* TSC at the beginning of the buffer
	uint64 freq
		* frequency of the CPUs at the end of the buffer.
uint32 lost_size
	* number of bytes of padding at the end of the buffer.
uint32 buf_size
	* size of the sub-buffer.
"""

block_header_fmt = "QQQQII"
block_header_size = struct.calcsize(block_header_fmt)

def get_block_header_bin(start, end, max, size):
	s = struct.pack(block_header,
			start, 1000000000,
			end, 1000000000,
			max - size, size)
	return s


"""
uint32 magic_number
	* 0x00D6B7ED, used to check the trace byte order vs host byte order.
uint32 arch_type
	* Architecture type of the traced machine.
uint32 arch_variant
	* Architecture variant of the traced machine. May be unused on some arch.
uint32 float_word_order
	* Byte order of floats and doubles, sometimes different from integer byte
	  order. Useful only for user space traces.
uint8 arch_size
	* Size (in bytes) of the void * on the traced machine.
uint8 major_version
	* major version of the trace.
uint8 minor_version
	* minor version of the trace.
uint8 flight_recorder
	* Is flight recorder mode activated ? If yes, data might be missing
	  (overwritten) in the trace.
uint8	has_heartbeat
	* Does this trace have heartbeat timer event activated ?
		Yes (1) -> Event header has 32 bits TSC
		No (0) -> Event header has 64 bits TSC
uint8 has_alignment
	* Is the information in this trace aligned ?
		Yes (1) -> aligned on min(arch size, atomic data size).
		No (0) -> data is packed.
uint32 freq_scale
		event time is always calculated from :
			trace_start_time + ((event_tsc - trace_start_tsc) * (freq / freq_scale))
uint64 start_freq
	* CPUs clock frequency at the beginnig of the trace.
uint64 start_tsc
	* TSC at the beginning of the trace.
uint64 start_monotonic
	* monotonically increasing time at the beginning of the trace.
		(currently not supported)
start_time
	* Real time at the beginning of the trace (as given by date, adjusted by NTP)
		This is the only time reference with the real world : the rest of the trace
		has monotonically increasing time from this point (with TSC difference and
		clock frequency).
	uint32 seconds
	uint32 nanoseconds
"""

trace_header_fmt = "IIIIBBBBBBIQQQII"

def get_trace_header_bin(start_time):
	s = struct.pack(trace_header_fmt,
			0x00D6B7ED, 0, 0, 0,
			4, 1, 0, 0, 0, 0,
			1, 1000000000, start_time, start_time,
			start_time / 1000000000, start_time % 1000000000)
	return s


"""
{ uint32 timestamp
	or
	uint64 timestamp }
	* if has_heartbeat : 32 LSB of the cycle counter at the event record time.
	* else : 64 bits complete cycle counter.
uint8 facility_id
	* Numerical ID of the facility corresponding to the event. See the facility
	  tracefile to know which facility ID matches which facility name and
		description.
uint8 event_id
	* Numerical ID of the event inside the facility.
uint16 event_size
	* Size of the variable length data that follows this header.
"""

event_header_fmt = "QBBH"

def get_event_bin(ent):
	s = struct.pack(event_header_fmt,
			ent.get_nanoseconds(),
			ent.get_fid(),
			ent.get_eid(),
			0)
	return s



def get_system_xml(fd):
	fd.write("""
<system 
 node_name="yggdrasil"
 domainname="ittc.ku.edu" 
 cpu=1
 arch_size="ILP32" 
 endian="little" 
 kernel_name="Linux" 
 kernel_release="2.4.18-686-smp" 
 kernel_version="#1 SMP Sun Apr 14 12:07:19 EST 2002"
 machine="i686" 
 processor="unknown" 
 hardware_platform="unknown"
 operating_system="Linux" 
 ltt_major_version="2"
 ltt_minor_version="0"
 ltt_block_size="100000"
>
Some comments about the system
</system>""")


class LTTOutput(OutputFilter):
	def __init__(self, pathname):
		Filter.__init__(self, {})
		self.pathname = pathname
		self.buffer = ""
		self.buffermax = 100000 - block_header_size

	def initialize(self):
		try:
			os.makedirs(self.pathname)
			os.mkdir(self.pathname + "/eventdefs")
			os.mkdir(self.pathname + "/info")
			os.mkdir(self.pathname + "/control")
		except Exception:
			print "mkdirs failed"

		self.binfile = open(self.pathname + "/cpu_0")
		self.buffer = get_trace_header_bin(0)
	
	def finalize(self):
		if self.buffer:
			self.flush()
		self.binfile.close()

	def flush(self):
		hdr = get_block_header_bin(self.blk_start,
				self.blk_end, self.buffermax, 
				len(self.buffer))
		hdr = hdr + self.buffer
		self.buffer = ""
		self.binfile.write(hdr)
		
	def process(self, entity):
		s = get_event_bin(entity)
		if len(s) + len(self.buffer) > self.buffermax:
			self.flush()
		self.buffer = self.buffer + s

		


