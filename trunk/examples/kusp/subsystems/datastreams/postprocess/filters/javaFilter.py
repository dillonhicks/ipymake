from datastreams.postprocess import filtering, entities
from discovery.oca_definitions import *
from discovery.kernel_constants import *
import re

### This Filter is used for creating observed Computation action events for DataStream
### instrumentation events coming out of the JVM 
### FIXME: Lot More work needs to be done in this filter to gather more information from the JVM
###        and the JVM has to be instrumented with some more points to collect more info.
class Javafilter(filtering.Filter):

	def initialize(self):
		"""This is the initialization function where we try to get the namespace pointers
		   for the DataStream points coming from the JVM. we also have some variables defined 
		   here which are later used in the processing of each event.
		"""
		self.java_wrapper_ptr = self.get_ns_pointer("WRAPPER/WRAPPER_START")
		self.java_vmThread_ptr = self.get_ns_pointer("JAVA/VMTHREAD")
		self.java_thread_ptr = self.get_ns_pointer("JAVA/JAVA_THREAD")
		self.java_native_thread_entry_ptr = self.get_ns_pointer("JAVA/JAVA_NATIVE_ENTRY")
		self.java_signal_thread_entry_ptr = self.get_ns_pointer("JAVA/JAVA_SIGNAL_ENTRY")
		self.java_watcher_thread_ptr = self.get_ns_pointer("JAVA/WATCHER")
		self.java_compiler_thread_entry_ptr = self.get_ns_pointer("JAVA/JAVA_COMPILER")
		self.java_main_class_ptr = self.get_ns_pointer("JAVA/JAVA_MAIN_THREAD_CALL")
		self.java_main_thread_call_ptr = self.get_ns_pointer("JAVA/JAVA_MAIN_CLASS")
		self.java_thread_call_ptr = self.get_ns_pointer("JAVA/JAVA_THREAD_CALL")
		self.java_method_call_ptr = self.get_ns_pointer("JAVA/JAVA_METHOD_NAME")
		self.java_class_call_ptr = self.get_ns_pointer("JAVA/JAVA_CLASS_NAME")
		self.java_low_mem_detector_ptr = self.get_ns_pointer("JAVA/JAVA_LOW_MEM_DETECTOR")
		self.java_thread_name_ptr = self.get_ns_pointer("JAVA/JAVA_THREAD_NAME")
		self.java_thread_gc_ptr = self.get_ns_pointer("JAVA/JAVA_GC_THREAD")
		self.java_attach_entry_ptr = self.get_ns_pointer("JAVA/JAVA_ATTACH_ENTRY")

		self.OCA_actions_ptr    = self.get_ns_pointer("OCA/ACTIONS")

		self.java_dict= {}

		self.native = 1

		self.compiler = 1

		self.signal = 1

		self.low_mem = 1

		self.gc_thread = 1

		self.java_thread_unknown = 1

		self.java_thread_dict = {}

		self.main_info = {}

		self.java_calls = {}

		self.java_call_number = 1

		self.java_attach = 1
		
		self.final_list = {}

		self.OCA_PIDS = {}

		self.numberOfReferences = 0

		self.thread_name_pids = {}


	def process(self, entity):
		"""Function is called for each event entity 
		"""
		cid = entity.get_cid()

		if cid == self.java_wrapper_ptr.get_cid():
			self.java_dict[OCA_JAVA_WRAPPER] = entity.get_tag()
			pid = entity.get_tag()
			if pid in self.OCA_PIDS.keys():
				java_wrapper_dict = self.create_OCA_dict(OCA_JAVA_WRAPPER,OCA_JAVA_WRAPPER_NAME,self.OCA_PIDS[pid])
				self.send_OCA_evt(java_wrapper_dict,entity.get_log_time())

		if cid == self.java_vmThread_ptr.get_cid():
			self.java_dict[OCA_JAVA_VM_THREAD] = entity.get_tag()
			pid = entity.get_tag()
			if pid in self.OCA_PIDS.keys():
				java_vm_dict = self.create_OCA_dict(OCA_JAVA_VM_THREAD,OCA_JAVA_VM_THREAD_NAME,self.OCA_PIDS[pid])
				self.send_OCA_evt(java_vm_dict,entity.get_log_time())

		if cid == self.java_watcher_thread_ptr.get_cid():
			self.java_dict[OCA_JAVA_WATCHER] = entity.get_tag()
			pid = entity.get_tag()
			if pid in self.OCA_PIDS.keys():
				java_watcher_dict = self.create_OCA_dict(OCA_JAVA_WATCHER,OCA_JAVA_WATCHER_NAME,self.OCA_PIDS[pid])
				self.send_OCA_evt(java_watcher_dict,entity.get_log_time())
			
		if cid == self.java_thread_ptr.get_cid():
			name = OCA_JAVA_THREAD+str(self.java_thread_unknown)
			self.java_dict[name] = entity.get_tag()
			self.java_thread_unknown = self.java_thread_unknown+1
		if cid == self.java_native_thread_entry_ptr.get_cid():
			name = OCA_JAVA_NATIVE_NAME+str(self.native)
			self.java_thread_dict[name] = entity.get_tag()
			pid = entity.get_tag()
			if pid in self.OCA_PIDS.keys():
				java_native_dict = self.create_OCA_dict(OCA_JAVA_NATIVE,name,self.OCA_PIDS[pid])
				self.send_OCA_evt(java_native_dict,entity.get_log_time())
			self.native = self.native+1
		if cid == self.java_compiler_thread_entry_ptr.get_cid():
			name = OCA_JAVA_COMPILER_NAME+str(self.compiler)
			self.java_thread_dict[name] = entity.get_tag()
			pid = entity.get_tag()
			if pid in self.OCA_PIDS.keys():
				java_compiler_dict = self.create_OCA_dict(OCA_JAVA_COMPILER,name,self.OCA_PIDS[pid])
				self.send_OCA_evt(java_compiler_dict,entity.get_log_time())
			self.compiler = self.compiler+1

		if cid == self.java_thread_gc_ptr.get_cid():
			name = OCA_JAVA_GC_NAME+str(self.gc_thread)
			self.java_dict[name] = entity.get_tag()
			pid = entity.get_tag()
			if pid in self.OCA_PIDS.keys():
				java_gc_dict = self.create_OCA_dict(OCA_JAVA_GC,name, self.OCA_PIDS[pid])
				self.send_OCA_evt(java_gc_dict,entity.get_log_time())
			self.gc_thread = self.gc_thread + 1
		if cid == self.java_signal_thread_entry_ptr.get_cid():
			name = OCA_JAVA_SIGNAL_DISPATCHER_NAME+str(self.signal)
			self.java_thread_dict[name] = entity.get_tag()
			pid = entity.get_tag()
			if pid in self.OCA_PIDS.keys():
				java_signal_dict = self.create_OCA_dict(OCA_JAVA_SIGNAL_DISPATCHER,name,self.OCA_PIDS[pid])
				self.send_OCA_evt(java_signal_dict,entity.get_log_time())
			self.signal = self.signal+1
		if cid == self.java_low_mem_detector_ptr.get_cid():
			name = OCA_JAVA_MEMORY_DETECTOR_NAME+str(self.low_mem)
			self.java_thread_dict[name] = entity.get_tag()
			pid = entity.get_tag()
			if pid in self.OCA_PIDS.keys():
				java_low_dict = self.create_OCA_dict(OCA_JAVA_MEMORY_DETECTOR,name,self.OCA_PIDS[pid])
				self.send_OCA_evt(java_low_dict,entity.get_log_time())
			self.low_mem = self.low_mem+1
	
		if cid == self.java_attach_entry_ptr.get_cid():
			name = OCA_JAVA_ATTACH_LISTENER_NAME+str(self.java_attach)
			self.java_thread_dict[name] = entity.get_tag()
			pid = entity.get_tag()
			if pid in self.OCA_PIDS.keys():
				java_attach_dict = self.create_OCA_dict(OCA_JAVA_ATTACH_LISTENER,name,self.OCA_PIDS[pid])
				self.send_OCA_evt(java_attach_dict,entity.get_log_time())
			self.java_attach = self.java_attach+1

#		if cid == self.java_main_class_ptr.get_cid():
#			self.main_info['JAVA_Utility_Thread_PID'] = entity.get_tag()
#			self.main_info['JAVA_Utility_Thread_Name'] = entity.get_extra_data() 

#		if cid == self.java_main_thread_call_ptr.get_cid():
#			self.main_info['Application Main Classname'] = entity.get_extra_data()

#		if cid == self.java_thread_name_ptr.get_cid():
#			data = entity.get_extra_data()
#			tagValue = entity.get_tag()
#			self.thread_name_pids[tagValue] = data

#		if cid == self.java_thread_call_ptr.get_cid():
#			thread_call_name = "JAVA_Utility_Thread_PID "+str(self.java_call_number)
#			thread_call_dict_name = "JAVA_Utility_Thread_Name "+str(self.java_call_number)
#			self.java_calls[thread_call_name] = entity.get_tag()
#			self.java_calls[thread_call_dict_name] = entity.get_extra_data()
			
#		if cid == self.java_method_call_ptr.get_cid():
#			self.numberOfReferences = self.numberOfReferences + 1
#			method_name = "Method Name Referenced "+str(self.java_call_number)
#			self.java_calls[method_name] = entity.get_extra_data()
#		if cid == self.java_class_call_ptr.get_cid():
#			class_name = "Class Name "+str(self.java_call_number)
#			self.java_calls[class_name] = entity.get_extra_data()
#			dict={}
#			thread_call_name = "JAVA_Utility_Thread_PID "+str(self.java_call_number)
#			thread_call_dict_name = "JAVA_Utility_Thread_Name "+str(self.java_call_number)
#			method_name = "Method Name Referenced "+str(self.java_call_number)

#			dict[thread_call_name] = self.java_calls[thread_call_name]
#			dict[thread_call_dict_name] = self.java_calls[thread_call_dict_name]
#			dict[method_name] = self.java_calls[method_name]
#			dict[class_name] = self.java_calls[class_name]

#			self.final_list[self.java_call_number] = dict
#			self.java_call_number= self.java_call_number+1
		
		if cid == self.OCA_actions_ptr.get_cid():
			data = entity.get_extra_data()
			if data[OCA_TYPE] == OCA_FORK:
				self.OCA_PIDS[data[OCA_ARG_ORIGINAL_PARENT_PID]] = data[OCA_ARG_PARENT_PID]
				self.OCA_PIDS[data[OCA_ARG_ORIGINAL_CHILD_PID]] = data[OCA_ARG_CHILD_PID]
			self.send_output("default", entity)
			

	def finalize(self):
		"""This Spits out information gathered as part of traversing through all the
		   JVM events. Also does some processing to assign names to the threads forked 
		   off from a utility class inside the JVM. 
		"""		

		for key in self.java_dict.keys():
			if key.startswith("JAVA Thread(unknown)"):
				value = self.java_dict[key]
				for thread_key, thread_value in self.java_thread_dict.items():
					if value == thread_value:
						self.java_dict[thread_key] = value
						del self.java_dict[key]


		print "\t Java Virtual Machine Decomposition"

		print "Pid\t\t JavaVM Name \t\t\t Thread Name Identified"
		for key in self.java_dict.keys():
			value = self.java_dict[key]
			if value in self.thread_name_pids.keys():
				if len(self.thread_name_pids[value]) >=15:
					print value,"\t\t",self.thread_name_pids[value],"\t\t",key
				else:
					print value,"\t\t",self.thread_name_pids[value],"\t\t\t",key

			else:
				print value,"\t\t\t\t\t\t",key

	#	print"\nThread names"
	#	for key in self.thread_name_pids.keys():
	#		print key," : ",self.thread_name_pids[key]

	#	print "\n\nApplication Main Thread Information"
	#	for key in self.main_info.keys():
	#		print key," : ",self.main_info[key]


	#	print "\n\nNumber of Function calls done by the application : ", self.numberOfReferences

	#	print "\n\nJAVA Application Level Calls"
	#	for key in self.final_list.keys():
	#		print "Call ID : ",key
	#		for keyID in self.final_list[key].keys():
	#			print keyID," : ",self.final_list[key][keyID]
	#		print "\n"
			


		print "\nJAVA postprocessing complete\n"
	
	def send_OCA_evt(self, OCA_dict, log_time):
		"""
		Use this wrapper to send OCA events.
		"""
		OCA_evt = entities.Event(self.OCA_actions_ptr.get_cid(), log_time, 0, OCA_dict, 0)
		self.send_output("default", OCA_evt)


	def create_OCA_dict(self, name, arg_name, pid):
		"""Used for creating the OCA Dict with respect to JVM related events.
		"""
		javaDict = {}
		javaDict[OCA_TYPE] =name
		javaDict[OCA_ARG_PID] = pid
		javaDict[OCA_ARG_AC_NAME] = arg_name
		return javaDict

