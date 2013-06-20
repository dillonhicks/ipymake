from datastreams.postprocess import filtering, entities
from discovery.oca_definitions import *
from discovery.kernel_constants import *


class narration(filtering.Filter):

	def initialize(self):

		self.oca_actions_ptr = self.get_ns_pointer("OCA/ACTIONS")

		self.oca_types = {}
		self.oca_types_num = {}
		self.mapping_oca_types_to_names(self.oca_types)

	def process(self,entity):
		
		dict={}
		dict=entity.get_extra_data()
		oca_type = dict[OCA_TYPE]

		if oca_type in self.oca_types.keys():

			if self.oca_types[oca_type] not in self.oca_types_num.keys(): 
				num = 0
			else: 
				num = self.oca_types_num[self.oca_types[oca_type]] 

			num = num+1
			self.oca_types_num[self.oca_types[oca_type]] = num

	def finalize(self):

	
		for key in self.oca_types_num.keys():
			print "Number of times ",key," : ",self.oca_types_num[key]
			print " "

	def mapping_oca_types_to_names(self,dict):

		dict[OCA_ROOT_THREAD] = "root"
		dict[OCA_FORK] = "fork"
		dict[OCA_SIGNAL_SEND] = "signal"
		dict[OCA_FCTL_LOCK] = "lock"
		dict[OCA_FCTL_UNLOCK] = "unlock"
		dict[OCA_NP_OPEN] = "np_open"
		dict[OCA_SHM_GET] = "shm_get"
		dict[OCA_SHM_ATTACH] = "shm_at"
		dict[OCA_SHM_DETACH] = "shm_dt"
		dict[OCA_PIPE_CREATE] = "pipe_create"
		dict[OCA_PIPE_OPEN] = "pipe_open"
		dict[OCA_FILE_OPEN] = "file_open"
		dict[OCA_PIPE_READ] = "pipe_read"
		dict[OCA_PIPE_WRITE] = "pipe_write"
		dict[OCA_PIPE_CLOSE] = "pipe_close"
		dict[OCA_FILE_CLOSE] = "file_close"
		dict[OCA_NP_CLOSE] = "np_close"


class socket_post(filtering.Filter):

	def initialize(self):
		self.sock_sendmsg_ptr = self.get_ns_pointer("SOCKET/SOCK_SENDMSG")
		
		self.sock_recvmsg_ptr = self.get_ns_pointer("SOCKET/SOCK_RECVMSG")

		self.socket_ptr = self.get_ns_pointer("SOCKET/SOCKET")

		self.sockBind_ptr = self.get_ns_pointer("SOCKET/BIND")

		self.sockListen_ptr = self.get_ns_pointer("SOCKET/LISTEN")
		self.sockAccept_ptr = self.get_ns_pointer("SOCKET/ACCEPT")
	
		self.sockConnectBegin_ptr = self.get_ns_pointer("SOCKET/CONNECT_BEGIN")
	
		self.sockConnectEnd_ptr = self.get_ns_pointer("SOCKET/CONNECT_END")
		self.sockSendTo_ptr = self.get_ns_pointer("SOCKET/SENDTO")

		self.sockRecvFrom_ptr = self.get_ns_pointer("SOCKET/RECVFROM")

		self.sockSendMsg_ptr = self.get_ns_pointer("SOCKET/SENDMSG")

		self.sockRecvMsg_ptr = self.get_ns_pointer("SOCKET/RECVMSG")


		self.exec_ptr 		= self.get_ns_pointer("EXECVE/DO_EXECVE")
#		self.close_ptr = self.get_ns_pointer("FILE/CLOSE");

	def process(self,entity):
		
		if entity.get_cid() == self.sock_sendmsg_ptr.get_cid():
			print "sock_sendmsg() : "
			data = entity.get_extra_data()
			self.printing(data)
			
		if entity.get_cid() == self.sock_recvmsg_ptr.get_cid():
			print "sock_recvmsg() : "
			data = entity.get_extra_data()
			self.printing(data)
		if entity.get_cid() == self.socket_ptr.get_cid():
			print "sys_socket() : "
			data = entity.get_extra_data()
			self.printing(data)
		if entity.get_cid() == self.sockBind_ptr.get_cid():
			print "sys_bind() : "
			data = entity.get_extra_data()
			self.printing(data)
		if entity.get_cid() == self.sockListen_ptr.get_cid():
			print "sys_listen() : "
			data = entity.get_extra_data()
			self.printing(data)
		if entity.get_cid() == self.sockAccept_ptr.get_cid():
			print "sys_accept() : "
			data = entity.get_extra_data()
			self.printing(data)
		if entity.get_cid() == self.sockConnectBegin_ptr.get_cid():
			print "sys_connect() Begin : "
			data = entity.get_extra_data()
			self.printing(data)
		if entity.get_cid() == self.sockConnectEnd_ptr.get_cid():
			print "sys_connect() End : "
			data = entity.get_extra_data()
			self.printing(data)
		if entity.get_cid() == self.sockSendTo_ptr.get_cid():
			print "sys_sendto()  : "
			data = entity.get_extra_data()
			self.printing(data)
		if entity.get_cid() == self.sockRecvFrom_ptr.get_cid():
			print "sys_recvfrom() : "
			data = entity.get_extra_data()
			self.printing(data)
		if entity.get_cid() == self.sockSendMsg_ptr.get_cid():
			print "sys_sendmsg() : "
			data = entity.get_extra_data()
			self.printing(data)
		if entity.get_cid() == self.sockRecvMsg_ptr.get_cid():
			print "sys_recvmsg() : "
			data = entity.get_extra_data()
			self.printing(data)
		if entity.get_cid() == self.exec_ptr.get_cid():
			print "exec : ", entity.get_extra_data()
			print " "

	#	if entity.get_cid() == self.close_ptr.get_cid():
	#		print "CLOSE : ", entity.get_extra_data()


	def finalize(self):

		print "socket postprocessing completed"

	def printing(self,dict):

		print "Source port : ", dict["sport"], "\tDestination port :", dict["dport"]
		print "Source IP address : ", dict["saddr"],  "\tDestination IP address : ", dict["daddr"]
		print "Pid : ", dict["pid"],  "\tSocket fd : ", dict["fd"]
		print "Socket inode id : ",dict["inode_id"],  "\tSocket sys id : ", dict["sys_id"]
		print " "
