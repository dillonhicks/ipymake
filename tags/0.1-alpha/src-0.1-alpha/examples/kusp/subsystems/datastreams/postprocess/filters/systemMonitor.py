from datastreams.postprocess import filtering, entities
from discovery.oca_definitions import *
from discovery.kernel_constants import *

# a very basic version of postprocessing. right now it just prints out 
# the pid of the process and the Image executed for the shared library discovery. 
class systemMonitor(filtering.Filter):

	def initialize(self):

		self.smon_pinfo_ptr = self.get_ns_pointer("SMON/PINFO")
		self.smon_psys_ptr = self.get_ns_pointer("SMON/PSYS")

		self.result = []

	def process(self,entity):

		dict = {}
		if entity.get_cid() == self.smon_pinfo_ptr.get_cid():
			dict = entity.get_extra_data()
		#	print "Pid of the process executed : ",entity.get_tag()
		#	print "Image Executed : ", dict
		#	print"\n"
		elif entity.get_cid() == self.smon_psys_ptr.get_cid():
			dict = entity.get_extra_data()
		 	pid = entity.get_pid()
			sysNum = entity.get_tag()
			image = dict
			record = (pid, sysNum, image)
			self.result.append(record)

	def finalize(self):

		print "System Call Information...\n"
		
		print "Pid\t\tSystemCall\t\tImage\n"

		for record in self.result:
			print record[0],"\t\t",record[1],"\t\t",record[2],"\n"

		print "finished"

