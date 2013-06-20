from datastreams.postprocess import filtering, entities
from discovery.oca_definitions import *
from discovery.kernel_constants import *
import cPickle
import pickle
import copy
import Queue

#################################### TODO #####################################
# Some of the entity times in the OCA event stream are incorrect. We also need
# to develop some notion of creation and deletion time for PC records to ensure
# a true unique identifier. We also should finish writing the logic for the
# thread exit event and add a timestamp to ensure true unique ids for AC
# records.
# 
# Improve / write more summary filters.
# 
# Modularize all the ACS/PCS code.
#
# The DCG code needs lots of work. Continue expanding this, and develop some
# good rules of thumb for what should be passed directly to the DCG via the
# OCA stream, and what should be constructed by the DCG from the OCA stream.
#
# Find a better way to initialize the e2o action map.
#
# Adding nonfamilial members to the group - lots of work to do here in: this
# code - the component set manager code - the active filter code - and
# possibly the dcg code
#
# Write code for handling syscall error cases
#
# Write filters that can handle a unified datastream
###############################################################################

# This is needed so that we don't make unnecessary copies of Passive_Components
class Passive_Component(dict):
	def __init__(self):
		return None

class OCA_event_creator(filtering.Filter):
	
	expected_parameters = {
		"print_CS_level" : {
			"types" : "integer",
			"doc" : "An option to print the ACS / PCS structures at certain " \
				"events to get a narrative of the computation",
			"default" : 0,
		},
		"outfile" : {
			"types"   : "string",
			"doc"     : "File to output printed information to.",
			"default" : "-",
		},
		"print_file_report" : {
			"types"   : "boolean",
			"doc"     : "Print out a file report.",
			"default" : False,
		},
		"NFS_port" : {
			"types" : "integer",
			"doc" : "An option that specifies the port on which the nfs daemon runs " \
				"so that we can filter out events that are related to nfs operations",
			"default" : 2049,
		},
	}

	def initialize(self):
		"""
		Initialize the OCA event creator. This function creates a namespace 
		pointer to each type of event this filter will accept (for quick 
		lookup). It also initializes all of the global data structures the
		OCA event creator uses to keep track of the computation structure.
		The purpose of individual events is described in the corresponding
		OCA action. See the event_to_OCA_action_map to lookup each event's
		corresponding OCA action.
		"""

		self.traceme_thread_ptr	= self.get_ns_pointer("TRACEME/TRACEME_TOOL")
		self.fork_ptr	 	= self.get_ns_pointer("FORK/DO_FORK")
		self.root_fd_ptr	= self.get_ns_pointer("ROOT_THREAD/INHERIT_FD")
		self.exit_ptr		= self.get_ns_pointer("EXIT/DO_EXIT")
		self.signal_send_ptr 	= self.get_ns_pointer("SIGNAL/SEND_SIGNAL")
		self.flock_ptr 		= self.get_ns_pointer("FILE/FLOCK")
		self.fcntl_ptr 		= self.get_ns_pointer("FILE/FCNTL")
		self.fifo_open_ptr 	= self.get_ns_pointer("FIFO/FIFO_OPEN")
		self.pipe_ptr 		= self.get_ns_pointer("PIPE/DO_PIPE")
		self.ptrace_ptr 	= self.get_ns_pointer("PTRACE/SYS_PTRACE")
	
		self.exec_ptr 		= self.get_ns_pointer("EXECVE/DO_EXECVE")
		self.exec_misc_open_ptr	= self.get_ns_pointer("EXECVE/MISC_OPEN")
		self.exec_som_open_ptr	= self.get_ns_pointer("EXECVE/SOM_OPEN")
		self.exec_elf_open_ptr	= self.get_ns_pointer("EXECVE/ELF_OPEN")
		
		self.shmget_ptr 	= self.get_ns_pointer("SHMEM/SHMGET")
		self.shmat_ptr 		= self.get_ns_pointer("SHMEM/SHMAT")
		self.shmdt_ptr 		= self.get_ns_pointer("SHMEM/SHMDT")
		self.shmat_add_ptr	= self.get_ns_pointer("SHMEM/SHMAT_ADD")

		self.close_ptr 		= self.get_ns_pointer("FILE/CLOSE")
		self.open_ptr 		= self.get_ns_pointer("FILE/OPEN")
		self.dupx_ptr		= self.get_ns_pointer("FILE/DUP_X")
		self.dup2_ptr		= self.get_ns_pointer("FILE/DUP2")
		self.fd_install_ptr	= self.get_ns_pointer("FILE/FD_INSTALL")
		self.read_info_ptr 	= self.get_ns_pointer("FILE/READ_INFO")
		self.read_data_ptr 	= self.get_ns_pointer("FILE/READ_DATA")
		self.write_info_ptr 	= self.get_ns_pointer("FILE/WRITE_INFO")
		self.write_data_ptr 	= self.get_ns_pointer("FILE/WRITE_DATA")
		self.readv_ptr		= self.get_ns_pointer("FILE/READV")
		self.writev_ptr		= self.get_ns_pointer("FILE/WRITEV")
		self.select_ptr		= self.get_ns_pointer("FILE/SELECT")
	
		self.dsui_signal_ptr 	= self.get_ns_pointer("DSCVR/DSUI_SIGNAL_THREAD")
		self.dsui_logger_ptr 	= self.get_ns_pointer("DSCVR/DSUI_LOGGING_THREAD")
		self.dsui_buffer_ptr 	= self.get_ns_pointer("DSCVR/DSUI_BUFFER_THREAD")
		
		self.listen_ptr         = self.get_ns_pointer("SOCKET/LISTEN")
		self.accept_ptr         = self.get_ns_pointer("SOCKET/ACCEPT")
		self.conn_end_ptr       = self.get_ns_pointer("SOCKET/CONNECT_END")
		self.send_msg_ptr       = self.get_ns_pointer("SOCKET/SOCK_SENDMSG")
		self.recv_msg_ptr       = self.get_ns_pointer("SOCKET/SOCK_RECVMSG")
		self.socket_ptr         = self.get_ns_pointer("SOCKET/SOCKET")
		self.socketpair1_ptr    = self.get_ns_pointer("SOCKET/SOCKETFIRSTPAIR")
		self.socketpair2_ptr    = self.get_ns_pointer("SOCKET/SOCKETSECONDPAIR")
		self.bind_ptr           = self.get_ns_pointer("SOCKET/BIND")
		self.conn_begin_ptr     = self.get_ns_pointer("SOCKET/LOCAL_CONNECT")
		self.send_to_ptr        = self.get_ns_pointer("SOCKET/SENDTO")
		self.recv_from_ptr      = self.get_ns_pointer("SOCKET/RECVFROM")
		self.send_msg_ptr       = self.get_ns_pointer("SOCKET/SENDMSG")
		self.recv_msg_ptr       = self.get_ns_pointer("SOCKET/RECVMSG")
		self.sock_send_ptr      = self.get_ns_pointer("SOCKET/SOCK_SENDMSG")
		self.sock_recv_ptr      = self.get_ns_pointer("SOCKET/SOCK_RECVMSG")
		self.client_add_ptr	= self.get_ns_pointer("SOCKET/CLIENT_ADD")
		self.server_add_ptr	= self.get_ns_pointer("SOCKET/SERVER_ADD")

		self.switch_to_ptr	= self.get_ns_pointer("SCHEDULER/SWITCH_TO")
		self.switch_from_ptr	= self.get_ns_pointer("SCHEDULER/SWITCH_FROM")
		self.syscall_ptr	= self.get_ns_pointer("SYSCALL/SYSTEM_CALL")

		self.OCA_actions_ptr    = self.get_ns_pointer("OCA/ACTIONS")

		# This is a dictionary of all the active components (i.e. threads / processes) that
		# make up the observed computation. It maps the abstract pid for each thread to a
		# dict with fields describing the AC
		#
		self.ACS = {}

		# A mapping of all passive components IDs ((inode_id, sys_id) tuples), to a passive
		# component object. The passive component objects are a dict with fields describing
		# the PC
		#
		self.PCS = {} 

		self.__pid2OCA = {}
		self.__OCA2pid = {}
	
		# Used to give ACs and PCs an abstract number
		self.OCA_pid      = 0
		self.pipe_num     = 0
		self.shm_num      = 0
		self.PT_num       = 0
		self.sock_num     = 0
		self.sk_end       = 0
		self.shm_GID_num  = 0
		self.file_GID_num = 0

		# Used to match up accept and connect socket calls. This is keyed by
		# ((saddr, sport), (daddr, dport)) and maps to socket name
		#
		self.listening_queues = {}
		self.local_socks = {}
		self.remote_socks = {}

		# Used to match up read and write info events with their data events
		self.readDicts    = {}
		self.writeDicts   = {}

		# XXX: Hack to initialize the event_to_OCA_action_map
		self.need_init_e2o_map = True

		# Placeholder for the PID of the traceme tool process
		self.traceme_pid = None

		self.print_level = self.params["print_CS_level"]
		if self.params["outfile"] == "-":
			self.outfile = sys.stdout
		else:
			self.outfile = open(self.params["outfile"], "w")

		# Dictionaries to identify groups of threads that share resources
		#
		self.shm_groups  = {}
		self.file_groups = {}

		self.file_report = self.params["print_file_report"]

		self.nfsPort = self.params["NFS_port"]

		self.unClassified = {}

		self.unClassifiedExten = ["taskalias","tty",".dsui.bin","meminfo","cpuinfo","bash","lib"]

		self.sharedFileExtension = ".so"

		# Used in local socket client/server analysis
		self.unrelated_conns = []

	#	self.init_e2o_map()

	def process(self, entity):

		# FIXME: Find a better way to initialize the OCA action map
	#	if self.need_init_e2o_map:
	#		self.init_e2o_map()
#		print "Keys : ", self.event_to_OCA_action_map.keys()
	#		self.need_init_e2o_map = False
			
		# Throw away events registered by the traceme tool process
		#
		cid = entity.get_cid()
		if self.process_traceme_events(entity):
			return
	#	elif self.event_to_OCA_action_map.has_key(cid):
	#		self.event_to_OCA_action_map[cid](entity)
		elif cid == self.dsui_signal_ptr.get_cid():
			self.__evt_dsui_signal(entity)
		elif cid == self.dsui_buffer_ptr.get_cid():
			self.__evt_dsui_buffer(entity)
		elif cid == self.dsui_logger_ptr.get_cid():
			self.__evt_dsui_logger(entity)
		elif cid == self.fork_ptr.get_cid():
			self.__evt_fork(entity)
		elif cid == self.exit_ptr.get_cid():
			self.__evt_exit(entity)
		elif cid == self.signal_send_ptr.get_cid():
			self.__evt_signal_send(entity)
		elif cid == self.shmget_ptr.get_cid():
			self.__evt_shmget(entity)
		elif cid == self.shmat_ptr.get_cid():
			self.__evt_shmat(entity)
		elif cid == self.shmdt_ptr.get_cid():
			self.__evt_shmdt(entity)
		elif cid == self.shmat_add_ptr.get_cid():
			self.__evt_shmat_add(entity)
		elif cid == self.fifo_open_ptr.get_cid():
			self.__evt_fifo_open(entity)
		elif cid == self.pipe_ptr.get_cid():
			self.__evt_do_pipe(entity)
		elif cid == self.fcntl_ptr.get_cid():
			self.__evt_fcntl(entity)
		elif cid == self.flock_ptr.get_cid():
			self.__evt_fcntl(entity)
		elif cid == self.ptrace_ptr.get_cid():
			self.__evt_ptrace(entity)
		elif cid == self.exec_ptr.get_cid():
			self.__evt_exec(entity)
		elif cid == self.exec_misc_open_ptr.get_cid():
			self.__evt_open(entity)
		elif cid == self.exec_som_open_ptr.get_cid():
			self.__evt_open(entity)
		elif cid == self.exec_elf_open_ptr.get_cid():
			self.__evt_open(entity)
		elif cid == self.close_ptr.get_cid():
			self.__evt_close(entity)
		elif cid == self.open_ptr.get_cid():
			self.__evt_open(entity)
		elif cid == self.dupx_ptr.get_cid():
			self.__evt_dup(entity)
		elif cid == self.dup2_ptr.get_cid():
			self.__evt_dup(entity)
		elif cid == self.fd_install_ptr.get_cid():
			self.__evt_fd_install(entity)
		elif cid == self.read_info_ptr.get_cid():
			self.__evt_read_info(entity)
		elif cid == self.select_ptr.get_cid():
			self.__evt_select(entity)
		elif cid == self.read_data_ptr.get_cid():
			self.__evt_read_data(entity)
		elif cid == self.write_info_ptr.get_cid():
			self.__evt_write_info(entity)
		elif cid == self.readv_ptr.get_cid():
			self.__evt_readv(entity)
		elif cid == self.writev_ptr.get_cid():
			self.__evt_writev(entity)
		elif cid == self.write_data_ptr.get_cid():
			self.__evt_write_data(entity)
		elif cid == self.socket_ptr.get_cid():
			self.__evt_socket(entity)
		elif cid == self.socketpair1_ptr.get_cid():
			self.__evt_socket(entity)
		elif cid == self.socketpair2_ptr.get_cid():
			self.__evt_socket(entity)
		elif cid == self.client_add_ptr.get_cid():
			self.__evt_socket_add(entity)
		elif cid == self.server_add_ptr.get_cid():
			self.__evt_socket_add(entity)
		elif cid == self.bind_ptr.get_cid():
			self.__evt_bind(entity)
		elif cid == self.conn_begin_ptr.get_cid():
			self.__evt_conn_begin(entity)
		elif cid == self.send_to_ptr.get_cid():
			self.__evt_send_to(entity)
		elif cid == self.recv_from_ptr.get_cid():
			self.__evt_recv_from(entity)
		elif cid == self.send_msg_ptr.get_cid():
			self.__evt_send_msg(entity)
		elif cid == self.recv_msg_ptr.get_cid():
			self.__evt_recv_msg(entity)
		elif cid == self.sock_send_ptr.get_cid():
			self.__evt_sock_send(entity)
		elif cid == self.sock_recv_ptr.get_cid():
			self.__evt_sock_recv(entity)
		elif cid == self.listen_ptr.get_cid():
			self.__evt_listen(entity)
		elif cid == self.accept_ptr.get_cid():
			self.__evt_accept(entity)
		elif cid == self.conn_end_ptr.get_cid():
			self.__evt_conn_end(entity)
		elif cid == self.switch_to_ptr.get_cid():
			self.__evt_switch_to(entity)
		elif cid == self.switch_from_ptr.get_cid():
			self.__evt_switch_from(entity)
		elif cid == self.syscall_ptr.get_cid():
			self.__evt_syscall(entity)
		else:
		#	self.send_output("default", entity)
			if self.print_level > 4:
				print >> self.outfile, "Warning: got DSKI event without OCA mapping"
				print >> self.outfile, "Unknown event: ", entity
			
	def finalize(self):

		if self.file_report:
			self.print_file_report()

	def process_traceme_events(self, entity):
		"""
		Process the scaffolding events in the raw event stream. Return
		False if the event is not part of the scaffolding.
		"""
		ret = False
		pid = entity.get_pid()
		cid = entity.get_cid()

		# This event is logged in the DSUI of the actual traceme command.
		# We use it to denote the pid of the traceme tool
		#
		if cid == self.traceme_thread_ptr.get_cid():
			self.traceme_pid = entity.get_tag()
			ret = True

		# Events logged by the traceme_pid are part of the scaffolding. The
		# first (and only) process the traceme tool forks is our root
		# thread.
		#
		elif pid == self.traceme_pid:
			# Root fd events are logged in the active filter (and,
			# therefore, before the fork event), so we create the root
			# record when we see the first of these events, as opposed
			# to the fork. This implicitly throws away the fork event
			# (and any other non root_fd_evt) registered by the
			# traceme process.
			#
			if cid == self.root_fd_ptr.get_cid():
				OCA_pid = self.pid2OCA(entity.get_tag(), OCA_PID_CREATE)
				if not self.ACS.has_key(OCA_pid):
					self.__evt_root_thread(entity)
				self.__evt_root_fd(entity)

			ret = True
			
		return ret

	def get_new_OCA_pid(self, pid):
		"""
		Create and return a new OCA pid given a pid recorded from raw
		instrumentation. This assumes duplicate raw pids are actually
		different tasks, but that the system is simply reusing the pid
		"""
		if self.__pid2OCA.has_key(pid):
			print "Warning: tried to get new OCA pid for a", \
				"pid we are already tracking."
			print "Assuming the pid has been reused ..."
		
		self.OCA_pid += 1
		self.__pid2OCA[pid] = self.OCA_pid
		self.__OCA2pid[self.OCA_pid] = pid
		return self.__pid2OCA[pid]

	def pid2OCA(self, pid, create=False):
		"""
		Look up a raw instrumentation pid and return the corresponding
		OCA pid. If create is True, this will create an OCA pid
		corresponding to the raw pid if one does not yet exist
		"""
		if self.__pid2OCA.has_key(pid):
			return self.__pid2OCA[pid]
		else:
			if not create:
				print "Warning: Tried to access OCA_pid of", \
						"unknown pid: %d." % pid
				return -1
			else:
				return self.get_new_OCA_pid(pid)
	
	def create_AC_record(self, parent_OCA_pid, child_OCA_pid, relation, clone_flags = None):
		"""
		Create an AC record. The child_OCA_pid is the pid of the AC to be
		added. The parent_OCA_pid is the pid of the AC already in the ACS 
		that the child is related to. The relation parameter specifies the
		type of relationship the parent has to the child (i.e. why the child
		is being added to the group). Use create_root_AC_record to create
		the initial AC record.
		"""
		if not self.__OCA2pid.has_key(child_OCA_pid):
			print "Error creating AC record with child_OCA_pid: %d" % child_OCA_pid
			print "Use get_new_OCA_pid to create valid OCA pids."
			raise AssertionError
		
		if relation == AC_FAMILIAL_TASK and not self.ACS.has_key(parent_OCA_pid):
			print "Error creating familial AC record with parent_OCA_pid: %d" % child_OCA_pid
			print "Parent AC does not exist"
			raise AssertionError

		self.ACS[child_OCA_pid] = {}
		child_rec = self.ACS[child_OCA_pid]

		child_rec[AC_ATTR_OCA_PID]    = child_OCA_pid
		child_rec[AC_ATTR_ORIG_PID]   = self.__OCA2pid[child_OCA_pid]
		child_rec[AC_ATTR_AC_ID]      = child_OCA_pid
		child_rec[AC_TYPE]            = AC_UTHREAD
		child_rec[AC_ATTR_NAME]       = OCA_TNAME_BASE % child_OCA_pid
		child_rec[AC_ATTR_RELATION]   = relation
		child_rec[AC_ATTR_MASTERS]    = []
		child_rec[AC_ATTR_SLAVES]     = []
			
		if relation == AC_ROOT_RECORD:
			child_rec[AC_ATTR_GENERATION] = AC_INIT_BASH
			child_rec[AC_ATTR_EXEC_NAME]  = AC_DEFAULT_EXEC_NAME
			child_rec[AC_ATTR_SHMATS]     = {}
			child_rec[AC_ATTR_FDS]        = {}
			child_rec[AC_ATTR_SHM_GID]    = self.get_new_shm_GID()
			child_rec[AC_ATTR_FILE_GID]   = self.get_new_file_GID()
		elif relation == AC_FAMILIAL_TASK:

			parent_rec = self.ACS[parent_OCA_pid]
		
			# clone_flags is passed when a task is forked off. If CLONE_VM is 
			# set, the child shares an address space with it's parent and, 
			# therefore, the child's AC_ATTR_SHMATS field points to the same 
			# shm addresses that the parent uses. Similarly, with the file
			# descriptor table, if CLONE_FILES is set, the child's AC_ATTR_FDS
			# field points to the parent's AC_ATTR_FDS table.
			#
			# If these flags are not set, the child process creates a new copy
			# of the address space and file descriptor information for the child
			# to use
			#
			if clone_flags & CLONE_VM: 	
				shm_GID = parent_rec[AC_ATTR_SHM_GID]
				child_rec[AC_ATTR_SHM_GID] = shm_GID
				child_rec[AC_ATTR_SHMATS]  = parent_rec[AC_ATTR_SHMATS] 
			else:
				shm_GID = self.get_new_shm_GID()
				child_rec[AC_ATTR_SHM_GID] = shm_GID
				child_rec[AC_ATTR_SHMATS]  = {}
				self.copy_address_space(parent_OCA_pid, child_OCA_pid)
			
			if clone_flags & CLONE_FILES:
				file_GID = parent_rec[AC_ATTR_FILE_GID]
				child_rec[AC_ATTR_FILE_GID] = file_GID
				child_rec[AC_ATTR_FDS]      = parent_rec[AC_ATTR_FDS] 
			else:
				file_GID = self.get_new_file_GID()
				child_rec[AC_ATTR_FILE_GID] = file_GID
				child_rec[AC_ATTR_FDS]      = {}
				self.copy_fd_table(parent_OCA_pid, child_OCA_pid)

			# Generation may change to 1 if and when an AC_INIT_BASH thread
			# calls exec
			#
			if parent_rec[AC_ATTR_GENERATION] == AC_INIT_BASH:
				child_rec[AC_ATTR_GENERATION] = AC_INIT_BASH
			else:
				child_rec[AC_ATTR_GENERATION] = parent_rec[AC_ATTR_GENERATION] + 1
	
			child_rec[AC_ATTR_EXEC_NAME] = self.ACS[parent_OCA_pid][AC_ATTR_EXEC_NAME]
		else:
			child_rec[AC_ATTR_GENERATION] = AC_NONFAMILIAL_TASK
			child_rec[AC_ATTR_EXEC_NAME]  = AC_DEFAULT_EXEC_NAME
			child_rec[AC_ATTR_SHMATS]     = {}
			child_rec[AC_ATTR_FDS]        = {}
			child_rec[AC_ATTR_SHM_GID]    = self.get_new_shm_GID()
			child_rec[AC_ATTR_FILE_GID]   = self.get_new_file_GID()

		self.file_groups[child_rec[AC_ATTR_FILE_GID]][AC_TG_ALIVE].append(child_OCA_pid)
		self.shm_groups[child_rec[AC_ATTR_SHM_GID]][AC_TG_ALIVE].append(child_OCA_pid)
	
	def get_new_file_GID(self):
		self.file_GID_num += 1
		self.file_groups[self.file_GID_num] = {}
		self.file_groups[self.file_GID_num][AC_TG_ALIVE] = []
		self.file_groups[self.file_GID_num][AC_TG_EXITED]  = []
		return self.file_GID_num

	def get_new_shm_GID(self):
		self.shm_GID_num += 1
		self.shm_groups[self.shm_GID_num] = {}
		self.shm_groups[self.shm_GID_num][AC_TG_ALIVE] = []
		self.shm_groups[self.shm_GID_num][AC_TG_EXITED]  = []
		return self.shm_GID_num

	def copy_address_space(self, parent_OCA_pid, child_OCA_pid):
		"""
		Creates a new copy of the parent's address space information and
		assigns it to the child record.
		"""
		child_rec  = self.ACS[child_OCA_pid]
		parent_rec = self.ACS[parent_OCA_pid]
		
		# Attached shared memory segments is the only address space
		# information we are currently tracking.
		#
		for shm in parent_rec[AC_ATTR_SHMATS].iterkeys():
			PC_entry = parent_rec[AC_ATTR_SHMATS][shm]
			child_rec[AC_ATTR_SHMATS][shm] = PC_entry

			child_AC_shm_ref = {}
			child_AC_shm_ref[AC_REF_ID] = (child_rec[AC_ATTR_SHM_GID], shm)
			for AC_ref in PC_entry[PC_ATTR_OPEN_REFS]:
				if AC_ref[AC_REF_ID] == (parent_rec[AC_ATTR_SHM_GID], shm):
					child_AC_shm_ref[AC_REF_MODE] = AC_ref[AC_REF_MODE]
					PC_entry[PC_ATTR_OPEN_REFS].append(child_AC_shm_ref)	
					break

	def copy_fd_table(self, parent_OCA_pid, child_OCA_pid):
		"""
		Creates a new copy of the parent's file descriptor table 
		information and assigns it to the child record.
		"""	
		
		child_rec  = self.ACS[child_OCA_pid]
		parent_rec = self.ACS[parent_OCA_pid]

		for fd in self.ACS[parent_OCA_pid][AC_ATTR_FDS].iterkeys():
			# Add the fd to the child's list of fds
			PC_entry = self.ACS[parent_OCA_pid][AC_ATTR_FDS][fd]
			child_rec[AC_ATTR_FDS][fd] = PC_entry
					
			# For the PC that this points to, add an AC_REF entry for the child's fd
			child_AC_ref = {}
			child_AC_ref[AC_REF_ID] = (child_rec[AC_ATTR_FILE_GID], fd)
			for AC_ref in PC_entry[PC_ATTR_OPEN_REFS]:
				if AC_ref[AC_REF_ID] == (parent_rec[AC_ATTR_FILE_GID], fd):
					child_AC_ref[AC_REF_MODE]   = AC_ref[AC_REF_MODE]
					child_AC_ref[AC_REF_READ]   = 0
					child_AC_ref[AC_REF_WROTE]  = 0
					PC_entry[PC_ATTR_OPEN_REFS].append(child_AC_ref)	
					break
	
	def create_root_AC_record(self, OCA_pid):
		"""
		Create the root AC record. This is done when the traceme tool
		issues its fork event
		"""
		self.create_AC_record(None, OCA_pid, AC_ROOT_RECORD)
	
	def create_PC_record(self, type, PC_id, name):
		"""
		Create a PC record. This creates an entry in the PCS dict.
		Lists on an AC record may also point to the data pointed
		to by the PCS dict
		"""
		if self.PCS.has_key(PC_id):
			# Not sure what's best here
			# For now, print out an error
			print "Error creating PC record: ", PC_id
			print "The PC_id already exists"
			raise AssertionError
			
		self.PCS[PC_id]                      = Passive_Component()
		self.PCS[PC_id][PC_TYPE]             = type 
		self.PCS[PC_id][PC_ATTR_PC_ID]       = PC_id
		self.PCS[PC_id][PC_ATTR_NAME]        = name
		self.PCS[PC_id][PC_ATTR_OPEN_REFS]   = []
		self.PCS[PC_id][PC_ATTR_CLOSED_REFS] = []

		if type == PC_FILE:
			self.PCS[PC_id][PC_ATTR_LOCKED] = False
		elif type == PC_SK_ENDPOINT:
			self.PCS[PC_id][PC_SKAT_STATE]    = SK_FREE
			self.PCS[PC_id][PC_SKAT_BACKLOG]  = 0
			self.PCS[PC_id][PC_SKAT_BOUND_ID] = SK_UNBOUND
			self.PCS[PC_id][PC_SKAT_NAME]     = SK_UNASSIGNED
			self.PCS[PC_id][PC_SKAT_OTHER_END]= None

###############################################################################
# Thread Creation/Destruction Definitions
###############################################################################

	def __evt_root_thread(self, entity):
		"""
		We recognize the root thread by the first root_fd event logged in 
		the active filter. These events are intended to announce the file
		descriptor table of the root thread, but because they are logged
		before the actual fork call, we use the first of them to announce
		the root thread.
		"""
		OCA_pid = self.pid2OCA(entity.get_tag())
		self.create_root_AC_record(OCA_pid)
		rec = self.ACS[OCA_pid]

		root_thread_dict = {}
		root_thread_dict[OCA_TYPE]          = OCA_ROOT_THREAD
		root_thread_dict[OCA_ARG_PID]       = rec[AC_ATTR_OCA_PID]
		root_thread_dict[OCA_ARG_AC_ID]     = rec[AC_ATTR_AC_ID] 
		root_thread_dict[OCA_ARG_AC_TYPE]   = rec[AC_TYPE]
		root_thread_dict[OCA_ARG_AC_NAME]   = rec[AC_ATTR_NAME]
		root_thread_dict[OCA_ARG_GEN]       = rec[AC_ATTR_GENERATION]
		root_thread_dict[OCA_ARG_EXEC_NAME] = rec[AC_ATTR_EXEC_NAME]
		root_thread_dict[OCA_ARG_REL]       = rec[AC_ATTR_RELATION]

		self.send_OCA_evt(root_thread_dict, entity.get_log_time())
		
	def __evt_fork(self, entity):
		"""
		This event is logged in the do_fork system call right after the
		copy_process call. Here we create a familial record of the
		child thread, which inherits some AC attributes from the parent
		"""
		pid         = entity.get_pid()
		clone_flags = entity.get_extra_data()

	#	print "parent pid : ", entity.get_pid(), " Child pid : ", entity.get_tag()

		parent_OCA_pid = self.pid2OCA(pid)
		if not self.ACS.has_key(parent_OCA_pid):
			print "Warning: Got a fork event from a task with unknown" \
					"OCA_pid: %d." % parent_OCA_pid
			raise AssertionError

		# The pid of the cloned child is attached as tag data
		child_OCA_pid = self.get_new_OCA_pid(entity.get_tag())
		if not self.ACS[parent_OCA_pid][AC_ATTR_RELATION] == AC_FAMILIAL_TASK \
     		and not self.ACS[parent_OCA_pid][AC_ATTR_RELATION] == AC_ROOT_RECORD:
			self.create_AC_record(parent_OCA_pid, child_OCA_pid, \
			 			self.ACS[parent_OCA_pid][AC_ATTR_RELATION], \
			 			clone_flags)
			self.ACS[child_OCA_pid][AC_ATTR_EXEC_NAME] = \
				self.ACS[parent_OCA_pid][AC_ATTR_EXEC_NAME]
		else:
			self.create_AC_record(parent_OCA_pid, child_OCA_pid, \
			 AC_FAMILIAL_TASK, clone_flags)

		# Get the inherited fds and shmaddrs
		inherited_fds = {}
		for fd in self.ACS[child_OCA_pid][AC_ATTR_FDS]:
			PC_entry = self.ACS[child_OCA_pid][AC_ATTR_FDS][fd]
			inherited_fds[fd] = {}
			inherited_fds[fd][OCA_ARG_PC_ID] = PC_entry[PC_ATTR_PC_ID]
			inherited_fds[fd][OCA_ARG_PC_NAME] = PC_entry[PC_ATTR_NAME]

			for AC_ref in PC_entry[PC_ATTR_OPEN_REFS]:
				if AC_ref[AC_REF_ID] == (self.ACS[child_OCA_pid][AC_ATTR_FILE_GID], fd):
					inherited_fds[fd][OCA_ARG_MODE] = AC_ref[AC_REF_MODE]
					break	

		inherited_shms = {}
		for shm in self.ACS[child_OCA_pid][AC_ATTR_SHMATS]:
			PC_entry = self.ACS[child_OCA_pid][AC_ATTR_SHMATS][shm]
			inherited_shms[shm] = {}
			inherited_shms[shm][OCA_ARG_PC_ID] = PC_entry[PC_ATTR_PC_ID]
			
			for AC_ref in PC_entry[PC_ATTR_OPEN_REFS]:
				if AC_ref[AC_REF_ID] == (self.ACS[child_OCA_pid][AC_ATTR_SHM_GID], shm):
					inherited_shms[shm][OCA_ARG_MODE] = AC_ref[AC_REF_MODE]
					break	
		
		fork_dict                      = {}
		fork_dict[OCA_TYPE]            = OCA_FORK
		fork_dict[OCA_ARG_PARENT_PID]  = parent_OCA_pid
		fork_dict[OCA_ARG_CHILD_PID]   = child_OCA_pid
		fork_dict[OCA_ARG_REL]         = AC_FAMILIAL_TASK
		fork_dict[OCA_ARG_CLONE_FLAGS] = clone_flags
		fork_dict[OCA_ARG_PARENT_ID]   = self.ACS[parent_OCA_pid][AC_ATTR_AC_ID]
		fork_dict[OCA_ARG_CHILD_ID]    = self.ACS[child_OCA_pid][AC_ATTR_AC_ID]
		fork_dict[OCA_ARG_EXEC_NAME]   = self.ACS[child_OCA_pid][AC_ATTR_EXEC_NAME]
		fork_dict[OCA_ARG_GEN]         = self.ACS[child_OCA_pid][AC_ATTR_GENERATION]
		fork_dict[OCA_ARG_PARENT_NAME] = self.ACS[parent_OCA_pid][AC_ATTR_NAME]
		fork_dict[OCA_ARG_CHILD_NAME]  = self.ACS[child_OCA_pid][AC_ATTR_NAME] 
		fork_dict[OCA_ARG_CHILD_TYPE]  = self.ACS[child_OCA_pid][AC_TYPE] 
		fork_dict[OCA_ARG_IN_FDS]      = inherited_fds
		fork_dict[OCA_ARG_IN_SHMS]     = inherited_shms
		fork_dict[OCA_ARG_ORIGINAL_PARENT_PID] = entity.get_pid()
		fork_dict[OCA_ARG_ORIGINAL_CHILD_PID] = entity.get_tag()

		self.send_OCA_evt(fork_dict, entity.get_log_time())

		if self.print_level >= MAX_PRINT_LEVEL:
			print >> self.outfile, "FORK: %d --Forked--> %d" % (parent_OCA_pid, child_OCA_pid)
			self.print_ACS()
			self.print_PCS()

	def __evt_root_fd(self, entity):
		"""
		One of these events is generated for every fd in the child's open
		file table at fork time. We use this to cover any DSKI fd's or
		pseudo terminal fd's
		"""

		data      = entity.get_extra_data()
		OCA_pid   = self.pid2OCA(entity.get_tag())
		fd 	  = data["fd"]
		mode 	  = data["mode"]
		inode_id  = data["inode_id"]
		sys_id 	  = data["sys_id"]
		filename  = data["filename"]
		PC_id     = (sys_id, inode_id)

		assert self.ACS.has_key(OCA_pid)
		assert self.ACS[OCA_pid][AC_ATTR_RELATION] == AC_ROOT_RECORD

		AC_ref_id            = (self.ACS[OCA_pid][AC_ATTR_FILE_GID], fd)
		AC_ref   	     = {}
		AC_ref[AC_REF_ID]    = AC_ref_id
		AC_ref[AC_REF_MODE]  = fileMode2String(mode)
		AC_ref[AC_REF_READ]  = 0
		AC_ref[AC_REF_WROTE] = 0

		# We assume that, other than regular files, the only type of
		# file a root thread may have open are pseudo terminals
		#
		if not self.PCS.has_key(PC_id):
			name = filename
			type = PC_FILE
			if sys_id == PC_DEVPTS_FS:
				self.PT_num += 1
				name = PC_PT_NAME_BASE % self.PT_num
				type = PC_PSEUDOT

			self.create_PC_record(type, PC_id, name)
			
		# Add the fd to this AC's list of fds
		self.ACS[OCA_pid][AC_ATTR_FDS][fd] = self.PCS[PC_id]
		self.PCS[PC_id][PC_ATTR_OPEN_REFS].append(AC_ref)

		root_fd_dict                  = {}
		root_fd_dict[OCA_TYPE]        = OCA_ROOT_FD
		root_fd_dict[OCA_ARG_PID]     = OCA_pid
		root_fd_dict[OCA_ARG_AC_ID]   = OCA_pid
		root_fd_dict[OCA_ARG_FD]      = fd
		root_fd_dict[OCA_ARG_AC_NAME] = self.ACS[OCA_pid][AC_ATTR_NAME]
		root_fd_dict[OCA_ARG_PC_ID]   = PC_id
		root_fd_dict[OCA_ARG_PC_TYPE] = self.PCS[PC_id][PC_TYPE]
		root_fd_dict[OCA_ARG_PC_NAME] = self.PCS[PC_id][PC_ATTR_NAME]
		root_fd_dict[OCA_ARG_MODE]    = fileMode2String(mode)
		
		self.send_OCA_evt(root_fd_dict, entity.get_log_time())

	def __evt_exit(self, entity):
		"""
		Event logged when a thread completes. May do more here in the future.
		On the lowest print level, we print the ACS/PCS whenever a thread exits
		"""
		OCA_pid = self.pid2OCA(entity.get_pid())	
		self.file_groups[self.ACS[OCA_pid][AC_ATTR_FILE_GID]][AC_TG_ALIVE].remove(OCA_pid)
		self.shm_groups[self.ACS[OCA_pid][AC_ATTR_SHM_GID]][AC_TG_ALIVE].remove(OCA_pid)
		self.file_groups[self.ACS[OCA_pid][AC_ATTR_FILE_GID]][AC_TG_EXITED].append(OCA_pid)
		self.shm_groups[self.ACS[OCA_pid][AC_ATTR_SHM_GID]][AC_TG_EXITED].append(OCA_pid)

		if self.print_level >= MIN_PRINT_LEVEL:
			print >> self.outfile, "EXIT: %s exited" % self.ACS[OCA_pid][AC_ATTR_NAME]
			self.print_ACS()
			self.print_PCS()

###############################################################################
# Syscall Instrumentation Point
###############################################################################

	def __evt_syscall(self, entity):
		"""
		Event logged at the entry of every system call
		"""
		OCA_pid = self.pid2OCA(entity.get_pid())
		data    = entity.get_extra_data()

		if OCA_pid < 0:
			print "ERROR: Got a system call (%s)" % (data["name"]), \
				" from unknown PID: %d" % (entity.get_pid())
			return


		syscall_dict = {}
		syscall_dict[OCA_TYPE]          = OCA_SYSCALL
		syscall_dict[OCA_ARG_PID]       = OCA_pid
		syscall_dict[OCA_ARG_EXEC_NAME] = self.ACS[OCA_pid][AC_ATTR_EXEC_NAME]
		syscall_dict[OCA_ARG_SYSCALL]   = data["nr"]
		syscall_dict[OCA_ARG_PARAMS]    = data["params"]

		self.send_OCA_evt(syscall_dict, entity.get_log_time())

###############################################################################
# DSUI Renaming Definitions
###############################################################################
	
	def __evt_signal_send(self, entity):
		"""
		This event is logged in send_signal(). If the pid of the receiving
		process is not in the group we are tracking, we add them in here 
		as a nonfamilial AC.
		"""
		# TODO: Instrument the kernel in such a way that if a
		# process in our computation receives a signal, the
		# sending thread will be added to our group
		#
		signal_num = entity.get_extra_data()
		sender_OCA_pid = self.pid2OCA(entity.get_pid())
		if not self.ACS.has_key(sender_OCA_pid):
			print "ERROR: Got a send signal event from a task with" \
					"unknown OCA_pid: %d." % sender_OCA_pid
			raise AssertionError

		# Create the receiver's OCA pid and AC record, 
		# if necessary
		receiver_OCA_pid = self.pid2OCA(entity.get_tag(), OCA_PID_CREATE)
		if not self.ACS.has_key(receiver_OCA_pid):
			self.create_AC_record(None, receiver_OCA_pid, AC_SIGNAL_REL)

		sig_dict                        = {}
		sig_dict[OCA_TYPE]              = OCA_SIGNAL_SEND 
		sig_dict[OCA_ARG_SENDER]        = sender_OCA_pid
		sig_dict[OCA_ARG_RECEIVER]      = receiver_OCA_pid	
#		FIXME:
#		Check this out:
		#sig_dict[OCA_ARG_SENDER_TYPE]   = self.ACS[sender_OCA_pid][AC_TYPE]
		#sig_dict[OCA_ARG_RECEIVER_TYPE] = self.ACS[receiver_OCA_pid][AC_TYPE]
		sig_dict[OCA_ARG_SIGNAL_NUMBER] = signum2String(signal_num)

		self.send_OCA_evt(sig_dict, entity.get_log_time())

	def __evt_dsui_signal(self, entity):
		"""
		These events announce the original pid of some relevant DSUI 
		threads. We replace the thread name with this information where 
		appropriate
		"""
		OCA_pid = self.pid2OCA(entity.get_tag())

		if not self.ACS.has_key(OCA_pid):
			print "ERROR: Got a bad DSUI_SIGNAL_THREAD event with" \
					"unknown OCA_pid: %d" % OCA_pid
			raise AssertionError
		
		self.ACS[OCA_pid][AC_ATTR_NAME] = OCA_DSUI_SIG

		signal_catcher_dict                  = {}
		signal_catcher_dict[OCA_TYPE]        = OCA_DSUI_THREAD_SIGNAL_CATCHER
		signal_catcher_dict[OCA_ARG_PID]     = OCA_pid
		signal_catcher_dict[OCA_ARG_AC_NAME] = OCA_DSUI_SIG
		self.send_OCA_evt(signal_catcher_dict, entity.get_log_time())

	def __evt_dsui_logger(self, entity):
		"""
		These events announce the original pid of some relevant DSUI 
		threads. We replace the thread name with this information where 
		appropriate
		"""
		OCA_pid = self.pid2OCA(entity.get_tag())
		
		if not self.ACS.has_key(OCA_pid):
			print "ERROR: Got a bad DSUI_LOGGER_THREAD event with" \
					"unknown OCA_pid: %d" % OCA_pid
			raise AssertionError
		
		self.ACS[OCA_pid][AC_ATTR_NAME] = OCA_DSUI_LOG

		logger_dict                  = {}
		logger_dict[OCA_TYPE]        = OCA_DSUI_THREAD_LOGGING
		logger_dict[OCA_ARG_PID]     = OCA_pid
		logger_dict[OCA_ARG_AC_NAME] = OCA_DSUI_LOG
		self.send_OCA_evt(logger_dict, entity.get_log_time())

	def __evt_dsui_buffer(self, entity):
		"""
		These events announce the original pid of some relevant DSUI 
		threads. We replace the thread name with this information where 
		appropriate
		"""	
		OCA_pid = self.pid2OCA(entity.get_tag())
		
		if not self.ACS.has_key(OCA_pid):
			print "ERROR: Got a bad DSUI_BUFFERING_THREAD event with" \
					"unknown OCA_pid: %d" % OCA_pid
			raise AssertionError

		self.ACS[OCA_pid][AC_ATTR_NAME] = OCA_DSUI_BUF

		buffering_thread_dict                  = {}
		buffering_thread_dict[OCA_TYPE]        = OCA_DSUI_THREAD_BUFFER
		buffering_thread_dict[OCA_ARG_PID]     = OCA_pid
		buffering_thread_dict[OCA_ARG_AC_NAME] = OCA_DSUI_BUF
		self.send_OCA_evt(buffering_thread_dict, entity.get_log_time())
	
###############################################################################
# VFS Definitions
###############################################################################

	def __evt_open(self, entity):
		"""
		Open event
		"""
		# TODO: Finish this instrumentation. Get flags argument and
		# return value, and write string converter to interpret them
		# TODO: Handle new OCA_pids being added via file communication
		#
		data      = entity.get_extra_data()
		OCA_pid   = self.pid2OCA(entity.get_pid())
		fd 	  = data["fd"]
		mode 	  = data["mode"]
		inode_id  = data["inode_id"]
		sys_id 	  = data["sys_id"]
		filename  = data["filename"]
		open_id   = (sys_id, inode_id)
		
		for unClassifiedExtension in self.unClassifiedExten:
			if filename.find(unClassifiedExtension) >-1:
				self.unClassified[filename] = fd
				return
	        #print "File open : ", filename

			
		if not self.ACS.has_key(OCA_pid):
			print >> self.outfile, "ERROR: Got open on unknown OCA_pid"
			raise AssertionError

		AC_ref_id = (self.ACS[OCA_pid][AC_ATTR_FILE_GID], fd)
		AC_ref   	     = {}
		AC_ref[AC_REF_ID]    = (OCA_pid, fd)
		AC_ref[AC_REF_MODE]  = fileMode2String(mode)
		AC_ref[AC_REF_READ]  = 0
		AC_ref[AC_REF_WROTE] = 0

		open_dict = {}

		if not self.PCS.has_key(open_id):
			# We haven't seen this PC yet, so create it.
			#
			# This is guaranteed to be either a normal PC_FILE or a
			# pseudo terminal type. FIFO's will always already be in 
			# the PCS (due to evt_fifo_open), and pipes and sockets do
			# not use sys_open to open file descriptors
			#
			if sys_id == PC_DEVPTS_FS:
				self.create_PC_record(PC_PSEUDOT, open_id, filename)
			else:
				self.create_PC_record(PC_FILE, open_id, filename)
	
		# Update our data structures to reflect that the calling AC now has
		# a reference to the opened PC
		#
		self.PCS[open_id][PC_ATTR_OPEN_REFS].append(AC_ref)
		self.ACS[OCA_pid][AC_ATTR_FDS][fd] = self.PCS[open_id]
		
		if filename.find(self.sharedFileExtension) >-1:
			open_dict[OCA_TYPE] = OCA_SHARED_FILE_OPEN
		else: 
			open_dict[OCA_TYPE] = OCA_OPEN

		open_dict[OCA_ARG_PID]     = OCA_pid
		open_dict[OCA_ARG_AC_ID]   = OCA_pid
		open_dict[OCA_ARG_FD]      = fd
		open_dict[OCA_ARG_MODE]    = AC_ref[AC_REF_MODE]
		open_dict[OCA_ARG_AC_NAME] = self.ACS[OCA_pid][AC_ATTR_NAME]
		open_dict[OCA_ARG_PC_ID]   = open_id
		open_dict[OCA_ARG_PC_TYPE] = self.PCS[open_id][PC_TYPE]
		open_dict[OCA_ARG_PC_NAME] = self.PCS[open_id][PC_ATTR_NAME]

		self.send_OCA_evt(open_dict, entity.get_log_time())
		
		if self.print_level >= MAX_PRINT_LEVEL:
			print >> self.outfile, "OPEN: OCA_pid %d opened %s" % (OCA_pid, self.PCS[open_id][PC_ATTR_NAME])
			self.print_ACS()
			self.print_PCS()

	def __evt_close(self, entity):

		# TODO: Add UNKNOWN close / read / write OCA events for
		# nonfamilial records
		#
		data      = entity.get_extra_data()
		OCA_pid   = self.pid2OCA(entity.get_pid())
		inode_id  = data["inode_id"]
		sys_id    = data["sys_id"]
		fd        = data["fd"]
		filename  = data["filename"]
		close_id  = (sys_id, inode_id)

		for unClassifiedExtension in self.unClassifiedExten:
			if filename.find(unClassifiedExtension) >-1:
				if self.unClassified.has_key(filename):
					del self.unClassified[filename]
				return
		#print "File Close : ", filename


		close_dict = {}

		if filename.find(self.sharedFileExtension) >-1:
			close_dict[OCA_TYPE] = OCA_SHARED_FILE_CLOSE
		else: 
			close_dict[OCA_TYPE] = OCA_CLOSE
	
		close_dict[OCA_ARG_PID]     = OCA_pid
		close_dict[OCA_ARG_AC_ID]   = OCA_pid
		close_dict[OCA_ARG_PC_ID]   = close_id
		#FIXME:
#		Check this out:
		#close_dict[OCA_ARG_PC_NAME] = filename
		#close_dict[OCA_ARG_PC_TYPE] = PC_UNKNOWN
		close_dict[OCA_ARG_FD]      = fd

		# Do we have a reference to this active component?
		#
		if not self.ACS.has_key(OCA_pid):
			print "ERROR: Got close event from unknown OCA_pid: %d" % OCA_pid
			raise AssertionError

		AC_ref_id = (self.ACS[OCA_pid][AC_ATTR_FILE_GID], fd)
		# Do we have a reference to this passive component?
		#
		if not self.PCS.has_key(close_id):
			if self.ACS[OCA_pid][AC_ATTR_RELATION] == AC_FAMILIAL_TASK:
				print "Error: Familial AC %d closed on fd %d a PC we did not " \
						"know about. PC_id: (%s, %d)" % (OCA_pid, fd, sys_id, inode_id)
				return
			else:
				print "Nonfamilial AC %d closed fd %d for unknown PC " \
						"(%s, %d)" % (OCA_pid, fd, sys_id, inode_id)
				self.send_OCA_evt(close_dict, entity.get_log_time())
				return
			
		# Do we have a reference to this file descriptor?
		#
		if not self.ACS[OCA_pid][AC_ATTR_FDS].has_key(fd):
			if self.ACS[OCA_pid][AC_ATTR_RELATION] == AC_FAMILIAL_TASK:
				print "Error: A familial AC closed a fd we did not " \
						"know about. AC_ref: (%d, %d)" % AC_ref_id
				return
			else:
				print "Nonfamilial AC %d closed unknown fd %d for PC " \
						"(%s, %d)" % (OCA_pid, fd, sys_id, inode_id)
				self.send_OCA_evt(close_dict, entity.get_log_time())
				return
	
		# Does our AC have an open reference to this PC?
		#
		if not self.ACS[OCA_pid][AC_ATTR_FDS][fd][PC_ATTR_PC_ID] == close_id:
			print "ERROR: Got a close event an fd %d that AC %d did not " \
					"have open" % (fd, OCA_pid)
			raise AssertionError

		# Remove the reference to it from self.ACS, but not the 
		# actual PC
		#
		self.ACS[OCA_pid][AC_ATTR_FDS][fd] = {}
		del self.ACS[OCA_pid][AC_ATTR_FDS][fd]

		# And remove the reference to the AC from the PCs list
		#
		for item in self.PCS[close_id][PC_ATTR_OPEN_REFS]:
			if item[AC_REF_ID] == AC_ref_id:
				closed_ref = copy.deepcopy(item)
				self.PCS[close_id][PC_ATTR_CLOSED_REFS].append(closed_ref)
				self.PCS[close_id][PC_ATTR_OPEN_REFS].remove(item)

		# FIXME: This is wrong. If all references to a file close, and
		# an AC reopens the file, it is recorded as a new file. We need
		# to keep this file in the PC list, and just remove references to
		# it.

		# After closing the last reference to a pipe or socket, we need
		# to remove it from our structures (or somehow mark it as destroyed)
		#
		# FIXME:
		# check this out.
		#if not self.PCS[close_id][PC_ATTR_AC_REFS]:
		#	del self.PCS[close_id]

		if self.print_level >= MAX_PRINT_LEVEL:
			print >> self.outfile, "CLOSE: OCA_pid %d closed %s" % (OCA_pid, self.PCS[close_id][PC_ATTR_NAME])
			self.print_ACS()
			self.print_PCS()
		
		self.send_OCA_evt(close_dict, entity.get_log_time())

	def __evt_read_info(self, entity):

		data          = entity.get_extra_data()
		OCA_pid       = self.pid2OCA(entity.get_pid())
		inode_id      = data["inode_id"]
		sys_id        = data["sys_id"]
		fd            = data["fd"]
		filename      = data["filename"]
		size          = data["return"]
		PC_id         = (sys_id, inode_id)

		if filename in self.unClassified.keys():
			self.readDicts[OCA_pid] = "unClassified"
			return

		if self.read_data_ptr.get_cid() != -1:
			#
			# Gathered rw_data with separate instrumentation point
			#
			if self.readDicts.has_key(OCA_pid):
				print "Error: got a read_info event before " \
						"getting a corresponding read_data event\n" \
						"Old Read Info:", self.readDicts[OCA_pid]
				print "Writing over with new Read Info:", data
	
			self.readDicts[OCA_pid]                  = {}

			if filename.find(self.sharedFileExtension) >-1:
				self.readDicts[OCA_pid][OCA_TYPE]        = OCA_SHARED_FILE_READ
			else:
				self.readDicts[OCA_pid][OCA_TYPE]        = OCA_READ

			self.readDicts[OCA_pid][OCA_ARG_PID]     = OCA_pid
			self.readDicts[OCA_pid][OCA_ARG_AC_ID]   = OCA_pid
			self.readDicts[OCA_pid][OCA_ARG_PC_ID]   = PC_id
			#FIXME:
#			Check this out:
			#self.readDicts[OCA_pid][OCA_ARG_PC_NAME] = filename
			#self.readDicts[OCA_pid][OCA_ARG_PC_TYPE] = PC_UNKNOWN
			self.readDicts[OCA_pid][OCA_ARG_FD]      = fd
			self.readDicts[OCA_pid][OCA_ARG_SIZE]    = size
		else:
			#
			# Did not gather rw_data with separate instrumentation point
			#
			readDict                  = {}
			readDict[OCA_TYPE]        = OCA_READ
			readDict[OCA_ARG_PID]     = OCA_pid
			readDict[OCA_ARG_AC_ID]   = OCA_pid
			readDict[OCA_ARG_PC_ID]   = PC_id
			#readDict[OCA_ARG_PC_NAME] = filename
			#readDict[OCA_ARG_PC_TYPE] = PC_UNKNOWN
			readDict[OCA_ARG_FD]      = fd
			readDict[OCA_ARG_SIZE]    = size
			self.send_OCA_evt(readDict, entity.get_log_time())

		
		self.__update_AC_ref_read(OCA_pid, fd, PC_id, size)
	
	def __evt_write_info(self, entity):
		
		data           = entity.get_extra_data()
		OCA_pid        = self.pid2OCA(entity.get_pid())
		inode_id       = data["inode_id"]
		sys_id         = data["sys_id"]
		fd             = data["fd"]
		filename       = data["filename"]
		size           = data["return"]
		PC_id          = (sys_id, inode_id)
			
		if filename in self.unClassified.keys():
			self.writeDicts[OCA_pid] = "unClassified"
			return

		if self.write_data_ptr.get_cid() != -1:
			#
			# Gathered rw_data with separate instrumentation point
			#
			if self.writeDicts.has_key(OCA_pid):
				print "Error: got a write_info event before " \
						"getting a corresponding read_data event\n" \
						"Old Write Info:", self.writeDicts[OCA_pid]
				print "Writing over with new Write Info:", data
			
			self.writeDicts[OCA_pid]                  = {}	

			if filename.find(self.sharedFileExtension) >-1:
				self.writeDicts[OCA_pid][OCA_TYPE]        = OCA_SHARED_FILE_WRITE
			else:
				self.writeDicts[OCA_pid][OCA_TYPE]        = OCA_WRITE

			self.writeDicts[OCA_pid][OCA_TYPE]        = OCA_WRITE
			self.writeDicts[OCA_pid][OCA_ARG_PID]     = OCA_pid
			self.writeDicts[OCA_pid][OCA_ARG_AC_ID]   = OCA_pid
			self.writeDicts[OCA_pid][OCA_ARG_PC_ID]   = PC_id
			#self.writeDicts[OCA_pid][OCA_ARG_PC_NAME] = filename
			#self.writeDicts[OCA_pid][OCA_ARG_PC_TYPE] = PC_UNKNOWN
			self.writeDicts[OCA_pid][OCA_ARG_FD]      = fd
			self.writeDicts[OCA_pid][OCA_ARG_SIZE]    = size
		else:
			#
			# Did not gather rw_data with separate instrumentation point
			#
			writeDict                  = {}	
			writeDict[OCA_TYPE]        = OCA_WRITE
			writeDict[OCA_ARG_PID]     = OCA_pid
			writeDict[OCA_ARG_AC_ID]   = OCA_pid
			writeDict[OCA_ARG_PC_ID]   = PC_id
			#writeDict[OCA_ARG_PC_NAME] = filename
			#writeDict[OCA_ARG_PC_TYPE] = PC_UNKNOWN
			writeDict[OCA_ARG_FD]      = fd
			writeDict[OCA_ARG_SIZE]    = size
			self.send_OCA_evt(writeDict, entity.get_log_time())

		self.__update_AC_ref_write(OCA_pid, fd, PC_id, size)
		
	def __evt_read_data(self, entity):
	
		data    = entity.get_extra_data()
		OCA_pid = self.pid2OCA(entity.get_pid())
		if self.readDicts[OCA_pid] == "unClassified":
			del self.readDicts[OCA_pid]
			return
		elif self.readDicts[OCA_pid] == "Shared File":
			del self.readDicts[OCA_pid]
			return
		if not self.readDicts.has_key(OCA_pid):
			print "ERROR: got a read_data event without a " \
					"matching read_info event. Skipping ..."
			return
		#raise AssertionError

		self.readDicts[OCA_pid][OCA_READ_WRITE_DATA] = data
		self.send_OCA_evt(self.readDicts[OCA_pid], entity.get_log_time())
		del self.readDicts[OCA_pid]

	def __evt_write_data(self, entity):

		data    = entity.get_extra_data()
		OCA_pid = self.pid2OCA(entity.get_pid())
		if self.writeDicts[OCA_pid] == "unClassified":
			del self.writeDicts[OCA_pid]
			return
		elif self.writeDicts[OCA_pid] == "Shared File":
			del self.writeDicts[OCA_pid]
			return
		if not self.writeDicts.has_key(OCA_pid):
			print "ERROR: got a write_data event without a" \
					"matching write_info event. Skipping ..."
			return
		#raise AssertionError

		self.writeDicts[OCA_pid][OCA_READ_WRITE_DATA] = data
		self.send_OCA_evt(self.writeDicts[OCA_pid], entity.get_log_time())
		del self.writeDicts[OCA_pid]
	
	def __evt_readv(self, entity):

		data     = entity.get_extra_data()
		OCA_pid  = self.pid2OCA(entity.get_pid())
		inode_id = data["inode_id"]
		sys_id   = data["sys_id"]
		fd       = data["fd"]
		filename = data["filename"]
		bufnum   = data["size"]
		size     = data["return"]
		PC_id    = (sys_id, inode_id)
	
		readv_dict = {}
		readv_dict[OCA_TYPE]        = OCA_READV
		readv_dict[OCA_ARG_PID]     = OCA_pid
		readv_dict[OCA_ARG_AC_ID]   = OCA_pid
		readv_dict[OCA_ARG_PC_ID]   = PC_id
		#readv_dict[OCA_ARG_PC_NAME] = filename
		#readv_dict[OCA_ARG_PC_TYPE] = PC_UNKNOWN
		readv_dict[OCA_ARG_FD]      = fd
		readv_dict[OCA_ARG_SIZE]    = size

		self.__update_AC_ref_read(OCA_pid, fd, PC_id, size)
		self.send_OCA_evt(readv_dict, entity.get_log_time())
	
	def __evt_writev(self, entity):

		data     = entity.get_extra_data()
		OCA_pid  = self.pid2OCA(entity.get_pid())
		inode_id = data["inode_id"]
		sys_id   = data["sys_id"]
		fd       = data["fd"]
		filename = data["filename"]
		bufnum   = data["size"]
		size     = data["return"]
		PC_id    = (sys_id, inode_id)
	
		writev_dict = {}
		writev_dict[OCA_TYPE]        = OCA_WRITEV
		writev_dict[OCA_ARG_PID]     = OCA_pid
		writev_dict[OCA_ARG_AC_ID]   = OCA_pid
		writev_dict[OCA_ARG_PC_ID]   = PC_id
		#writev_dict[OCA_ARG_PC_NAME] = filename
		#writev_dict[OCA_ARG_PC_TYPE] = PC_UNKNOWN
		writev_dict[OCA_ARG_FD]      = fd
		writev_dict[OCA_ARG_SIZE]    = size

		self.__update_AC_ref_write(OCA_pid, fd, PC_id, size)	
		self.send_OCA_evt(writev_dict, entity.get_log_time())
	
	def __evt_dup(self, entity):
		"""
		This corresponds to both dup and dup2. dup has to be preprocessed in
		the active filter to get the old fd attached to the event. NOTE: dup2
		does not call fd_install.
		"""
		data      = entity.get_extra_data()
		OCA_pid   = self.pid2OCA(entity.get_pid())
		oldfd 	  = data["old_fd"]
		newfd     = data["new_fd"]
		mode 	  = data["mode"]
		inode_id  = data["inode_id"]
		sys_id 	  = data["sys_id"]
		filename  = data["filename"]
		open_id   = (sys_id, inode_id)


		if not self.ACS[OCA_pid][AC_ATTR_FDS].has_key(oldfd):
			if self.ACS[OCA_pid][AC_ATTR_RELATION] == AC_FAMILIAL_TASK:
				print "ERROR: Familial task duped an unknown FD." \
					"PID: %d, FD: %d" % (OCA_pid, oldfd)
				raise AssertionError
			else:
				print "Nonfamilial AC %d duped FD %d." % (OCA_pid, oldfd)
				return
		
		if not self.PCS.has_key(open_id):
			if self.ACS[OCA_pid][AC_ATTR_RELATION] == AC_FAMILIAL_TASK:
				print "ERROR: Familial task duped an unknown PC." \
					"PID: %d, PC: (%s, %d)" % (OCA_pid, sys_id, inode_id)
				raise AssertionError
			else:
				print "Nonfamilial AC %d duped PC (%s %d)." % (OCA_pid, sys_id, inode_id)
				return
			
		# Dups are considered to be a new AC reference
		#
		AC_ref_id = (self.ACS[OCA_pid][AC_ATTR_FILE_GID], newfd)
		AC_ref   	      = {}
		AC_ref[AC_REF_ID]     = AC_ref_id
		AC_ref[AC_REF_MODE]   = fileMode2String(mode)
		AC_ref[AC_REF_READ]   = 0
		AC_ref[AC_REF_WROTE]  = 0

		if self.ACS[OCA_pid][AC_ATTR_FDS].has_key(newfd):
			# This means a reference to this newfd was not closed before
			# dup was called. Change the AC_ref on the PC to show that 
			# this reference is now closed.
			#
			old_PC_entry = self.ACS[OCA_pid][AC_ATTR_FDS][newfd]
			for item in old_PC_entry[PC_ATTR_OPEN_REFS]:
				if item[AC_REF_ID] == AC_ref_id:
					closed_ref = copy.deepcopy(item)
					old_PC_entry[PC_ATTR_CLOSED_REFS].append(closed_ref)
					old_PC_entry[PC_ATTR_OPEN_REFS].remove(item)	

		# Replace the existing AC reference with a reference
		# to where the fd now points
		#
		self.ACS[OCA_pid][AC_ATTR_FDS][newfd] = self.ACS[OCA_pid][AC_ATTR_FDS][oldfd]

		# Add the new AC_ref to the list of AC_refs on the PC
		#
		self.PCS[open_id][PC_ATTR_OPEN_REFS].append(AC_ref)

		# XXX: Should we emit OCA events from here?

		if self.print_level >= MAX_PRINT_LEVEL:
			print >> self.outfile, "DUP: OCA %d duped %d --> %d" % (OCA_pid, oldfd, newfd)
			self.print_ACS()
			self.print_PCS()
	
	def __evt_fcntl(self, entity):
		
		# TODO: This needs to be reviewed and updated
		data = entity.get_extra_data()
		#ret  = data["ret"]
		
		#if ret:
			# TODO: Handle error cases
		#	return

		sys_id = data["sys_id"]
		inode_id = data["inode_id"]

		PC_id = (sys_id, inode_id)
		
		fLockDict={}

		if fctlLocking2String[data["cmd"]] == "F_SETLKW" or fctlLocking2String[data["cmd"]] == "LOCK_EX":
			fLockDict[OCA_TYPE] = OCA_FCNTL_LOCK
			if self.PCS.has_key(PC_id):
				self.PCS[PC_id][PC_ATTR_LOCKED] = True

		if fctlLocking2String[data["cmd"]] == "F_SETLK" or fctlLocking2String[data["cmd"]] == "LOCK_UN":

			fLockDict[OCA_TYPE] = OCA_FCNTL_UNLOCK
			if self.PCS.has_key(PC_id):
				self.PCS[PC_id][PC_ATTR_LOCKED] = False

		fLockDict[OCA_ARG_PID] = entity.get_pid()
		fLockDict[OCA_ARG_PC_NAME] = data["filename"]
		fLockDict[OCA_ARG_PC_ID] = PC_id

		id = entities.Event(self.OCA_actions_ptr.get_cid(),entity.get_log_time(),0,fLockDict,0)
		self.send_output("default",id)

	def __evt_select(self, entity):
		data        = entity.get_extra_data()
		OCA_pid     = self.pid2OCA(entity.get_pid())
		in_fds      = data["in"]
		out_fds     = data["out"]
		ex_fds      = data["ex"]
		res_in_fds  = data["res_in"]
		res_out_fds = data["res_out"]
		res_ex_fds  = data["res_ex"]

		print "In _fds : ", in_fds
		print "Changed In _fds ", res_in_fds
		
		for i in range(32):
			mask = 1 << i
			print "fd in selection is ", (res_in_fds & mask)
			mask = 0 << i
	
	def __evt_fd_install(self, entity):
		"""
		This simply asserts that we have a record of the installed
		fd before we log this instrumentation point.
		"""
		
		OCA_pid = self.pid2OCA(entity.get_pid())
		fd = entity.get_tag()
		
		if not self.ACS.has_key(OCA_pid):
			print "Got fd_install from unknown AC. fd %d" % fd
			raise AssertionError
		
		if fd in self.unClassified.values():
			return

		if not self.ACS[OCA_pid][AC_ATTR_FDS].has_key(fd):
			print "WARNING: Got fd_install on AC %d for unknown fd %d" % (OCA_pid, fd)
			raise AssertionError

###############################################################################
# Pipe Definitions
###############################################################################

	def __evt_do_pipe(self, entity):
		"""
		Pipe event
		"""
		data 		= entity.get_extra_data()
		OCA_pid         = self.pid2OCA(entity.get_pid())
		inode_id 	= data["inode_id"]
		sys_id 		= data["sys_id"]
		rfd 		= data["read_fd"]
		wfd 		= data["write_fd"]
		r_mode		= data["r_mode"]
		w_mode		= data["w_mode"]
		pipe_id   	= (sys_id, inode_id)
		
		assert not self.PCS.has_key(pipe_id)
		
		self.pipe_num += 1
		pipe_name = PC_PIPE_NAME_BASE % self.pipe_num
		self.create_PC_record(PC_PIPE, pipe_id, pipe_name)
		self.ACS[OCA_pid][AC_ATTR_FDS][rfd] = self.PCS[pipe_id]
		self.ACS[OCA_pid][AC_ATTR_FDS][wfd] = self.PCS[pipe_id]

		assert self.ACS.has_key(OCA_pid)
		read_AC_ref_id  = (self.ACS[OCA_pid][AC_ATTR_FILE_GID], rfd)
		read_AC_ref   	          = {}
		read_AC_ref[AC_REF_ID]    = read_AC_ref_id
		read_AC_ref[AC_REF_MODE]  = fileMode2String(r_mode)
		read_AC_ref[AC_REF_READ]  = 0
		read_AC_ref[AC_REF_WROTE] = 0

		write_AC_ref_id = (self.ACS[OCA_pid][AC_ATTR_FILE_GID], wfd)
		write_AC_ref   	           = {}
		write_AC_ref[AC_REF_ID]    = write_AC_ref_id
		write_AC_ref[AC_REF_MODE]  = fileMode2String(w_mode)
		write_AC_ref[AC_REF_READ]  = 0
		write_AC_ref[AC_REF_WROTE] = 0

		self.PCS[pipe_id][PC_ATTR_OPEN_REFS].append(read_AC_ref)
		self.PCS[pipe_id][PC_ATTR_OPEN_REFS].append(write_AC_ref)
	
		pipe_dict 		      = {}
		pipe_dict[OCA_TYPE] 	      = OCA_PIPE_CREATE
		pipe_dict[OCA_ARG_PID]	      = OCA_pid
		pipe_dict[OCA_ARG_AC_ID]      = OCA_pid
		pipe_dict[OCA_ARG_AC_NAME]    = self.ACS[OCA_pid][AC_ATTR_NAME]
		pipe_dict[OCA_ARG_PC_ID]      = pipe_id
		pipe_dict[OCA_ARG_PC_NAME]    = pipe_name
		pipe_dict[OCA_ARG_FD_READ]    = rfd
		pipe_dict[OCA_ARG_FD_WRITE]   = wfd
		pipe_dict[OCA_ARG_MODE_READ]  = read_AC_ref[AC_REF_MODE]
		pipe_dict[OCA_ARG_MODE_WRITE] = write_AC_ref[AC_REF_MODE]
		
		self.send_OCA_evt(pipe_dict, entity.get_log_time())
		
		if self.print_level >= MAX_PRINT_LEVEL:
			print >> self.outfile, "PIPE: OCA_PID %d, rfd %d, wfd %d)" % (OCA_pid, rfd, wfd)
			self.print_ACS()
			self.print_PCS()
	
###############################################################################
# FIFO Definitions
###############################################################################

	def __evt_fifo_open(self, entity):
		"""
		This creates the Named Pipe PCS record so that when the open event
		comes through we know this is a named pipe.
		"""
		data     = entity.get_extra_data()
		inode_id = data["inode_id"]
		sys_id 	 = data["sys_id"]
		filename = data["filename"]
		PC_id    = (sys_id, inode_id)

		if not self.PCS.has_key(PC_id):
			self.create_PC_record(PC_FIFO, PC_id, filename)
		
		OCA_pid = self.pid2OCA(entity.get_pid())

###############################################################################
# IPC Shared Memory Definitions
###############################################################################

	def __evt_shmat_add(self, entity):
		"""
		An event announcing that our active filter has added a member to the
		group we are tracing because of a socket connection.
		"""
		OCA_pid = self.pid2OCA(entity.get_pid(), OCA_PID_CREATE)
		self.create_AC_record(None, OCA_pid, AC_SHMEM_REL)

		self.ACS[OCA_pid][AC_ATTR_EXEC_NAME] = entity.get_extra_data()

		OCA_dict = {}
		OCA_dict[OCA_TYPE]      = OCA_SHMAT_ADD
		OCA_dict[OCA_ARG_PID]   = OCA_pid
		OCA_dict[OCA_ARG_AC_ID] = OCA_pid
		OCA_dict[OCA_ARG_GEN]   = AC_NONFAMILIAL_TASK
		OCA_dict[OCA_ARG_REL]   = AC_SHMEM_REL

		self.send_OCA_evt(OCA_dict, entity.get_log_time())
		
	
	def __evt_shmget(self, entity):
		"""
		shmget event
		"""

		# XXX: The way we are handling the PCS right now is that we are creating
		# entries when an AC gets access to an entry with the open system call.
		# This is much more analogous to the shmat function than shmget (which
		# creates the shm segment). We should instrument PC creation and deletion
		# and distinguish this clearly from reference creation and deletion.
		#
		"""data = entity.get_extra_data()
		# shmget returns the shmid
		shmid = data["ret"]
		key = data["key"]

		# TODO: Instrument shmctl to note when a shared memory segment is destroyed.
		if not self.shmids.has_key(shmid):
			self.shmids[shmid] = "SHM %d" % self.shm_num
			self.shm_num = self.shm_num + 1

		shmgetDict = {}
		shmgetDict[OCA_TYPE] = OCA_SHM_GET
		shmgetDict[OCA_ARG_PID] = entity.get_pid()
		shmgetDict[OCA_ARG_SHM_ID] = shmid
		shmgetDict[OCA_ARG_SHM_NAME] = self.shmids[shmid]

		if key is IPC_PRIVATE:
			shmgetDict[OCA_ARG_SHM_KEY] = shmStringTable[IPC_PRIVATE]
		else:
			shmgetDict[OCA_ARG_SHM_KEY] = key

		shmgetDict[OCA_ARG_SHM_SIZE] = data["size"]
		shmgetDict[OCA_ARG_SHM_FLAGS] = shmgetFlags2String(data["flags"])
		id = entities.Event(self.OCA_actions_ptr.get_cid(),entity.get_log_time(),0,shmgetDict,0)
		self.send_output("default",id)"""

	def __evt_shmat(self, entity):
		"""
		shmat event
		"""
		# I have pretty high confidence that shmid and inode id are always
		# the same. We are building the graph off of the sys_id, inode_id
		# pair, so get rid of shmid if we determine we have no use for it.
		#
		data      = entity.get_extra_data()
		OCA_pid   = self.pid2OCA(entity.get_pid())
		flags     = data["flags"]
		shmid     = data["shmid"]
		shmaddr   = data["shmaddr"]
		inode_id  = data["inode_id"]
		sys_id    = data["sys_id"]
		ret       = data["err"]
		seg_id    = (sys_id, inode_id)
		
		if not self.ACS.has_key(OCA_pid):
			print "ERROR: Got shmat evt for unknown OCA_pid %d" % OCA_pid
			raise AssertionError

		if not self.PCS.has_key(seg_id):
			self.shm_num += 1
			name = PC_SHM_NAME_BASE % self.shm_num
			self.create_PC_record(PC_SHM, seg_id, name)
			
		AC_ref_id = (self.ACS[OCA_pid][AC_ATTR_SHM_GID], shmaddr)
		AC_ref              = {}
		AC_ref[AC_REF_ID]   = AC_ref_id
		AC_ref[AC_REF_MODE] = flags

		self.PCS[seg_id][PC_ATTR_OPEN_REFS].append(AC_ref)
		self.ACS[OCA_pid][AC_ATTR_SHMATS][shmaddr] = self.PCS[seg_id]

		shmat_dict                   = {}
		shmat_dict[OCA_TYPE]         = OCA_SHM_ATTACH
		shmat_dict[OCA_ARG_PID]      = OCA_pid
		shmat_dict[OCA_ARG_AC_ID]    = OCA_pid
		shmat_dict[OCA_ARG_AC_NAME]  = self.ACS[OCA_pid][AC_ATTR_NAME]
		shmat_dict[OCA_ARG_PC_ID]    = seg_id
		shmat_dict[OCA_ARG_PC_NAME]  = self.PCS[seg_id][PC_ATTR_NAME]
		shmat_dict[OCA_ARG_SHM_ID]   = shmid
		shmat_dict[OCA_ARG_SHM_ADDR] = shmaddr
		shmat_dict[OCA_ARG_MODE]     = shmatFlags2String(flags)
		shmat_dict[OCA_ARG_RET]      = ret
			
		if self.print_level >= MAX_PRINT_LEVEL:
			print >> self.outfile, "SHMAT: OCA_pid %d attached %s" % (OCA_pid, self.PCS[seg_id][PC_ATTR_NAME])
			self.print_ACS()
			self.print_PCS()

		self.send_OCA_evt(shmat_dict, entity.get_log_time())

	def __evt_shmdt(self, entity):
		"""
		shmdt event
		"""

		data      = entity.get_extra_data()
		OCA_pid   = self.pid2OCA(entity.get_pid())
		shmaddr   = data["shmaddr"]
		inode_id  = data["inode_id"]
		sys_id    = data["sys_id"]
		ret       = data["ret"]
		seg_id    = (sys_id, inode_id)
	
		shmdt_dict                   = {}
		shmdt_dict[OCA_TYPE]         = OCA_SHM_DETACH
		shmdt_dict[OCA_ARG_PID]      = OCA_pid
		shmdt_dict[OCA_ARG_AC_ID]    = OCA_pid
		shmdt_dict[OCA_ARG_AC_NAME]  = self.ACS[OCA_pid][AC_ATTR_NAME]
		shmdt_dict[OCA_ARG_PC_ID]    = seg_id
		shmdt_dict[OCA_ARG_SHM_ADDR] = shmaddr
		shmdt_dict[OCA_ARG_RET]      = ret
		
		if not self.PCS.has_key(seg_id):
			if self.ACS[OCA_pid][AC_ATTR_RELATION] == AC_FAMILIAL_TASK:
				print "Error: Familial AC %d detached from a shm seg we did not " \
					"know about. User Address: %d. PC_id: (%s, %d)" % (OCA_pid, sys_id, inode_id)
				raise AssertionError
			else:
				print "Nonfamilial AC %d detached from a shm seg we did not know " \
					"about. PC_id: (%s, %d)" % (OCA_pid, sys_id, inode_id)

				self.send_OCA_evt(shmdt_dict, entity.get_log_time())
				return
		
		shmdt_dict[OCA_ARG_PC_NAME]  = self.PCS[seg_id][PC_ATTR_NAME]
		# The AC must have known about the shm seg before getting a detach evt
		#
		if not self.ACS[OCA_pid][AC_ATTR_SHMATS].has_key(shmaddr):
			if self.ACS[OCA_pid][AC_ATTR_RELATION] == AC_FAMILIAL_TASK:
				print "ERROR: Familial AC %d detached from shmaddr %d " \
					"it was not attached to. PC_ID: (%s, %d)" % (OCA_pid, \
					shmaddr, sys_id, inode_id)
				raise AssertionError
			else:
				print "Nonfamilial AC %d detached from shmaddr %d it was not " \
					"attached to. PC_ID: (%s, %d)" % (OCA_pid, shmaddr, \
				       sys_id, inode_id)
				self.send_OCA_evt(shmdt_dict, entity.get_log_time())
				return

		# The AC must have known about the shm seg before getting a detach evt
		#
		known_seg_id = self.ACS[OCA_pid][AC_ATTR_SHMATS][shmaddr][PC_ATTR_PC_ID]	
		if not known_seg_id == seg_id:
			print "The shm address AC %d is detaching from does not point to " \
				"the seg_id in my records. SHMADDR: %d, Known seg_id: (%s, %d) " \
				"Given seg_id: (%s, %d)" % (OCA_pid, shmaddr, known_seg_id[0], \
				known_seg_id[1], seg_id[0], seg_id[1])
			raise AssertionError

		# Remove the reference to it from self.ACS, but not the 
		# actual PC
		#
		self.ACS[OCA_pid][AC_ATTR_SHMATS][shmaddr] = {}
		del self.ACS[OCA_pid][AC_ATTR_SHMATS][shmaddr]

		# And remove the reference to the AC from the PCs list
		#
		AC_ref_id = (self.ACS[OCA_pid][AC_ATTR_SHM_GID], shmaddr)
		for item in self.PCS[seg_id][PC_ATTR_OPEN_REFS]:
			if item[AC_REF_ID] == AC_ref_id:
				closed_ref = copy.deepcopy(item)
				self.PCS[seg_id][PC_ATTR_CLOSED_REFS].append(closed_ref)
				self.PCS[seg_id][PC_ATTR_OPEN_REFS].remove(item)

		# TODO: We need to instrument the creation and destruction of
		# the actual PC in memory

		#if not self.PCS[seg_id][PC_ATTR_AC_REFS]:
		#	del self.PCS[seg_id]

		if self.print_level >= MAX_PRINT_LEVEL:	
			print >> self.outfile, "SHMDT: OCA_pid %d detached %s" % (OCA_pid, self.PCS[seg_id][PC_ATTR_NAME])
			self.print_ACS()
			self.print_PCS()

		self.send_OCA_evt(shmdt_dict, entity.get_log_time())

###############################################################################
# Ptrace Definitions
###############################################################################
	
	def __evt_ptrace(self, entity):
		"""
		Ptrace event. In here, we currently only process events with requests
		that alter master / slave relationships.
		"""
		data            = entity.get_extra_data()
		OCA_pid         = self.pid2OCA(entity.get_pid())
		request         = ptraceRequest2String(data["request"])
		arg_pid         = data["pid"]
		parent_pid      = data["parent_pid"]
		addr            = data["addr"]
		arg_data        = data["data"]
		ret             = data["ret"]
		ptrace_OCA_dict = {}

		# TODO: Take out hard coded strings
		# Give print outs to each assert as done above

		assert self.ACS.has_key(OCA_pid)
		if request == "PTRACE_TRACEME":
			OCA_parent_pid = self.pid2OCA(parent_pid)
			assert self.ACS.has_key(OCA_parent_pid)

			if OCA_parent_pid not in self.ACS[OCA_pid][AC_ATTR_MASTERS]:
				self.ACS[OCA_pid][AC_ATTR_MASTERS].append(OCA_parent_pid)
			if OCA_pid not in self.ACS[OCA_parent_pid][AC_ATTR_SLAVES]:
				self.ACS[OCA_parent_pid][AC_ATTR_SLAVES].append(OCA_pid)

			ptrace_OCA_dict[OCA_TYPE]               = OCA_PTRACE_ATTACH
			ptrace_OCA_dict[OCA_PTRACE_MASTER_ID]   = OCA_parent_pid
			ptrace_OCA_dict[OCA_PTRACE_MASTER_NAME] = self.ACS[OCA_parent_pid][AC_ATTR_NAME]
			ptrace_OCA_dict[OCA_PTRACE_MASTER_TYPE] = self.ACS[OCA_parent_pid][AC_TYPE]
			ptrace_OCA_dict[OCA_PTRACE_SLAVE_ID]    = OCA_pid
			ptrace_OCA_dict[OCA_PTRACE_SLAVE_NAME]  = self.ACS[OCA_pid][AC_ATTR_NAME]
			ptrace_OCA_dict[OCA_PTRACE_SLAVE_TYPE]  = self.ACS[OCA_pid][AC_TYPE]

		elif request == "PTRACE_ATTACH":
			OCA_arg_pid = self.pid2OCA(arg_pid, OCA_PID_CREATE)
			if not self.ACS.has_key(OCA_arg_pid):
				self.create_nonfamilial_AC_record(OCA_arg_pid)

			if OCA_pid not in self.ACS[OCA_arg_pid][AC_ATTR_MASTERS]:
				self.ACS[OCA_arg_pid][AC_ATTR_MASTERS].append(OCA_pid)
			if OCA_arg_pid not in self.ACS[OCA_pid][AC_ATTR_SLAVES]:
				self.ACS[OCA_pid][AC_ATTR_SLAVES].append(OCA_arg_pid)

			ptrace_OCA_dict[OCA_TYPE]               = OCA_PTRACE_ATTACH
			ptrace_OCA_dict[OCA_PTRACE_MASTER_ID]   = OCA_pid
			ptrace_OCA_dict[OCA_PTRACE_MASTER_NAME] = self.ACS[OCA_pid][AC_ATTR_NAME]
			ptrace_OCA_dict[OCA_PTRACE_MASTER_TYPE] = self.ACS[OCA_pid][AC_TYPE]
			ptrace_OCA_dict[OCA_PTRACE_SLAVE_ID]    = OCA_arg_pid
			ptrace_OCA_dict[OCA_PTRACE_SLAVE_NAME]  = self.ACS[OCA_arg_pid][AC_ATTR_NAME]
			ptrace_OCA_dict[OCA_PTRACE_SLAVE_TYPE]  = self.ACS[OCA_arg_pid][AC_TYPE]
			
		elif request == "PTRACE_DETACH":
			OCA_arg_pid = self.pid2OCA(arg_pid, OCA_PID_CREATE)
			
			if self.ACS[OCA_pid][AC_ATTR_RELATION] == AC_FAMILIAL_TASK:
				assert self.ACS.has_key(OCA_arg_pid)
			elif not self.ACS.has_key(OCA_arg_pid):
				print "Nonfamilial AC %d detached from unknown pid %d" % (OCA_pid, arg_pid)
				return

			if not OCA_arg_pid in self.ACS[OCA_pid][AC_ATTR_SLAVES]:
				print "WARNING: Detaching PID: %d not on slaves list" \
						% (OCA_arg_pid)
				return
			self.ACS[OCA_pid][AC_ATTR_SLAVES].remove(OCA_arg_pid)

			if not OCA_pid in self.ACS[OCA_pid][AC_ATTR_MASTERS]:
				print "WARNING: Detaching PID: %d not on masters list" \
						% (OCA_arg_pid)
				return
			self.ACS[OCA_arg_pid][AC_ATTR_MASTERS].remove(OCA_pid)

			ptrace_OCA_dict[OCA_TYPE]               = OCA_PTRACE_DETACH
			ptrace_OCA_dict[OCA_PTRACE_MASTER_ID]   = OCA_pid
			ptrace_OCA_dict[OCA_PTRACE_MASTER_NAME] = self.ACS[OCA_pid][AC_ATTR_NAME]
			ptrace_OCA_dict[OCA_PTRACE_MASTER_TYPE] = self.ACS[OCA_pid][AC_TYPE]
			ptrace_OCA_dict[OCA_PTRACE_SLAVE_ID]    = OCA_arg_pid
			ptrace_OCA_dict[OCA_PTRACE_SLAVE_NAME]  = self.ACS[OCA_arg_pid][AC_ATTR_NAME]
			ptrace_OCA_dict[OCA_PTRACE_SLAVE_TYPE]  = self.ACS[OCA_arg_pid][AC_TYPE]

		else:
			OCA_arg_pid = self.pid2OCA(arg_pid)
			assert self.ACS.has_key(OCA_arg_pid) and self.ACS.has_key(OCA_pid)

			ptrace_OCA_dict[OCA_TYPE]               = OCA_PTRACE_CONTROL
			ptrace_OCA_dict[OCA_PTRACE_MASTER_ID]   = OCA_pid
			ptrace_OCA_dict[OCA_PTRACE_MASTER_NAME] = self.ACS[OCA_pid][AC_ATTR_NAME]
			ptrace_OCA_dict[OCA_PTRACE_MASTER_TYPE] = self.ACS[OCA_pid][AC_TYPE]
			ptrace_OCA_dict[OCA_PTRACE_SLAVE_ID]    = OCA_arg_pid
			ptrace_OCA_dict[OCA_PTRACE_SLAVE_NAME]  = self.ACS[OCA_arg_pid][AC_ATTR_NAME]
			ptrace_OCA_dict[OCA_PTRACE_SLAVE_TYPE]  = self.ACS[OCA_arg_pid][AC_TYPE]
			ptrace_OCA_dict[OCA_ARG_REQUEST]        = request

		ptrace_OCA_dict[OCA_ARG_ADDR] = addr
		ptrace_OCA_dict[OCA_ARG_DATA] = arg_data
		ptrace_OCA_dict[OCA_ARG_RET] = ret
		self.send_OCA_evt(ptrace_OCA_dict, entity.get_log_time())

###############################################################################
# Exec Definitions
###############################################################################

	def __evt_exec(self, entity):

		data = entity.get_extra_data()
		OCA_pid = self.pid2OCA(entity.get_pid())
		
		if not self.ACS.has_key(OCA_pid):
			print "ERROR: OCA_pid %d called exec with no AC record" % OCA_pid
			raise AssertionError

		# If this is a traceme helper thread and it has been execed at
		# least once (i.e. it is running the bash shell and the shell is
		# calling exec again), change it's generation to 1 and start
		# logging OCA events.
		#
		if self.ACS[OCA_pid][AC_ATTR_GENERATION] == AC_INIT_BASH \
     		and self.ACS[OCA_pid][AC_ATTR_EXEC_NAME] != AC_DEFAULT_EXEC_NAME:
			self.ACS[OCA_pid][AC_ATTR_GENERATION] = 1
		
		self.ACS[OCA_pid][AC_ATTR_EXEC_NAME] = data

		exec_name = data.split("./")
		#print exec_name[0]
		#print "Exec : ", data.split("./")
		#self.unwantedExten.append(exec_name)
		
		exec_OCA_dict = {}
		exec_OCA_dict[OCA_TYPE]          = OCA_EXEC
		exec_OCA_dict[OCA_ARG_PID]       = OCA_pid
		exec_OCA_dict[OCA_ARG_AC_ID]     = OCA_pid
		exec_OCA_dict[OCA_ARG_EXEC_NAME] = data
		exec_OCA_dict[OCA_ARG_AC_NAME]   = self.ACS[OCA_pid][AC_ATTR_NAME]
		exec_OCA_dict[OCA_ARG_GEN]       = self.ACS[OCA_pid][AC_ATTR_GENERATION]
		self.send_OCA_evt(exec_OCA_dict, entity.get_log_time())

		if self.print_level >= MAX_PRINT_LEVEL:
			print >> self.outfile, "EXEC: OCA_pid %d execed --> %s" % (OCA_pid, data)
			self.print_ACS()
			self.print_PCS()

###############################################################################
# Socket Definitions
###############################################################################

	def __evt_socket(self, entity):
			
		data    = entity.get_extra_data()	
		OCA_pid = self.pid2OCA(entity.get_pid())	
		PC_id   = (data["sys_id"], data["inode_id"])
		fd      = data["fd"]
		mode    = data["mode"]
		
		self.sk_end += 1
		name = OCA_SK_END_BASE % self.sk_end

		# create_PC_record initializes sockets with the correct
		# initial attribute values
		#
		self.create_PC_record(PC_SK_ENDPOINT, PC_id, name)

		assert self.ACS.has_key(OCA_pid)
		AC_ref = {}
		AC_ref[AC_REF_ID]     = (self.ACS[OCA_pid][AC_ATTR_FILE_GID], fd)
		AC_ref[AC_REF_MODE]   = fileMode2String(mode)
		AC_ref[AC_REF_READ]   = 0
		AC_ref[AC_REF_WROTE]  = 0

		self.ACS[OCA_pid][AC_ATTR_FDS][fd] = self.PCS[PC_id]
		self.PCS[PC_id][PC_ATTR_OPEN_REFS].append(AC_ref)
		
		OCA_dict = {}
		OCA_dict[OCA_TYPE]        = OCA_SOCKET_CREATE
		OCA_dict[OCA_ARG_PID]     = OCA_pid
		OCA_dict[OCA_ARG_AC_ID]   = OCA_pid
		OCA_dict[OCA_ARG_FD]      = fd
		OCA_dict[OCA_ARG_PC_ID]   = self.PCS[PC_id][PC_ATTR_PC_ID]
		OCA_dict[OCA_ARG_PC_NAME] = self.PCS[PC_id][PC_ATTR_NAME]
		self.send_OCA_evt(OCA_dict, entity.get_log_time())

	def __evt_bind(self, entity):
		
		data = entity.get_extra_data()
		pid  = entity.get_pid()

		OCA_pid  = self.pid2OCA(pid)
		PC_id    = (data["sys_id"], data["inode_id"])
		fd       = data["fd"]
		ret      = data["ret"]
		family   = data["family"]
	#	print "sport : ", data['sport']
	#	print "dport : ", data['dport']

		if family == AF_UNIX:
			bound_id = (data["known_sys_id"], data["known_inode"])
		elif family == AF_INET:
			bound_id = (data["sport"])
		else:
			# Do not process unimplemented socket families
			return
	
		if not self.PCS.has_key(PC_id):
			print "Attempted to bind on unknown PC: (%s, %d)" \
				% (PC_id[0], PC_id[1])
			raise AssertionError
		
		if ret != 0:
			print "WARNING: %s failed to bind %s" \
				% (self.ACS[OCA_pid][AC_ATTR_NAME], self.PCS[PC_id][PC_ATTR_NAME])
			return
		
		self.PCS[PC_id][PC_SKAT_BOUND_ID] = bound_id
		self.PCS[PC_id][PC_SKAT_STATE]    = SK_BOUND

		OCA_dict = {}
		OCA_dict[OCA_TYPE]         = OCA_SOCKET_BIND
		OCA_dict[OCA_ARG_PID]      = OCA_pid
		OCA_dict[OCA_ARG_AC_ID]    = OCA_pid
		OCA_dict[OCA_ARG_FD]       = fd
		OCA_dict[OCA_ARG_PC_ID]    = self.PCS[PC_id][PC_ATTR_PC_ID]
		OCA_dict[OCA_ARG_PC_NAME]  = self.PCS[PC_id][PC_ATTR_NAME]
		OCA_dict[OCA_ARG_BOUND_ID] = self.PCS[PC_id][PC_SKAT_BOUND_ID]
		self.send_OCA_evt(OCA_dict, entity.get_log_time())

	def __evt_conn_begin(self, entity):
		"""
		The active filter uses this event to store information about which 
		processes should be added to the group. Local sockets queue up requests
		with this event.
		"""
		data      = entity.get_extra_data()
		OCA_pid   = self.pid2OCA(entity.get_pid())
		PC_id     = (data["sys_id"], data["inode_id"])
		listen_id = (data["known_sys_id"], data["known_inode"])
		family    = data["family"]

		# Used to track and identify unique local socket connections
		#
		if family == AF_UNIX:
			if self.listening_queues.has_key(listen_id):
				self.listening_queues[listen_id].append(PC_id)
			else:
				self.listening_queues[listen_id] = []
				self.listening_queues[listen_id].append(PC_id)
		
			if not self.PCS.has_key(PC_id):
				# Go ahead and create the PC record for
				# the discovered socket endpoint. This will
				# initially not have any AC references
				#
				self.sk_end += 1
				name = OCA_SK_END_BASE % self.sk_end
				self.create_PC_record(PC_SK_ENDPOINT, PC_id, name)

			#
			# In situations where the computation we are tracking
			# connects to a server, we would like to differentiate
			# between processes that were added to the group because
			# they are actually a part of the computation and 
			# processes that were added because they connected to a
			# common server.
			#
			# In this situation, we can make this distinction when
			# a client is added to our group by means of a socket
			# connection. Only processes that are in our group by
			# some other means are actually part of the computation
			#
			# NOTE: This distinction is not useful when you are
			# tracing the computation of a server process, and
			# especially not when the computation you wish to analyze
			# acts as both a client and a server.
			#
			if not self.ACS.has_key(OCA_pid):
				self.unrelated_conns.append(entity.get_pid())

      			if entity.get_pid() in self.unrelated_conns:
				OCA_dict = {}
				OCA_dict[OCA_TYPE] = OCA_UNRELATED_CLIENT_CONN
				OCA_dict[OCA_ARG_PC_ID] = PC_id
				self.send_OCA_evt(OCA_dict, entity.get_log_time())

	def __evt_sock_send(self, entity):

		data = entity.get_extra_data()
		pid  = entity.get_pid()

		#print "Socket send PID ", pid
		OCA_pid = self.pid2OCA(pid)
		PC_id   = (data["sys_id"], data["inode_id"])
		#print "socket send dport : ", data['dport']
		#print "socket send sport : ", data['sport']
		
		if data['dport'] == self.nfsPort:
			print "Got A NFS socket message send event. Ignoring it."
			return
		if not self.ACS.has_key(OCA_pid):
			print "ERROR: Got read event from unknown OCA_pid: %d" % OCA_pid
			raise AssertionError

		if PC_id[0] == DSCVR_NULL_SYSID:
			print "WARNING: Got send event for Null file. OCA_pid: %d" %OCA_pid
			return

		if not self.PCS.has_key(PC_id):
			if self.ACS[OCA_pid][AC_ATTR_RELATION] == AC_FAMILIAL_TASK:
				print "Error: Familial AC %d socket send on PC we did not " \
						"know about. PC_id: (%s, %d)" % (OCA_pid, PC_id[0], PC_id[1])
				raise AssertionError
			else:
				print "Nonfamilial AC %d socket send to unknown PC. " \
					"PC_id: (%s, %d)" % (OCA_pid, PC_id[0], PC_id[1])

	def __evt_sock_recv(self, entity):
		
		data = entity.get_extra_data()
		pid  = entity.get_pid()

		OCA_pid = self.pid2OCA(pid)
		PC_id   = (data["sys_id"], data["inode_id"])
		#print "socket recv dport : ", data['dport']
		#print "socket recv sport : ", data['sport']
		
		if data['dport'] == self.nfsPort:
			print "Got A NFS socket message recv event. Ignoring it."
			return
		if not self.ACS.has_key(OCA_pid):
			print "ERROR: Got recv event from unknown OCA_pid: %d" % OCA_pid
			raise AssertionError
		
		if PC_id[0] == DSCVR_NULL_SYSID:
			print "WARNING: Got recv event for Null file. OCA_pid: %d" %OCA_pid
			return

		if not self.PCS.has_key(PC_id):
			if self.ACS[OCA_pid][AC_ATTR_RELATION] == AC_FAMILIAL_TASK:
				print "Error: Familial AC %d socket recv on PC we did not " \
						"know about. PC_id: (%s, %d)" % (OCA_pid, PC_id[0], PC_id[1])
				raise AssertionError
			else:
				print "Nonfamilial AC %d socket recv on unknown PC. " \
					"PC_id: (%s, %d)" % (OCA_pid, PC_id[0], PC_id[1])

	def __evt_send_to(self, entity):
		
		data = entity.get_extra_data()
		pid  = entity.get_pid()

		OCA_pid = self.pid2OCA(pid)
		PC_id   = (data["sys_id"], data["inode_id"])
		fd      = data["fd"]
		mode    = data["mode"]
		ret     = data["ret"]
			
		OCA_dict                = {}	
		OCA_dict[OCA_TYPE]      = OCA_SOCKET_SEND_TO
		OCA_dict[OCA_ARG_PID]   = OCA_pid
		OCA_dict[OCA_ARG_AC_ID] = OCA_pid
		OCA_dict[OCA_ARG_PC_ID] = PC_id
		OCA_dict[OCA_ARG_FD]    = fd
		OCA_dict[OCA_ARG_SIZE]  = ret

		self.__update_AC_ref_write(OCA_pid, fd, PC_id, ret)		
		self.send_OCA_evt(OCA_dict, entity.get_log_time())

	def __evt_recv_from(self, entity):
		
		data = entity.get_extra_data()
		pid  = entity.get_pid()

		OCA_pid = self.pid2OCA(pid)
		PC_id   = (data["sys_id"], data["inode_id"])
		fd      = data["fd"]
		mode    = data["mode"]
		ret     = data["ret"]
		
		if PC_id[0] == DSCVR_NULL_SYSID:
			print "WARNING: Got send event for Null file. OCA_pid: %d" %OCA_pid
			return
		
		OCA_dict                = {}	
		OCA_dict[OCA_TYPE]      = OCA_SOCKET_RECV_FROM
		OCA_dict[OCA_ARG_PID]   = OCA_pid
		OCA_dict[OCA_ARG_AC_ID] = OCA_pid
		OCA_dict[OCA_ARG_PC_ID] = PC_id
		OCA_dict[OCA_ARG_FD]    = fd
		OCA_dict[OCA_ARG_SIZE]  = ret

		self.__update_AC_ref_read(OCA_pid, fd, PC_id, ret)		
		self.send_OCA_evt(OCA_dict, entity.get_log_time())

	def __evt_send_msg(self, entity):
	
		data = entity.get_extra_data()
		pid  = entity.get_pid()

		OCA_pid = self.pid2OCA(pid)
		PC_id   = (data["sys_id"], data["inode_id"])
		fd      = data["fd"]
		mode    = data["mode"]
		ret     = data["ret"]
		
		OCA_dict                = {}	
		OCA_dict[OCA_TYPE]      = OCA_SOCKET_SEND_MSG
		OCA_dict[OCA_ARG_PID]   = OCA_pid
		OCA_dict[OCA_ARG_AC_ID] = OCA_pid
		OCA_dict[OCA_ARG_PC_ID] = PC_id
		OCA_dict[OCA_ARG_FD]    = fd
		OCA_dict[OCA_ARG_SIZE]  = ret

		self.__update_AC_ref_write(OCA_pid, fd, PC_id, ret)
		self.send_OCA_evt(OCA_dict, entity.get_log_time())
		
	def __evt_recv_msg(self, entity):
		
		data = entity.get_extra_data()
		pid  = entity.get_pid()

		OCA_pid = self.pid2OCA(pid)
		PC_id   = (data["sys_id"], data["inode_id"])
		fd      = data["fd"]
		mode    = data["mode"]
		ret     = data["ret"]
		
		OCA_dict                = {}	
		OCA_dict[OCA_TYPE]      = OCA_SOCKET_RECV_MSG
		OCA_dict[OCA_ARG_PID]   = OCA_pid
		OCA_dict[OCA_ARG_AC_ID] = OCA_pid
		OCA_dict[OCA_ARG_PC_ID] = PC_id
		OCA_dict[OCA_ARG_FD]    = fd
		OCA_dict[OCA_ARG_SIZE]  = ret

		self.__update_AC_ref_read(OCA_pid, fd, PC_id, ret)
		self.send_OCA_evt(OCA_dict, entity.get_log_time())
	
	def __evt_listen(self, entity):

		data = entity.get_extra_data()
		pid  = entity.get_pid()

		OCA_pid = self.pid2OCA(pid)
		PC_id   = (data["sys_id"], data["inode_id"])
		fd      = data["fd"]
		backlog = entity.get_tag()
		family  = data["family"]

		# Backlog is the number of requests this passive socket will hold
		# in its pending queue
		#
		self.PCS[PC_id][PC_SKAT_BACKLOG]  = backlog
		self.PCS[PC_id][PC_SKAT_STATE]    = SK_LISTENING

		OCA_dict = {}
		OCA_dict[OCA_TYPE]         = OCA_SOCKET_LISTEN
		OCA_dict[OCA_ARG_PID]      = OCA_pid
		OCA_dict[OCA_ARG_AC_ID]    = OCA_pid
		OCA_dict[OCA_ARG_FD]       = fd
		OCA_dict[OCA_ARG_FAMILY]   = family
		OCA_dict[OCA_ARG_PC_ID]    = self.PCS[PC_id][PC_ATTR_PC_ID]
		OCA_dict[OCA_ARG_PC_NAME]  = self.PCS[PC_id][PC_ATTR_NAME]
		OCA_dict[OCA_ARG_BACKLOG]  = self.PCS[PC_id][PC_SKAT_BACKLOG]
		self.send_OCA_evt(OCA_dict, entity.get_log_time())

	def __evt_socket_add(self, entity):
		"""
		An event announcing that our active filter has added a member to the
		group we are tracing because of a socket connection.
		"""
		OCA_pid = self.pid2OCA(entity.get_pid(), OCA_PID_CREATE)
		self.create_AC_record(None, OCA_pid, AC_SOCKET_REL)

		self.ACS[OCA_pid][AC_ATTR_EXEC_NAME] = entity.get_extra_data()
		
		#print >> self.outfile, "SOCKET_ADD"
		#self.print_ACS()
		#self.print_PCS()

		OCA_dict = {}
		OCA_dict[OCA_TYPE]          = OCA_SOCKET_ADD
		OCA_dict[OCA_ARG_PID]       = OCA_pid
		OCA_dict[OCA_ARG_AC_ID]     = OCA_pid
		OCA_dict[OCA_ARG_EXEC_NAME] = self.ACS[OCA_pid][AC_ATTR_EXEC_NAME]
		OCA_dict[OCA_ARG_GEN]       = AC_NONFAMILIAL_TASK
		OCA_dict[OCA_ARG_REL]       = AC_SOCKET_REL

		self.send_OCA_evt(OCA_dict, entity.get_log_time())
		
	def __evt_accept(self, entity):
		"""
		A server socket is accepting a connection. This call creates a new
		socket end point for the server to use as its end of the connection.
		"""

		data = entity.get_extra_data()
		pid  = entity.get_pid()

		OCA_pid       = self.pid2OCA(pid)
		PC_id         = (data["sys_id"], data["inode_id"])
		fd            = data["fd"]
		mode          = data["mode"]
		listen_inode  = data["known_inode"]
		listen_sys_id = data["known_sys_id"]
		server_id     = (data["saddr"], data["sport"])
		client_id     = (data["daddr"], data["dport"])
		ret           = data["ret"]
		family        = data["family"]

		if family == AF_UNIX:
			listen_id = (listen_sys_id, listen_inode)
		elif family == AF_INET:
			sock_id = (server_id, client_id)
		else:
			# Do not process unimplemented socket families
			return
		
		if self.PCS.has_key(PC_id):
			print "ERROR: Calling socket_accept on socket already in the " \
				"PCS. PC_id: (%s,%d)" % (PC_id[0], PC_id[1])
			raise AssertionError
		
		# We assume the accept failure occurs after a reference to the 
		# SK_ENDPOINT is created
		#
		if ret < 0:
			print "WARNING: %s failed to accept %s on socket with ID " % \
				(self.ACS[OCA_pid][AC_ATTR_NAME], self.PCS[PC_id][PC_ATTR_NAME]),
			if family == AF_UNIX:
				print "listen_id: %d" % listen_id,
			elif family == AF_INET:
				print "server: (%s, %d), client (%s, %d)" % \
     				(server_id[0], server_id[1], client_id[0], client_id[1]),

			print ", returned %d" % ret
			return
	
		# Create the PC record for this end of the socket and an AC reference
		# to it
		#	
		self.sk_end += 1
		name = OCA_SK_END_BASE % self.sk_end
		self.create_PC_record(PC_SK_ENDPOINT, PC_id, name)

		assert self.ACS.has_key(OCA_pid)
		AC_ref_id = (self.ACS[OCA_pid][AC_ATTR_FILE_GID], fd)
		AC_ref = {}
		AC_ref[AC_REF_ID]      = AC_ref_id
		AC_ref[AC_REF_MODE]    = fileMode2String(mode)
		AC_ref[AC_REF_READ]    = 0
		AC_ref[AC_REF_WROTE]   = 0

		self.ACS[OCA_pid][AC_ATTR_FDS][fd] = self.PCS[PC_id]
		self.PCS[PC_id][PC_ATTR_OPEN_REFS].append(AC_ref)		
	
		#
		# Local sockets are identified when a local connect event (in the unix
		# protocol code) is registered on the system as part of the computation.
		# The next accept on the listening id the local connect is trying to
		# connect to dequeues that listening id's queue. Local connects are registered
		# even when the client is not part of the computation by logic in the
		# active filter.
		#
		if family == AF_UNIX:
			if not self.listening_queues.has_key(listen_id):
				print "ERROR: Got accept on unknown listening socket \
						Listen ID: [(%s, %d). Accept ID: (%s, %d)" % \
						(listen_id[0], listen_id[1], PC_id[0], PC_id[1])
				return
			
			if not self.listening_queues[listen_id]:
				print "ERROR: Got accept on listening socket before",
				print "receiving connect begin. Listen ID:",
				print "[(%s, %d). Accept ID: (%s, %d)]" % \
					(listen_id[0], listen_id[1], PC_id[0], PC_id[1])
				return

			self.sock_num += 1
			sock_id = (PC_id, self.listening_queues[listen_id][0])
			del self.listening_queues[listen_id][0]
			self.local_socks[sock_id] = OCA_SKNAME_BASE % self.sock_num
			self.PCS[PC_id][PC_SKAT_NAME] = self.local_socks[sock_id]	
			self.PCS[sock_id[1]][PC_SKAT_NAME] = self.local_socks[sock_id] 
			self.PCS[PC_id][PC_SKAT_OTHER_END] = sock_id[1]
			self.PCS[sock_id[1]][PC_SKAT_OTHER_END] = PC_id

		# We can receive connect_end and accept calls in any order
		# We need to record the (sys_id, inode_id) of the one we receive
		# first so as to match these up when we create a full PC record.
		#	
		if family == AF_INET:
			if not self.remote_socks.has_key(sock_id):						
				self.sock_num += 1
				self.remote_socks[sock_id] = OCA_SKNAME_BASE % self.sock_num
				self.PCS[PC_id][PC_SKAT_NAME] = self.remote_socks[sock_id]
		
		self.PCS[PC_id][PC_SKAT_BOUND_ID] = server_id
		self.PCS[PC_id][PC_SKAT_STATE]    = SK_CONNECTED_SERVER
		
		#print >> self.outfile, "ACCEPT"
		#self.print_ACS()
		#self.print_PCS()
				
		OCA_dict = {}
		OCA_dict[OCA_TYPE]          = OCA_SOCKET_ACCEPT
		OCA_dict[OCA_ARG_PID]       = OCA_pid 
		OCA_dict[OCA_ARG_FD]        = fd
		OCA_dict[OCA_ARG_AC_ID]     = self.ACS[OCA_pid][AC_ATTR_AC_ID]
		OCA_dict[OCA_ARG_GEN] 	    = self.ACS[OCA_pid][AC_ATTR_GENERATION]
		OCA_dict[OCA_ARG_PC_ID]     = self.PCS[PC_id][PC_ATTR_PC_ID]
		OCA_dict[OCA_ARG_PC_NAME]   = self.PCS[PC_id][PC_ATTR_NAME]
		OCA_dict[OCA_ARG_SOCK_NAME] = self.PCS[PC_id][PC_SKAT_NAME]
		OCA_dict[OCA_ARG_EXEC_NAME] = self.ACS[OCA_pid][AC_ATTR_EXEC_NAME]	
		OCA_dict[OCA_ARG_AC_NAME]   = self.ACS[OCA_pid][AC_ATTR_NAME]	
		OCA_dict[OCA_ARG_SOCK_ID]   = sock_id
		OCA_dict[OCA_ARG_FAMILY]    = family
		self.send_OCA_evt(OCA_dict, entity.get_log_time())
	
	def __evt_conn_end(self, entity):
		"""
		A client socket is completing its end of the connection. 
		"""	
		data = entity.get_extra_data()
		pid  = entity.get_pid()

		OCA_pid      = self.pid2OCA(pid)
		PC_id        = (data["sys_id"], data["inode_id"])
		fd           = data["fd"]
		known_inode  = data["known_inode"]
		known_sys_id = data["known_sys_id"]
		server_id    = (data["daddr"], data["dport"])
		client_id    = (data["saddr"], data["sport"])
		mode         = data["mode"]
		ret          = data["ret"]
		family       = data["family"]
		
		if family == AF_UNIX:
			sock_id = (known_inode, known_sys_id)
		elif family == AF_INET:
			sock_id = (server_id, client_id)
		else:
			# Do not process unimplemented socket families
			return
		
		if not self.ACS.has_key(OCA_pid):
			print "ERROR: Unknown AC record calling connect. OCA_pid %d" % OCA_pid
			raise AssertionError
		
		# We assume the connect failure occurs after a reference to the 
		# SK_ENDPOINT is created
		#
		if ret != 0:
			print "WARNING: %s failed to connect on socket with ID: " % \
				(self.ACS[OCA_pid][AC_ATTR_NAME]),
			if family == AF_UNIX:
				print "(%s, %d)" % (known_sys_id, known_inode),
			elif family == AF_INET:
				print "server: (%s, %d), client (%s, %d)" % \
     				(server_id[0], server_id[1], client_id[0], client_id[1]),

			print ", returned %d" % ret
			return

		if not self.PCS.has_key(PC_id):
			# This must be a nonfamilial AC we are connecting to
			#
			if self.ACS[OCA_pid][AC_ATTR_RELATION] == AC_FAMILIAL_TASK:
				print "ERROR: Familial AC calling connect end on " \
					"unknown socket. PC_id: (%s,%d)" % (PC_id[0], PC_id[1])
				raise AssertionError
			
			# Go ahead and create the PC record for
			# the discovered socket endpoint
			#
			self.sk_end += 1
			name = OCA_SK_END_BASE % self.sk_end
			self.create_PC_record(PC_SK_ENDPOINT, PC_id, name)
	
		# Create an AC reference and hook up the ACS to the PCS
		#
		AC_ref_id = (self.ACS[OCA_pid][AC_ATTR_FILE_GID], fd)
		AC_ref = {}
		AC_ref[AC_REF_ID]    = AC_ref_id
		AC_ref[AC_REF_MODE]  = fileMode2String(mode)
		AC_ref[AC_REF_READ]  = 0
		AC_ref[AC_REF_WROTE] = 0

		self.ACS[OCA_pid][AC_ATTR_FDS][fd] = self.PCS[PC_id]
		self.PCS[PC_id][PC_ATTR_OPEN_REFS].append(AC_ref)		

		# We can receive connect_end and accept calls in any order
		# We need to record the (sys_id, inode_id) of the one we receive
		# first so as to match these up when we create a full PC record.
		#	
		if family == AF_INET:
			if not self.remote_socks.has_key(sock_id):						
				self.sock_num += 1
				self.remote_socks[sock_id] = OCA_SKNAME_BASE % self.sock_num

			self.PCS[PC_id][PC_SKAT_NAME] = self.remote_socks[sock_id]
		
		self.PCS[PC_id][PC_SKAT_BOUND_ID] = client_id
		self.PCS[PC_id][PC_SKAT_STATE]    = SK_CONNECTED_CLIENT

		#print >> self.outfile, "CONNECT_END"
		#self.print_ACS()
		#self.print_PCS()
				
		OCA_dict = {}
		OCA_dict[OCA_TYPE]          = OCA_SOCKET_CONNECT
		OCA_dict[OCA_ARG_PID]       = OCA_pid 
		OCA_dict[OCA_ARG_FD]        = fd
		OCA_dict[OCA_ARG_AC_ID]     = self.ACS[OCA_pid][AC_ATTR_AC_ID]
		OCA_dict[OCA_ARG_GEN] 	    = self.ACS[OCA_pid][AC_ATTR_GENERATION]
		OCA_dict[OCA_ARG_PC_ID]     = self.PCS[PC_id][PC_ATTR_PC_ID]
		OCA_dict[OCA_ARG_PC_NAME]   = self.PCS[PC_id][PC_ATTR_NAME]
		OCA_dict[OCA_ARG_SOCK_NAME] = self.PCS[PC_id][PC_SKAT_NAME]
		OCA_dict[OCA_ARG_EXEC_NAME] = self.ACS[OCA_pid][AC_ATTR_EXEC_NAME]	
		OCA_dict[OCA_ARG_AC_NAME]   = self.ACS[OCA_pid][AC_ATTR_NAME]	
		OCA_dict[OCA_ARG_FAMILY]    = family
		OCA_dict[OCA_ARG_SOCK_ID]   = sock_id
		self.send_OCA_evt(OCA_dict, entity.get_log_time())

###############################################################################
# Context Switch Definitions
###############################################################################

	def __evt_switch_from(self, entity):
		"""
		Event registered when processes are switched from
		The tag on this event represents whether or not this process
		is on the run queue when it is switched from.
		"""
		OCA_pid = self.pid2OCA(entity.get_pid())

		if entity.get_tag() == 1:
			was_preempted = True
		else: 
			was_preempted = False
	
		if not self.ACS.has_key(OCA_pid):
			# Throw away switch from events for processes that have
			# not been given an OCA pid yet
			#
			#print "WARNING: switch from from unknown PID: %d" % entity.get_pid()
			return
			
		OCA_dict = {}
		OCA_dict[OCA_TYPE] = OCA_SWITCH_FROM
		OCA_dict[OCA_ARG_PID] = OCA_pid
		OCA_dict[OCA_ARG_EXEC_NAME] = self.ACS[OCA_pid][AC_ATTR_EXEC_NAME]
		OCA_dict[OCA_ARG_PREEMPTED] = was_preempted 
		self.send_OCA_evt(OCA_dict, entity.get_log_time())

	def __evt_switch_to(self, entity):
		"""
		Event registered when processes are switched to
		"""
		OCA_pid = self.pid2OCA(entity.get_pid())
		
		if not self.ACS.has_key(OCA_pid):
			# Throw away switch to events for processes that have
			# not been given an OCA pid yet
			#
			#print "WARNING: switch to from unknown PID: %d" % entity.get_pid()
			return
	
		OCA_dict = {}
		OCA_dict[OCA_TYPE] = OCA_SWITCH_TO
		OCA_dict[OCA_ARG_PID] = OCA_pid
		OCA_dict[OCA_ARG_EXEC_NAME] = self.ACS[OCA_pid][AC_ATTR_EXEC_NAME]
		self.send_OCA_evt(OCA_dict, entity.get_log_time())
	
###############################################################################
# Helper Definitions
###############################################################################
	
	def __update_AC_ref_read(self, OCA_pid, fd, PC_id, size):

		# Do we have a reference to this active component?
		#
		if not self.ACS.has_key(OCA_pid):
			print "ERROR: Got read event from unknown OCA_pid: %d" % OCA_pid
			raise AssertionError

		AC_ref = (self.ACS[OCA_pid][AC_ATTR_FILE_GID], fd)
		# Do we have a reference to this passive component?
		#
		if PC_id[0] == DSCVR_NULL_SYSID:
			print "WARNING: Got read event for Null file. OCA_pid: %d" % OCA_pid
			return

		if not self.PCS.has_key(PC_id):
			if self.ACS[OCA_pid][AC_ATTR_RELATION] == AC_FAMILIAL_TASK:
				print "Error: Familial AC %d read on fd %d." % \
						(OCA_pid, fd),
				print "Unknown PC. (%s, %d)" % (PC_id[0], PC_id[1])
				return
			else:
				print "Nonfamilial AC read fd to unknown PC. AC_ref: " \
					"(%d, %d). PC_id: (%s, %d)" % (AC_ref[0], AC_ref[1], \
				    	PC_id[0], PC_id[1])
				return
		
		# Do we have a reference to this file descriptor?
		#
		if not self.ACS[OCA_pid][AC_ATTR_FDS].has_key(fd):
			if self.ACS[OCA_pid][AC_ATTR_RELATION] == AC_FAMILIAL_TASK:
				print "Error: Familial AC read to unknown fd. AC_ref: " \
					"(%d, %d)" % AC_ref
				return
				#raise AssertionError
			else:
				print "Nonfamilial AC read to unknown fd. AC_ref: " \
					"(%d, %d). PC_id: (%s, %d)" % (AC_ref[0], AC_ref[1], \
				    	PC_id[0], PC_id[1])
				return
		
		# Does our AC have an open reference to this PC?
		#
		if not self.ACS[OCA_pid][AC_ATTR_FDS][fd][PC_ATTR_PC_ID] == PC_id:
			print "ERROR: AC_ref (%d, %d) wrote to unknown PC (%s, %d)" \
				% (AC_ref[0], AC_ref[1], PC_id[0], PC_id[1])
			#raise AssertionError
			return
		
		if size < 0:
			#print "WARNING: AC_ref (%d, %d) write to PC (%s, %d) returned " \
			#	"an error." % (AC_ref[0], AC_ref[1], PC_id[0], PC_id[1])
			return
		
		for item in self.PCS[PC_id][PC_ATTR_OPEN_REFS]:
			if item[AC_REF_ID] == AC_ref:
				item[AC_REF_READ] += size 

	def __update_AC_ref_write(self, OCA_pid, fd, PC_id, size):

		# Do we have a reference to this active component?
		#
		if not self.ACS.has_key(OCA_pid):
			print "ERROR: Got write event from unknown OCA_pid: %d" % OCA_pid
			raise AssertionError

		AC_ref = (self.ACS[OCA_pid][AC_ATTR_FILE_GID], fd)
		# Do we have a reference to this passive component?
		#
		if PC_id[0] == DSCVR_NULL_SYSID:
			print "WARNING: Got write event for Null file. OCA_pid: %d" % OCA_pid
			return

		if not self.PCS.has_key(PC_id):
			if self.ACS[OCA_pid][AC_ATTR_RELATION] == AC_FAMILIAL_TASK:
				print "Error: Familial AC %d write on fd %d." % \
						(OCA_pid, fd),
				print "Unknown PC. (%s, %d)" % (PC_id[0], PC_id[1])
				return
			else:
				print "Nonfamilial AC write fd to unknown PC. AC_ref: " \
					"(%d, %d). PC_id: (%s, %d)" % (AC_ref[0], AC_ref[1], \
				    	PC_id[0], PC_id[1])
				return
		
		# Do we have a reference to this file descriptor?
		#
		if not self.ACS[OCA_pid][AC_ATTR_FDS].has_key(fd):
			if self.ACS[OCA_pid][AC_ATTR_RELATION] == AC_FAMILIAL_TASK:
				print "Error: Familial AC write to unknown fd. AC_ref: " \
					"(%d, %d)" % AC_ref
				#raise AssertionError
				return
			else:
				print "Nonfamilial AC write to unknown fd. AC_ref: " \
					"(%d, %d). PC_id: (%s, %d)" % (AC_ref[0], AC_ref[1], \
				    	PC_id[0], PC_id[1])
				return
		
		# Does our AC have an open reference to this PC?
		#
		if not self.ACS[OCA_pid][AC_ATTR_FDS][fd][PC_ATTR_PC_ID] == PC_id:
			print "ERROR: AC_ref (%d, %d) wrote to unknown PC (%s, %d)" \
				% (AC_ref[0], AC_ref[1], PC_id[0], PC_id[1])
			#raise AssertionError
			return

		if size < 0:
			#print "WARNING: AC_ref (%d, %d) write to PC (%s, %d) returned " \
			#	"an error." % (AC_ref[0], AC_ref[1], PC_id[0], PC_id[1])
			return
		
		for item in self.PCS[PC_id][PC_ATTR_OPEN_REFS]:
			if item[AC_REF_ID] == AC_ref:
				item[AC_REF_WROTE] += size 
			
	def send_OCA_evt(self, OCA_dict, log_time):
		"""
		Use this wrapper to send OCA events.
		"""

		OCA_evt = entities.Event(self.OCA_actions_ptr.get_cid(), log_time, 0, OCA_dict, 0)
		self.send_output("default", OCA_evt)

	def print_ACS(self):
			
		print >> self.outfile, "Current ACS:"
		for OCA_pid in self.ACS.iterkeys():
			print >> self.outfile, "OCA_pid:", self.ACS[OCA_pid][AC_ATTR_OCA_PID]
			if self.print_level >= RAW_INFO_PRINT:
				print >> self.outfile, "\tOrig_pid:\t", self.ACS[OCA_pid][AC_ATTR_ORIG_PID]
			print >> self.outfile, "\tName:\t\t", self.ACS[OCA_pid][AC_ATTR_NAME]
			print >> self.outfile, "\tExec:\t\t", self.ACS[OCA_pid][AC_ATTR_EXEC_NAME]
			print >> self.outfile, "\tRelation:\t", self.ACS[OCA_pid][AC_ATTR_RELATION]
			print >> self.outfile, "\tGeneration:\t", self.ACS[OCA_pid][AC_ATTR_GENERATION]
			print >> self.outfile, "\tFile Group:\t",
			self.print_file_group(self.ACS[OCA_pid][AC_ATTR_FILE_GID])
			print >> self.outfile, "\n\tSHM Group:\t",
			self.print_shm_group(self.ACS[OCA_pid][AC_ATTR_SHM_GID])
			print >> self.outfile, "\n",
			if self.ACS[OCA_pid][AC_ATTR_FDS]:
				print >> self.outfile, "\tOpen File Descriptors"
				for fd in self.ACS[OCA_pid][AC_ATTR_FDS].iterkeys():
					#
					# Don't print regular files for lower print levels
					#
					if self.print_level < REG_FILE_PRINT:
						if self.ACS[OCA_pid][AC_ATTR_FDS][fd][PC_TYPE] == PC_FILE:
							continue

					if fd < 10:
						print >> self.outfile, "\t\t%d  ----> " % fd,
					else:
						print >> self.outfile, "\t\t%d ----> " % fd,

				
					if self.print_level >= REG_FILE_PRINT:
						print >> self.outfile, "(%s, %d)" % ( \
						 self.ACS[OCA_pid][AC_ATTR_FDS][fd][PC_ATTR_PC_ID][0], \
						 self.ACS[OCA_pid][AC_ATTR_FDS][fd][PC_ATTR_PC_ID][1] ),

					print >> self.outfile, `self.ACS[OCA_pid][AC_ATTR_FDS][fd][PC_ATTR_NAME]`,
					
					if self.ACS[OCA_pid][AC_ATTR_FDS][fd][PC_TYPE] == PC_SK_ENDPOINT:
						print >> self.outfile, "Connected on: %s" \
							% (self.ACS[OCA_pid][AC_ATTR_FDS][fd][PC_SKAT_NAME]),

					print >> self.outfile, ""

			if self.ACS[OCA_pid][AC_ATTR_SHMATS]:
				print >> self.outfile, "\tAttached shm segments"
				for shmaddr in self.ACS[OCA_pid][AC_ATTR_SHMATS].iterkeys():
					print >> self.outfile, "\t\t%s" % self.ACS[OCA_pid][AC_ATTR_SHMATS][shmaddr][PC_ATTR_NAME],
					if self.print_level >= RAW_INFO_PRINT:
						print >> self.outfile, "\t (Addr: %d points to (%s, %d))" % (shmaddr, \
							self.ACS[OCA_pid][AC_ATTR_SHMATS][shmaddr][PC_ATTR_PC_ID][0], \
							self.ACS[OCA_pid][AC_ATTR_SHMATS][shmaddr][PC_ATTR_PC_ID][1]),
						print >> self.outfile, ""

			if self.ACS[OCA_pid][AC_ATTR_MASTERS]:
				print >> self.outfile, "\tPtrace Masters: ",
				for pid in self.ACS[OCA_pid][AC_ATTR_MASTERS]:
					print >> self.outfile, "(  ", pid, ",  ",
				print >> self.outfile, ")"
			if self.ACS[OCA_pid][AC_ATTR_SLAVES]:
				print >> self.outfile, "\tPtrace Slaves: ",
				for pid in self.ACS[OCA_pid][AC_ATTR_SLAVES]:
					print >> self.outfile, "(  ", pid, ",  ",
				print >> self.outfile, ")"
			print >> self.outfile, ""
		print >> self.outfile, ""

	def print_PCS(self):
	
		print >> self.outfile, "Current PCS:"
		for PC_id in self.PCS.iterkeys():
			#
			# Don't print regular files on lower print levels
			#
			if self.print_level < REG_FILE_PRINT:
				if self.PCS[PC_id][PC_TYPE] == PC_FILE:
					continue
			
			if self.print_level >= RAW_INFO_PRINT:
				print >> self.outfile, "PC_ID:", self.PCS[PC_id][PC_ATTR_PC_ID]
			print >> self.outfile, "\tName:\t\t", self.PCS[PC_id][PC_ATTR_NAME]
			print >> self.outfile, "\tType:\t\t", self.PCS[PC_id][PC_TYPE]
			if self.PCS[PC_id][PC_TYPE] == PC_SK_ENDPOINT:
				print >> self.outfile, "\tState:\t\t", self.PCS[PC_id][PC_SKAT_STATE]
				print >> self.outfile, "\tBound to:\t", self.PCS[PC_id][PC_SKAT_BOUND_ID] 
				print >> self.outfile, "\tBacklog:\t", self.PCS[PC_id][PC_SKAT_BACKLOG] 
				print >> self.outfile, "\tSK Name:\t", self.PCS[PC_id][PC_SKAT_NAME] 
				if self.PCS[PC_id][PC_SKAT_OTHER_END]:
					print >> self.outfile, "\tOther End:\t", \
						self.PCS[PC_id][PC_SKAT_OTHER_END]
			if self.PCS[PC_id][PC_TYPE] == PC_FILE:
				print >> self.outfile, "\tLocked:\t", self.PCS[PC_id][PC_ATTR_LOCKED]
			if not self.PCS[PC_id][PC_ATTR_OPEN_REFS]:
				print >> self.outfile, "\tNo Open AC Refs"
			else:
				print >> self.outfile, "\tOpen AC_Refs: "
				for ac_ref in self.PCS[PC_id][PC_ATTR_OPEN_REFS]:
					self.print_AC_ref(ac_ref, self.PCS[PC_id][PC_TYPE])
			if not self.PCS[PC_id][PC_ATTR_CLOSED_REFS]:
				print >> self.outfile, "\tNo Closed AC Refs"
			else:
				print >> self.outfile, "\tClosed AC_Refs: "
				for ac_ref in self.PCS[PC_id][PC_ATTR_CLOSED_REFS]:
					self.print_AC_ref(ac_ref, self.PCS[PC_id][PC_TYPE])
			print >> self.outfile, ""
		print >> self.outfile, ""
	
	def print_AC_ref(self, AC_ref, PC_type):		
		if PC_type == PC_SHM:
			print >> self.outfile, "\t\t(",
			self.print_shm_group(AC_ref[AC_REF_ID][0])
			print >> self.outfile, ", %d)" % AC_ref[AC_REF_ID][1]
			print >> self.outfile, "\t\t\tAC Type: %s" %  \
					(self.ACS[AC_ref[AC_REF_ID][0]][AC_TYPE]) 
			print >> self.outfile, "\t\t\tMode: %s" %  \
					(AC_ref[AC_REF_MODE]) 
		else:
			#for id in self.file_groups.iterkeys():
				#	print >> self.outfile, "ID: %d\t" % id,
				#self.print_file_group(id)
				#print >> self.outfile, ""
			print >> self.outfile, "\t\t(",
			self.print_file_group(AC_ref[AC_REF_ID][0])
			print >> self.outfile, ", %d)" % AC_ref[AC_REF_ID][1]
			print >> self.outfile, "\t\t\tAC Type: %s" %  \
					(self.ACS[AC_ref[AC_REF_ID][0]][AC_TYPE]) 
			print >> self.outfile, "\t\t\tMode: %s" %  \
					(AC_ref[AC_REF_MODE]) 
			print >> self.outfile, "\t\t\tRead: %d\tWrote: %d" % \
					(AC_ref[AC_REF_READ], AC_ref[AC_REF_WROTE])	

	def print_file_group(self, FGID):
			
		alive_lst = self.file_groups[FGID][AC_TG_ALIVE]
		exited_lst = self.file_groups[FGID][AC_TG_EXITED]
		pid_lst = alive_lst + exited_lst
		self.outfile.write("[")
		for pid in pid_lst[:-1]:
			if pid in exited_lst:
				self.outfile.write("!")
			self.outfile.write("%d, " % pid)
		if pid_lst[-1] in exited_lst:
			self.outfile.write("!")
		self.outfile.write("%d]" % pid_lst[-1])

	def print_shm_group(self, SHM_GID):
			
		alive_lst = self.shm_groups[SHM_GID][AC_TG_ALIVE]
		exited_lst = self.shm_groups[SHM_GID][AC_TG_EXITED]
		pid_lst = alive_lst + exited_lst
		self.outfile.write("[")
		for pid in pid_lst[:-1]:
			if pid in exited_lst:
				self.outfile.write("!")
			self.outfile.write("%d, " % pid)
		if pid_lst[-1] in exited_lst:
			self.outfile.write("!")
		self.outfile.write("%d]" % pid_lst[-1])

	def print_file_report(self):

		files      = []
		so_files   = []
		conf_files = []
		misc_files = []

		for PC_id in self.PCS.iterkeys():
			if self.PCS[PC_id][PC_TYPE] == PC_FILE:
				files.append(self.PCS[PC_id])
				
				if self.PCS[PC_id][PC_ATTR_NAME].endswith(".so") \
				or not self.PCS[PC_id][PC_ATTR_NAME].find(".so.") < 0:
					so_files.append(self.PCS[PC_id])
				elif self.PCS[PC_id][PC_ATTR_NAME].endswith(".conf") \
				or not self.PCS[PC_id][PC_ATTR_NAME].find(".conf.") < 0:
					conf_files.append(self.PCS[PC_id])
				else:
					misc_files.append(self.PCS[PC_id])

		print >> self.outfile, "File Report\n"
		print >> self.outfile, "Total Files Opened:\t\t%d" % len(files)
		print >> self.outfile, "Total Shared Library Files:\t%d" % len(so_files)
		print >> self.outfile, "Total Config Files:\t\t%d" % len(conf_files)
		print >> self.outfile, "Total Miscellaneous Files:\t%d" % len(misc_files)

		print >> self.outfile, "Shared Library Files:"
		for file in so_files:
			self.print_file(file)

		print >> self.outfile, "\nConfig Files:"
		for file in conf_files:
			self.print_file(file)

		print >> self.outfile, "\nUnclassified Files:"
		for file in misc_files:
			self.print_file(file)

	def print_file(self, file):

		total_refs  = file[PC_ATTR_OPEN_REFS]
		total_refs.extend(file[PC_ATTR_CLOSED_REFS])
		total_read  = 0
		total_wrote = 0

		for ref in total_refs:
			total_read += ref[AC_REF_READ]
			total_read += ref[AC_REF_WROTE]

		print >> self.outfile, "\t%s(%d Total Refs, %d Closed Refs, %d Bytes Read, %d Bytes Written)" \
			% (file[PC_ATTR_NAME], len(total_refs), len(file[PC_ATTR_CLOSED_REFS]), \
       				total_read, total_wrote)


	def init_e2o_map(self):	
		"""
		None of the admininistrative events announcing the namespace cids
		have been processed yet in the initialize function. So we do this 
		here, on the first pass of a real entity process.
		FIXME: This is stupid. Figure out a better way to do this.
		"""
		self.event_to_OCA_action_map = {
			self.fork_ptr.get_cid()           : self.__evt_fork,
			self.exit_ptr.get_cid()           : self.__evt_exit,
			self.signal_send_ptr.get_cid()    : self.__evt_signal_send,
			self.shmget_ptr.get_cid()         : self.__evt_shmget,
			self.shmat_ptr.get_cid()          : self.__evt_shmat,
			self.shmdt_ptr.get_cid()          : self.__evt_shmdt,
			self.shmat_add_ptr.get_cid()      : self.__evt_shmat_add,
			self.fifo_open_ptr.get_cid()      : self.__evt_fifo_open,
			self.pipe_ptr.get_cid()           : self.__evt_do_pipe,
			self.fcntl_ptr.get_cid()          : self.__evt_fcntl,
			self.flock_ptr.get_cid()	  : self.__evt_fcntl,
			self.ptrace_ptr.get_cid()         : self.__evt_ptrace,
			self.exec_ptr.get_cid()           : self.__evt_exec,
			self.exec_misc_open_ptr.get_cid() : self.__evt_open,
			self.exec_som_open_ptr.get_cid()  : self.__evt_open,
			self.exec_elf_open_ptr.get_cid()  : self.__evt_open,
			self.close_ptr.get_cid()          : self.__evt_close,
			self.open_ptr.get_cid()           : self.__evt_open,
			self.dupx_ptr.get_cid()           : self.__evt_dup,
			self.dup2_ptr.get_cid()		  : self.__evt_dup,
			self.fd_install_ptr.get_cid()     : self.__evt_fd_install,
			self.read_info_ptr.get_cid()      : self.__evt_read_info,
			self.read_data_ptr.get_cid()      : self.__evt_read_data,
			self.write_info_ptr.get_cid()     : self.__evt_write_info,
			self.readv_ptr.get_cid()	  : self.__evt_readv,
			self.writev_ptr.get_cid()	  : self.__evt_writev,
			self.write_data_ptr.get_cid()     : self.__evt_write_data,
			self.dsui_signal_ptr.get_cid()    : self.__evt_dsui_signal,
			self.dsui_logger_ptr.get_cid()    : self.__evt_dsui_logger,
			self.dsui_buffer_ptr.get_cid()    : self.__evt_dsui_buffer,
			self.socket_ptr.get_cid()	  : self.__evt_socket,
			self.client_add_ptr.get_cid()	  : self.__evt_socket_add,
			self.server_add_ptr.get_cid()	  : self.__evt_socket_add,
			self.bind_ptr.get_cid()	          : self.__evt_bind,
			self.conn_begin_ptr.get_cid()     : self.__evt_conn_begin,
			self.send_to_ptr.get_cid()	  : self.__evt_send_to,
			self.recv_from_ptr.get_cid()      : self.__evt_recv_from,
			self.send_msg_ptr.get_cid()       : self.__evt_send_msg,
			self.recv_msg_ptr.get_cid()       : self.__evt_recv_msg,
			self.sock_send_ptr.get_cid()	  : self.__evt_sock_send,
			self.sock_recv_ptr.get_cid()      : self.__evt_sock_recv,
			self.listen_ptr.get_cid()	  : self.__evt_listen,
			self.accept_ptr.get_cid()	  : self.__evt_accept,
			self.conn_end_ptr.get_cid()       : self.__evt_conn_end,
			self.switch_to_ptr.get_cid()	  : self.__evt_switch_to,
			self.switch_from_ptr.get_cid()    : self.__evt_switch_from,
			self.syscall_ptr.get_cid()	  : self.__evt_syscall,
		}
