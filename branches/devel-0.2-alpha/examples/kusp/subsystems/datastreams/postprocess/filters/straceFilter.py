from datastreams.postprocess import filtering, entities
from discovery.oca_definitions import *
from discovery.kernel_constants import *
from discovery.syscall_numbers import *
from ctypes import *

class straceFilter(filtering.Filter):


	def initialize(self):

		self.systemCall_ptr = self.get_ns_pointer("SYSCALL/SYSTEM_CALL")
		self.sys_tr_filter_ptr = self.get_ns_pointer("SYSCALL/SYS_TR_FILTER")
		self.sys_char_ptr = self.get_ns_pointer("SYSCALL/SYS_CHAR")
		self.sys_stat64_ptr = self.get_ns_pointer("SYSCALL/SYS_STAT")
		self.syscallNames = getNumbersToSysCallNames()

		self.charValues = {}

		self.stat64Values = {}

		self.results = []

	def process(self, entity):
		
		if entity.get_cid() == self.systemCall_ptr.get_cid():
			data = entity.get_extra_data()
		#	print "Name : ", data["name"]
		#	print "Arguments : ", data["raw_params"]
			metadata = getSyscallMetadata(data["nr"])
	
			if metadata is None:
				return

			dict = {}
			dict["sys_name"] = metadata["sys_name"]
			argValue = []
		
			for i in range(metadata["numberArgs"]):
				if metadata['argTypes'][i] is "char":
					argValue.append(self.charValues[data["nr"]][0])
					del self.charValues[data["nr"]][0]
#				elif metadata['argTypes'][i] is "struct stat64":
#					argValue.append(self.stat64Values[data["nr"]][0])
#					del self.stat64Values[data["nr"]][0]
				else:
					argValue.append(data["raw_params"][i])

			if data["nr"] in self.charValues.keys():
				del self.charValues[data["nr"]]

#			if data["nr"] in self.stat64Values.keys():
#				del self.stat64Values[data["nr"]]

			dict["arg_values"] = argValue

			self.results.append(dict)

		elif entity.get_cid() == self.sys_char_ptr.get_cid():
			data = entity.get_extra_data()
			tag =  entity.get_tag()
			
			if not tag in self.charValues.keys():
				list = []
				list.append(data)
				self.charValues[tag] = list
			else:
				list = self.charValues[tag]
				list.append(data)
				self.charValues[tag] = list

#		elif entity.get_cid() == self.sys_stat64_ptr.get_cid():
#			data = entity.get_extra_data()
#			tag =  entity.get_tag()
			
#			if not tag in self.stat64Values.keys():
#				list = []
#				list.append(data)
#				self.stat64Values[tag] = list
#			else:
#				list = self.stat64Values[tag]
#				list.append(data)
#				self.stat64Values[tag] = list

		elif entity.get_cid() == self.sys_tr_filter_ptr.get_cid():
			data = entity.get_extra_data()
#			print "Event from the Filter :", self.syscallNames[data]

	def finalize(self):

		for syscallInfo in self.results:
			counter = 0
			print syscallInfo["sys_name"],"(",
			for value in syscallInfo["arg_values"]:
				counter = counter + 1
				if counter == len(syscallInfo["arg_values"]):
					print value,
				else:
					print value,",",
			print ")"
#			print counter, len(syscallInfo["arg_values"])	

		print "System call postprocessing complete."
