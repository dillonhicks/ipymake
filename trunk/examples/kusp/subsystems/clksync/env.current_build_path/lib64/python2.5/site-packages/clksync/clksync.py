import clksync_mod
from pykusp import location
import os
import math
import time
import sys
import fcntl
import struct
import array
#import stats
import random

clksync_struct_format = "illQLiP"

#from datastreams import dsui
#dsui.start("/tmp/clksync.dsui.bin", 0)


def khz2mult(tsckhz, shift):
	tmp = 1000000L << shift
	tmp = tmp + (tsckhz / 2)
	return (tmp / tsckhz)

def pack_info_struct(nfo):
	d = {
		"flags":0,
		"tv_sec":0,
		"tv_nsec":0,
		"tsc":0,
		"tsckhz":0,
		"size":0,
		"dev_name":0
	}
	d.update(nfo)

	z = struct.pack(
		clksync_struct_format,
		d["flags"],
		d["tv_sec"],
		d["tv_nsec"],
		d["tsc"],
		d["tsckhz"],
		d["size"],
		d["dev_name"])
	return z

def unpack_info_struct(s):
	z = struct.unpack(clksync_struct_format, z)
	
	r = {
		"tsc":z[3],
		"tsckhz":z[4],
		"tv_sec":z[1],
		"tv_nsec":z[2]
	}
	return r

def to_timeval(time):
	tv_nsec, tv_sec = math.modf(time)
	tv_nsec = tv_nsec * 10**9

	while (tv_nsec < 0):
		tv_sec = tv_sec - 1
		tv_nsec = tv_nsec + 10**9
	while (tv_nsec > (10**9 - 1)):
		tv_sec = tv_sec + 1
		tv_nsec = tv_nsec - 10**9
	return (long(tv_sec), long(tv_nsec))
			
#XXX: Used to collect KU_NTPDATE instrumentation
#def query_time_server(timeserver, dsui):
def query_time_server(timeserver):
	#FIXME: errors not handled
	while (1):
		#XXX: Used to collect KU_NTPDATE instrumentation
		#execfile = location.kusproot + "/bin/ku_ntpdate " + timeserver + " --dsui-output /tmp/ntpdate.dsui." + str(dsui) + ".bin"
		execfile = location.kusproot + "/bin/ku_ntpdate " + timeserver
	
		fileobj = os.popen(execfile)
		output = fileobj.read()
		fileobj.close()

		if output.startswith("server"):
			break
		else:
			print output
			print "Bad response from ku_ntpdate, retrying."
			time.sleep(1)
	
	items = output.split()
	
	retval = {
		"server" : items[1],
		"stratum" : int(items[3]),
	 	"offset" : float(items[5]),
		"tsc" : long(items[7]),
		"delay" : float(items[9]),
		"dispersion" : float(items[11])
	}

	return retval

class clksync_device:

	def __init__(self):
		self.fd = os.open("/dev/clksync",0)
		nfo = self.get_info()
		self.cur_tsckhz = nfo["tsckhz"]
	
	def __del__(self):
		os.close(self.fd)
		
	def set_frequency(self, new_tsckhz):
		
		pct_change = abs(float(self.cur_tsckhz) / float(new_tsckhz))

		old_mult = self.get_info()["mult"]

		if pct_change < 0.9 or pct_change > 1.1:
			print "Requested change in tsckhz is more than 10%, ignoring"
			return

		clksync_mod.set_freq(self.fd, new_tsckhz)
	
		print "Waiting for clocksource->mult to stabilize..."
		time.sleep(2)

		# sleep 2 seconds, to let the kernel mult value stabilize
		self.cur_tsckhz = new_tsckhz
	
	def get_frequency(self):
		return self.cur_tsckhz

	def get_info(self):
		return clksync_mod.get_info()


	def adjust_time(self, offset):
		tv_sec, tv_nsec = to_timeval(offset)
		clksync_mod.adj_time(self.fd, tv_sec, tv_nsec)

	def get_tsckhz_correction(self, drift, elapsed_tscs):
		# FIXME: I have my doubts about the math here

		#print "drift",drift,"elapsed_tscs",elapsed_tscs
		# clock cycles per second
		tsc_per_sec = (float(self.cur_tsckhz))* 1000
		#print "tsc_per_sec",tsc_per_sec
	
		# how many tscs of drift are represented by current tsckhz
		# value
		drift_in_cycles = float(drift * tsc_per_sec)

		# value to add to current tsckhz to correct it. round to nearest int
		correction = (-1 * drift_in_cycles * (tsc_per_sec / float(elapsed_tscs))) / 1000.0
		#print "correction", correction

		if correction < 0:
			correction = correction - 0.5
		else:
			correction = correction + 0.5
		correction = int(correction)

		return correction

#FIXME: This algorithm throws away offsets outside of the standard deviation
# of a window of previously applied offsets. It may need to be tested more
# thoroughly and tweaked
class clksync_analyzer:
	def __init__(self, window):
		self.window = window
		self.reset_data()

	def reset_data(self):

		self.offsets = []
		self.mean = 0.0
		self.stdev = 0.0

	def crop_data(self):

		self.offsets = self.offsets[-self.window:]

	def mean_of(self, list):

		mean = 0.0
		for item in list:
			mean = mean + item
		mean = mean / len(list)
		return mean
	
	def stdev_of(self, list):

		mean = self.mean_of(list)
		stdev = 0.0
		for item in list:
			stdev = stdev + (item - mean)**2
		stdev = stdev / len(list)
		stdev = stdev**0.5
		return stdev

	def check_offset(self, offset, time, elapsed, out_of_sync):
		
		if out_of_sync or (len(self.offsets) < self.window):

			self.offsets.append(offset)

		else:

			mean = self.mean_of(self.offsets)
			stdev = self.stdev_of(self.offsets)

			lowlim = mean - (1.5 * stdev)
			uplim = mean + (1.5 * stdev)

			if offset < lowlim:
				offset = lowlim
				self.offsets.append(offset)
				self.crop_data()

			elif offset > uplim:
				offset = uplim
				self.offsets.append(offset)
				self.crop_data()

			else:
				self.offsets.append(offset)
				self.crop_data()
		
		return offset

		
	def get_sleep_time(self):
		return 4

