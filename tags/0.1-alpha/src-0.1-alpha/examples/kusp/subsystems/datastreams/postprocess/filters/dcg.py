#!/usr/bin/env python

"""
Example use of networkx to represent computation structure as
discovered by observing and analyzing computation component actions
through DSKI instrumentation. This code is the first basic prototype
intended to experiment with and serve as an example for techniques
we will use in the actual DS post-processing filters that will derive
the discovered computational structure from a series of records/events
describing relevant actions by the computation.

"""

import networkx as NX
import pylab    as PL

#
# Import the the Observed Computation Action definitions
#
from discovery.oca_definitions import *

######################################################################
# Build a graph representing the discovered computation structure. 
#
# Each node in the Discovered Computation Graph (DCG) represents a
# component playing a role in the computation, Threads are the most
# obvious node types but other node types include: semaphores, pipes,
# sockets, named pipes, file locks, and others as required to support
# the evolving set of things we can discover about a computation.
#
# Each edge in the DCG represents a relation among computation
# components. Generally, this means that an action taken by a thread
# component created the relation to another component. Sometimes the
# action creates a relation among components already represented by
# DCG nodes, sometimes the relation add a new component to the set
# represented by the DCG, and soemtimes, as with FORK, it involves the
# creation of a new component.
#
# We assume that the information from which we deduce the computation
# structure is presented as a series of observations about how the
# computation behaves, i.e. a series of Observed Computation Actions
# (OCA). Each OCA has associated information specific to the action,
# which is used to make the appropriate changes to the graph
# representing the computation.
#
# Each node in the graph is a hashable tuple (node_type, node_label).
# Any additional information about nodes can be stored in the
# Node_attributes dictionary which uses the (node_type, node_label) as
# a key. Each entry is itself a dictionary using node_type specific
# node attribute keys, including: size, sub-type, total data volume,
# number of uses, perhaps even histograms.
#
# Each edge is an NX data structure, but because we are using the
# XDIgraph graph type, an arbitrary object can be attached to each
# edge. This is a dictionary describing the edge attributes, directly
# analogous to the Node_attributes dictionary. DCG edge types and edge
# attribute record types are defined with the OCA routines that create
# the edges.
######################################################################

#
# Hash table indexed by (node_type, node_label) tuples which holds the
# set of attributes for that node. If the NX.XDiGraph permitted us to
# attach arbitrary object to nodes as it does edges, this would not be
# required.
#
Node_attributes = {}

#
# DCG Node Type Key, and Acceptable Node Type Values
#
# The following lists are the valide DCG Node types.  Also, virtually
# every node will have a label. When possible labels will be
# meaningful character strings. In some cases, however, the only
# available label may be hex numbers. 
#
# Attribute definitions are useful, in many cases, for more than one
# node type. The most fundamental attribute is the node type. This
# information is redundant, since it is also the first element of the
# (node_type, node_label) tuple used as the key for the
# Node_attributes dictionary, but storign the type as an attribute
# makes accessing node attributes completely and consistent.  The
# string representation attribute is partially redundant with the
# "node_label" portion of the Node_attributes key, but takes a
# slightly more readable form.
#

################################# TODO ##################################
#
# Continue testing new open, close, read, write stuff. Put dup and
# dup2 in here
#
#########################################################################

DCG_NA_TYPE   = "Node Type" 
DCG_NA_ID     = "Unique ID"
DCG_NA_STRING = "String Repr"
DCG_NA_MODE   = "Mode"
DCG_NA_EXEC   = "Execed Process"
DCG_NA_FDS    = "File Descriptors"
DCG_NA_GEN    = "Generation"
DCG_NA_REL    = "Relationship"
DCG_NA_UNIQUE_SOCKET_NAME = "Socket Name DCG"
#
# These DCG node type key values represent the components whose
# existence we can deduce from the computation's use of system calls
#
DCG_NT_UTHREAD    = "User Thread"
DCG_NT_PIPE       = "Pipe"
DCG_NT_NAMED_PIPE = "NPipe"
DCG_NT_SEM        = "SV SEM"
DCG_NT_SHM        = "SV SHM"
DCG_NT_FILE_LOCK  = "File Lock"
DCG_NT_SOCKET     = "Socket"
DCG_NT_PTRACE	  = "Ptrace"
DCG_NT_FILE	  = "File"
DCG_NT_PSEUDOT    = "Pseudo Terminal"
DCG_NT_UNKNOWN    = "Unknown"

#
# This set of DCG Node type key values represent computation
# components that exist within the kernel, but which are part of the
# DCG because they support the computation, and thus they affect
# computation behavior and may also be potential interaction channels,
# wrt execution security analysis.
#
DCG_NT_KTHREAD    = "K-Thread"
DCG_NT_HARDIRQ    = "H-IRQ"
DCG_NT_SOFTIRQ    = "S-IRQ"
DCG_NT_MUTEX      = "K-Mutex"
DCG_NT_RWLOCK     = "R/W Lock"
DCG_NT_SEQLOCK    = "SEQ Lock"
DCG_NT_MEMORY     = "Memory"
DCG_NT_MODULE     = "Module"

#
# This is a placeholder for the DCG node types that represent
# user-level components of a computation that are not threads.  The
# FUTEX type is special in that it exists only at the user level when
# no contention exists, but when contention occurs, a kernel-level
# mutex is created to help with management. Other user-level component
# candidates include any shared data structures. However, under
# threaded programming models it is unlikely we can track these
# interaction channels unless we have sophisticated compiler support.
#
DCG_NT_FUTEX      = "Futex"


CT_NT_Map = {
	AC_UTHREAD : DCG_NT_UTHREAD,
	PC_PIPE    : DCG_NT_PIPE,
	PC_FIFO    : DCG_NT_NAMED_PIPE,
	PC_SEM     : DCG_NT_SEM,
	PC_SHM     : DCG_NT_SHM,
	PC_FILE    : DCG_NT_FILE,
	PC_SOCKET  : DCG_NT_SOCKET,
	PC_PSEUDOT : DCG_NT_PSEUDOT,
	PC_UNKNOWN : DCG_NT_UNKNOWN
}

def CT_2_NT(comp_type):
	if CT_NT_Map.has_key(comp_type):
		return CT_NT_Map[comp_type]
	else:
		print "Unknown component type in conversion to node type", comp_type
		raise AssertionError

#
# Active and passive components each have their own identifiers. Each 
# node in the DCG is identified as either an active or passive 
# component. A more specific description of the node is given by the 
# DCG_NA_TYPE attribute
#
DCG_AC_NODE       = "AC Node"
DCG_PC_NODE       = "PC Node"

#
# DCG Edge Types
#
# Attributes of edges are defined in response to the need of various
# relations among nodes to express a specific set of information
# related to the relation among two nodes represented by the edge.

# Attribute Dictionary Key
DCG_EA_TYPE   = "Edge Type"


# Attributes associated with various edges
#
DCG_EA_MODE   = "Mode"
DCG_EA_FD     = "FD"
DCG_EA_STRING = "String Repr"
DCG_EA_SIGNUM = "Signal Number"
DCG_EA_COUNT  = "Count"

# Edge Attribute: TYPE 
# Type values
#
# Just brain-storming possible types here. I am not sure how many of
# these will really be used, or useful. A lot depends on what kinds of
# analyses we want to do. A particularly subtle point is that some
# kinds of analysis woudl include creating new graphs with new edge
# types beyond the basic types used for the original DCG
#
DCG_ET_FORK       = "Fork"

# These could be relations/edges in a derived graph which examines
# descendant relationships which can be derived from the primitive
# "fork" relations. I hav no idea if this will turn out to be a good
# idea or not, so I lave it at defining the edge types for now.
DCG_ET_PARENT     = "Parent"
DCG_ET_CHILD      = "Child"
DCG_ET_DESCENDANT = "Descendant"
DCG_ET_ANCESTOR   = "Ancestor"

# Edge types 
#
DCG_ET_SIGNAL      = "Signal"
DCG_ET_OPEN        = "Open"
DCG_ET_CLOSE       = "Close"
DCG_ET_READ        = "Read"
DCG_ET_WRITE       = "Write"
DCG_ET_LOCK        = "Lock"
DCG_ET_UNLOCK      = "Unlock"
DCG_ET_USE         = "Use"
DCG_ET_MASTER	   = "Ptrace Master"
DCG_ET_SLAVE	   = "Ptrace Slave"
DCG_ET_SHMAT	   = "SHM Attach"
DCG_ET_SHMDT	   = "SHM Detach"
DCG_ET_IN_FD       = "Inherit FD"
DCG_ET_IN_SHM      = "Inherit SHM"

# FIXME: Do this in the OCA pre process filter
# A dictionary to hold the number of times a process has locked 
# a file, we need this count so that we can attach the number
# of times the same process has locked the same file for reading
# or writing, the key to this dictionary is the pid of the process 

lock_count = {}

# FIXME: Do this in the OCA pre process filter
# A dictionary to hold the number of times a process has unlocked 
# a file, we need this count so that we can attach the number
# of times the same process has unlocked the same file,
# the key to this dictionary is the pid of the process 

unlock_count = {}

# Get graphviz to detemine the layout of *all* the nodes in the
# graph. There are several options. In the case of the family
# tree, the "dot" layout command give a good family tree view.
# How this will work when the graph is complex, representing a
# large number of relations, is unclear. For the moment, we will
# take one layout, and just draw subsets of it as specified by the
# drawing_options. Later on, we may want to create subset graphs,
# and lay them out individually
#
# The documentation of this does not seem to exist, but an error
# message indicated a list of choices some of which did not work,
# but these did: twopi, fdp, circo, neato, dot
#

def do_layout(DCG, prog):
    return NX.graphviz_layout(DCG, prog)

# 
# Generic encapsuation routine for creating a DCG node data
# structure. The Networkx framework permits the nodes in a graph to be
# any hashable object, so for the moment, we use a tuple (node_type,
# node_label).  A global Node_attributes dictionary index by these
# tuples is used to track arbitrary sets of information associated
# with each node. Many nodes, if not all, will have the DCG_NA_STRING
# attribtue, which is its human-readable string representation. Used
# for diagrams if nothing else.
#
def create_DCG_node_tag(node_type, node_label):
    new_node_tag = (node_type, node_label)
    Node_attributes[new_node_tag] = {}
    return new_node_tag

#
# Generic encapsulation routine for creating an edge attribite data
# set. This is simple for the moment, but we encapsulate because it
# may become a good deal more complex.
#
def create_DCG_edge_attr(edge_type):
    edge_attr = {}
    edge_attr[DCG_EA_TYPE] = edge_type
    return edge_attr


def get_edge_wtype(DCG, type, u, v=None):
	for edge in DCG.edges(u):
		if edge[1] == v and edge[2][DCG_EA_TYPE] == type:
			return edge
	return None

#####################################################################
# The following routines individually represent the graph
# modifications we make in response to each of the valid OCA types
#####################################################################
def oca_root_thread(DCG, OCA):
	"""
	This OCA event occurs when the preprocess filter identifies a
	first generation thread.  
	"""
	new_node = create_DCG_node_tag(DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
	new_node_attr = Node_attributes[new_node]
	new_node_attr[DCG_NA_TYPE]   = CT_2_NT(OCA[OCA_ARG_AC_TYPE])
	new_node_attr[DCG_NA_STRING] = OCA[OCA_ARG_AC_NAME]
	new_node_attr[DCG_NA_GEN]    = OCA[OCA_ARG_GEN]
	new_node_attr[DCG_NA_REL]    = OCA[OCA_ARG_REL]
	new_node_attr[DCG_NA_EXEC]   = OCA[OCA_ARG_EXEC_NAME]
	DCG.add_node(new_node)

#
# Creating New Threads
#
# Three types of new thread creation: fork, spawn, kernel-thread.
# Forking creates a new thread witha new address space. Spawning
# creates a new thread sharing the address space with the
# parent. Creation of a kernel thread is similar, but distinct,
# because all kernel threads share the OS address space, and remain in
# kernel mode.
#
def oca_fork(DCG, OCA):
	"""
	Parent forking a child. First we make sure that the 
	parent node is already part of the DCG. If so, then add
	the edge (parent,child,attr) to the DCG
	"""
	parent_tag = (DCG_AC_NODE, OCA[OCA_ARG_PARENT_ID])
	if DCG.has_node(parent_tag):
		# Create the tag for the child node, and the edge attribute
		# dictionary. 
		#
		child_tag = (DCG_AC_NODE, OCA[OCA_ARG_CHILD_ID])
		edge_attr = create_DCG_edge_attr(DCG_ET_FORK)

		# For the moment we play with having an edge attribute
		# providing a string representation of what it means.
		# Adding the edge creates the child node.
		#
		edge_attr[DCG_EA_STRING] = "%s --fork--> %s" % (OCA[OCA_ARG_PARENT_NAME], OCA[OCA_ARG_CHILD_NAME])
		DCG.add_edge(parent_tag, child_tag, edge_attr)

		# Now that the child node has been created by creating the
		# edge, create its attributes structure and fill in the Node
		# attribute that will be used as the node labels in the
		# drawings and in test output.
		#
		Node_attributes[child_tag] = {}
		child_attr                = Node_attributes[child_tag]
		child_attr[DCG_NA_TYPE]   = CT_2_NT(OCA[OCA_ARG_CHILD_TYPE])
		child_attr[DCG_NA_STRING] = OCA[OCA_ARG_CHILD_NAME]
		child_attr[DCG_NA_GEN]    = OCA[OCA_ARG_GEN]
		child_attr[DCG_NA_REL]    = OCA[OCA_ARG_REL]
		child_attr[DCG_NA_EXEC]   = OCA[OCA_ARG_EXEC_NAME]

		# Create edges to inherited references
		#
		in_fds  = OCA[OCA_ARG_IN_FDS]
		for fd in OCA[OCA_ARG_IN_FDS].iterkeys():
		#	print "pc name : ", in_fds[fd]
			pc_tag  = (DCG_PC_NODE, in_fds[fd][OCA_ARG_PC_ID])
			if not DCG.has_node(pc_tag):
#				print pc_tag
				print "ERROR: Inherited FD to PC node not in the DCG", OCA
				raise AssertionError
						
			pc_name = Node_attributes[pc_tag][DCG_NA_STRING]
			edge_attr = create_DCG_edge_attr(DCG_ET_IN_FD)
			edge_attr[DCG_EA_FD]     = `fd`
			edge_attr[DCG_EA_MODE]   = `in_fds[fd][OCA_ARG_MODE]`
			edge_attr[DCG_EA_STRING] = "%s --Inherited--> %s on FD %d" % (OCA[OCA_ARG_CHILD_NAME], pc_name, fd)
			DCG.add_edge(child_tag, pc_tag, edge_attr)	

		in_shms = OCA[OCA_ARG_IN_SHMS]
		for shm in OCA[OCA_ARG_IN_SHMS].iterkeys():
			pc_tag = (DCG_PC_NODE, in_fds[shm][OCA_ARG_PC_ID])
			if not DCG.has_node(pc_tag):
				print "ERROR: Inherited FD to PC node not in the DCG", OCA
				raise AssertionError
						
			pc_name = Node_attributes[pc_tag][DCG_NA_STRING]
			edge_attr = create_DCG_edge_attr(DCG_ET_IN_SHM)
			edge_attr[DCG_EA_SHMADDR] = `shm`
			edge_attr[DCG_EA_MODE]    = `in_fds[fd][OCA_ARG_MODE]`
			edge_attr[DCG_EA_STRING]  = "%s --Inherited--> %s on SHMADDR %d" % (OCA[OCA_ARG_CHILD_NAME], pc_name, shm)
			DCG.add_edge(child_tag, pc_tag, edge_attr)	
	else:
		print "ERROR: Parent of OCA_FORK is not a node in the DCG", OCA
		raise AssertionError

def oca_spawn(DCG, OCA):
	print "oca_spawn"

def oca_kernel_fork(DCG, OCA):
	print "oca_kernel_fork"

def oca_root_fd(DCG, OCA):
	"""
	The root thread's file descriptor table is recorded in the active filter.
	We use these events to initialize this table for our computation.
	"""
	root_tag = (DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
	if not DCG.has_node(root_tag):
		print "ERROR: Root node for root_fd is not a node in the DCG", OCA
		raise AssertionError

	pc_id   = OCA[OCA_ARG_PC_ID]
	pc_tag  = (DCG_PC_NODE, pc_id)
	if not DCG.has_node(pc_tag):
		# Create the PC if it does not yet exist
		#
		DCG.add_node(pc_tag)
		Node_attributes[pc_tag] = {}
		pc_attr = Node_attributes[pc_tag]
		pc_attr[DCG_NA_TYPE]   = CT_2_NT(OCA[OCA_ARG_PC_TYPE])
		pc_attr[DCG_NA_ID]     = pc_id
		pc_attr[DCG_NA_STRING] = OCA[OCA_ARG_PC_NAME]
	
	edge_attr = create_DCG_edge_attr(DCG_ET_IN_FD)
	edge_attr[DCG_EA_FD]     = `OCA[OCA_ARG_FD]`
	edge_attr[DCG_EA_MODE]   = `OCA[OCA_ARG_MODE]`
	edge_attr[DCG_EA_STRING] = "%s --Inherited--> %s on FD %d" % (OCA[OCA_ARG_AC_NAME], OCA[OCA_ARG_PC_NAME], OCA[OCA_ARG_FD])
	DCG.add_edge(root_tag, pc_tag, edge_attr)	

#####################################################################
# Key definitions related to observing a signal action
#
def oca_signal_send(DCG, OCA):
    """
    The Sender process is sending a signal to the Receiver process So,
    we create and edge fromt he sender to the receiver. We store the
    edge type ans an attribute, and the signal number as well.
    """
    # The sender must be part of the current DCG but the receiver may
    # or may not be. If it is not, then we add the receiver node to
    # the growing DCG
    #
    sender_tag   = (DCG_AC_NODE, OCA[OCA_ARG_SENDER])
    if DCG.has_node(sender_tag):
        # Create the tag for the receiver node. If the receiver node
        # not not already exist in the DCG then add it.
        #
        receiver_tag = (DCG_AC_NODE, OCA[OCA_ARG_RECEIVER])
        if not DCG.has_node(receiver_tag):
            DCG.add_node(receiver_tag)
            Node_attributes[receiver_tag] = {}
            receiver_attr = Node_attributes[receiver_tag]
            receiver_attr[DCG_NA_TYPE] = CT_2_NT(OCA[OCA_ARG_AC_TYPE])
            receiver_attr[DCG_EA_STRING] = "T%d" % (OCA[OCA_ARG_RECEIVER])

        # Set the edge STRING attribute that describes the edge, as
        # well as the one that noes the signal number. 
        #
        # FIXME: It is not clear why, but the edge attribute values
        # MUST BE STRINGS, even the signal number. If not, it causes
        # an exception in NX.graphviz_layout when we try to draw the
        # graph. When we start drawing only subsets of the full graph
        # this may no longer be necessary. Or, we might prefer to
        # create a copy of the graph for drawing purposes, that does
        # not have attributes.
        #
        edge_attr = create_DCG_edge_attr(DCG_ET_SIGNAL)
        edge_attr[DCG_EA_STRING] = "UT%d --Signal--> UT%d" % (OCA[OCA_ARG_SENDER], OCA[OCA_ARG_RECEIVER])
        edge_attr[DCG_EA_SIGNUM] = "%s" % (OCA[OCA_ARG_SIGNAL_NUMBER])
        DCG.add_edge(sender_tag, receiver_tag, edge_attr)
    else:
        print "ERROR: Sender of OCA_SIGNAL is not a node in the DCG", OCA


# TODO: Consider collapsing these sets of functions for open/close
# read/write on different types of PCs into one set of functions
# that handles all types of PCs.

def oca_open(DCG, OCA):
	"""
	A process opens a file (i.e. obtains a file descriptor to some PC).

	Because of the way the instrumentation is set up, this covers
	every type of PC except for sockets and pipes (regular pipes,
	named pipes are covered here). Use the custom socket and pipe open
	functions to modify the graph for these events.
	"""
	# The opener must be part of the current DCG but the PC may or may
	# not be. If it is not, then we add the NP node to the growing
	# DCG, and then add an edge from the process to the opener.
	#
	opener_tag = (DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
	if DCG.has_node(opener_tag):
		# Create the tag for the opened NP node. If the NP node does
		# not not already exist in the DCG then add it.
		#

		# FIXME: We are assuming files  are not being actively created 
		# and destroyed. If they are, using (inode, sys_id) pairs are not 
		# true unique identifiers
		#
		pc_id   = OCA[OCA_ARG_PC_ID]
		pc_tag  = (DCG_PC_NODE, pc_id)
		if not DCG.has_node(pc_tag):
			DCG.add_node(pc_tag)
			Node_attributes[pc_tag] = {}
			pc_attr = Node_attributes[pc_tag]
			pc_attr[DCG_NA_TYPE]   = CT_2_NT(OCA[OCA_ARG_PC_TYPE])
			pc_attr[DCG_NA_ID]     = pc_id
			pc_attr[DCG_NA_STRING] = OCA[OCA_ARG_PC_NAME]
			#print OCA[OCA_ARG_PC_NAME]

		# Set the edge STRING attribute that describes the edge, as
		# well as the one that notes the NPID
		#
		edge_attr = create_DCG_edge_attr(DCG_ET_OPEN)
		edge_attr[DCG_EA_FD]     = `OCA[OCA_ARG_FD]`
		edge_attr[DCG_EA_MODE]   = `OCA[OCA_ARG_MODE]`
		edge_attr[DCG_EA_STRING] = "%s --Opened--> %s on FD %d" % (OCA[OCA_ARG_AC_NAME], OCA[OCA_ARG_PC_NAME], OCA[OCA_ARG_FD])
		DCG.add_edge(opener_tag, pc_tag, edge_attr)
	else:
        	print "ERROR: Opener of OCA_FILE_OPEN is not a node in the DCG", OCA
		raise AssertionError

def oca_close(DCG, OCA):
	"""
	A process closes a file descriptor. 
	"""
	# The closer must be part of the current DCG and the NP must also
	# be. 
	#
	closer_tag = (DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
	if DCG.has_node(closer_tag):
		# Create the tag for the closed NP node. If the NP node does
		# not not already exist in the DCG then this is an error.
		#
		pc_id   = OCA[OCA_ARG_PC_ID]
		pc_tag  = (DCG_PC_NODE, pc_id)
		if pc_id[0] == "devpts":
			return
		if DCG.has_node(pc_tag):
			# Set the edge STRING attribute that describes the edge
			#
#			print "closer tag : ",closer_tag
#			print "pc_id of close : ", pc_id
			closer_str = Node_attributes[closer_tag][DCG_NA_STRING]
			pc_str     = Node_attributes[pc_tag][DCG_NA_STRING]
			edge_attr  = create_DCG_edge_attr(DCG_ET_CLOSE)
			edge_attr[DCG_EA_FD] = `OCA[OCA_ARG_FD]`
			edge_attr[DCG_EA_STRING] = "%s --Closed--> %s on FD %d" % (closer_str, pc_str, OCA[OCA_ARG_FD])
			DCG.add_edge(closer_tag, pc_tag, edge_attr)
		else:
			print "ERROR: PIPE of OCA_Pipe_Close is not a node in the DCG"#, OCA
		#	raise AssertionError
	else:
		print "ERROR: Closer of OCA_FILE_Close is not a node in the DCG", OCA
		#raise AssertionError

def oca_read(DCG, OCA):
	"""
	A process reads on a file descriptor. 
	"""
	# The reader must be part of the current DCG and the NP must also
	# be. 
	#
	reader_tag = (DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
	if DCG.has_node(reader_tag):
		# Create the tag for the closed NP node. If the NP node does
		# not not already exist in the DCG then this is an error.
		#
		pc_id   = OCA[OCA_ARG_PC_ID]
		pc_tag  = (DCG_PC_NODE, pc_id)
		if DCG.has_node(pc_tag):
			# Set the edge STRING attribute that describes the edge
			#
			reader_str = Node_attributes[reader_tag][DCG_NA_STRING]
			pc_str     = Node_attributes[pc_tag][DCG_NA_STRING]
			read_edge  = get_edge_wtype(DCG, DCG_ET_READ, reader_tag, pc_tag)
			if read_edge:
				edge_attr = read_edge[2]
				count = int(edge_attr[DCG_EA_COUNT]) + OCA[OCA_ARG_SIZE]
				edge_attr[DCG_EA_COUNT] = `count`
			else:
				edge_attr  = create_DCG_edge_attr(DCG_ET_READ)
				edge_attr[DCG_EA_FD] = `OCA[OCA_ARG_FD]`
				edge_attr[DCG_EA_COUNT] = `OCA[OCA_ARG_SIZE]`
				edge_attr[DCG_EA_STRING] = "%s --Read--> %s on FD %d" % (reader_str, pc_str, OCA[OCA_ARG_FD])
				DCG.add_edge(reader_tag, pc_tag, edge_attr)
		else:
			print "ERROR: PIPE of OCA_Pipe_Read is not a node in the DCG"#, OCA
			#raise AssertionError
	else:
		print "ERROR: Reader of OCA_Pipe_Read is not a node in the DCG"#, OCA
		#raise AssertionError

def oca_write(DCG, OCA):
	"""
	A process writes on a file descriptor. 
	"""
	# The writer must be part of the current DCG and the NP must also
	# be. 
	#
	writer_tag = (DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
	if DCG.has_node(writer_tag):
		# Create the tag for the closed NP node. If the NP node does
		# not not already exist in the DCG then this is an error.
		#
		pc_id   = OCA[OCA_ARG_PC_ID]
		pc_tag  = (DCG_PC_NODE, pc_id)

	# A fix for making the graph to work. getting a write event from a non familial Ac
	# with respect to devpts. this happens when i run my experiment by sshing from an outside network
	# will have to do something about this.
		if pc_id[0] =="devpts":
			return

		if DCG.has_node(pc_tag):
			# Set the edge STRING attribute that describes the edge
			#
			writer_str = Node_attributes[writer_tag][DCG_NA_STRING]
			pc_str     = Node_attributes[pc_tag][DCG_NA_STRING]
			write_edge = get_edge_wtype(DCG, DCG_ET_WRITE, writer_tag, pc_tag)
			if write_edge:
				edge_attr = write_edge[2]
				count = int(edge_attr[DCG_EA_COUNT]) + OCA[OCA_ARG_SIZE]
				edge_attr[DCG_EA_COUNT] = `count`
			else:
				edge_attr  = create_DCG_edge_attr(DCG_ET_WRITE)
				edge_attr[DCG_EA_FD] = `OCA[OCA_ARG_FD]`
				edge_attr[DCG_EA_COUNT] = `OCA[OCA_ARG_SIZE]`
				edge_attr[DCG_EA_STRING] = "%s --Wrote--> %s on FD %d" % (writer_str, pc_str, OCA[OCA_ARG_FD])
				DCG.add_edge(writer_tag, pc_tag, edge_attr)
		else:
			print "ERROR: PIPE of OCA_Pipe_Write is not a node in the DCG"#, OCA
			#raise AssertionError
	else:
		print "ERROR: Writer of OCA_FILE_Write is not a node in the DCG", OCA
		#raise AssertionError

def oca_pipe(DCG, OCA):
	"""
	A process creates a pipe with the pipe system call
	"""
	# The piper must be part of the current DCG but the pipe should
	# not be.
	#
	piper_tag = (DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
	if DCG.has_node(piper_tag):
		# Create the tag for the opened pipe node. This corresponds to
		# pipe creation, so the pipe node should not exist already.
		# TODO: Instrument dup and dup2 to add to the fds attribute
		#
		pipe_tag = (DCG_PC_NODE, OCA[OCA_ARG_PC_ID])
        	if not DCG.has_node(pipe_tag):
			DCG.add_node(pipe_tag)
			Node_attributes[pipe_tag] = {}
			pipe_attr = Node_attributes[pipe_tag]
			pipe_attr[DCG_NA_TYPE]   = DCG_NT_PIPE
			pipe_attr[DCG_NA_STRING] = OCA[OCA_ARG_PC_NAME]
		else:
			print "ERROR: got oca_pipe for pipe that already exists.", OCA
			raise AssertionError

		# Set the edge STRING attribute that describes the edge, as
		# well as the one that notes the Pipe name
		#
		r_edge = create_DCG_edge_attr(DCG_ET_OPEN)
		r_edge[DCG_EA_STRING] = "%s --PipeOpenRead--> %s on FD %d" % (OCA[OCA_ARG_AC_NAME], OCA[OCA_ARG_PC_NAME], OCA[OCA_ARG_FD_READ])
		#r_edge[DCG_EA_MODE] = OCA[OCA_ARG_MODE_READ]
		w_edge = create_DCG_edge_attr(DCG_ET_OPEN)
		w_edge[DCG_EA_STRING] = "%s --PipeOpenWrite--> %s on FD %d" % (OCA[OCA_ARG_AC_NAME], OCA[OCA_ARG_PC_NAME], OCA[OCA_ARG_FD_WRITE])
		#w_edge[DCG_EA_MODE] = OCA[OCA_ARG_MODE_WRITE]
		DCG.add_edge(piper_tag, pipe_tag, r_edge)
		DCG.add_edge(piper_tag, pipe_tag, w_edge)
	else:
		print "ERROR: Opener of OCA_OPEN is not a node in the DCG", OCA
	    	raise AssertionError

def oca_ptrace_attach(DCG, OCA):
	"""
	The process is making use of the ptrace system call to
	establish a master / slave relationship (either via the
	slave using the TRACEME request or the master using the
	ATTACH request.
	"""
	master_tag = (DCG_AC_NODE, OCA[OCA_PTRACE_MASTER_ID])
	slave_tag = (DCG_AC_NODE, OCA[OCA_PTRACE_SLAVE_ID])

	# The master can attach an arbitrary pid using the PTRACE_ATTACH
	# request. In this case, the slave node might not be in the graph
	#
	if not DCG.has_node(slave_tag):
		DCG.add_node(slave_tag)
		Node_attributes[slave_tag] = {}
		slave_attr = Node_attributes[slave_tag]
		slave_attr[DCG_NA_TYPE] = CT_2_NT(OCA[OCA_ARG_AC_TYPE])
		slave_attr[DCG_NA_STRING] = OCA[OCA_PTRACE_SLAVE_NAME]

	assert DCG.has_node(master_tag) and DCG.has_node(slave_tag)
			
	# Create ptrace edges representing master / slave relationship
	edge_attr = create_DCG_edge_attr(DCG_ET_MASTER)
	edge_attr[DCG_EA_STRING] = "%s --ptrace-master--> %s" % (OCA[OCA_PTRACE_MASTER_NAME], OCA[OCA_PTRACE_SLAVE_NAME])
	DCG.add_edge(master_tag, slave_tag, edge_attr)

	edge_attr = create_DCG_edge_attr(DCG_ET_SLAVE)
	edge_attr[DCG_EA_STRING] = "%s --ptrace-slave--> %s" % (OCA[OCA_PTRACE_SLAVE_NAME], OCA[OCA_PTRACE_MASTER_NAME])
	DCG.add_edge(slave_tag, master_tag, edge_attr)

def oca_ptrace_detach(DCG, OCA):
	"""
	This detaches a master / slave relationship
	"""
	pass

def oca_exec(DCG, OCA):
	"""
	The process is using the exec system call to exec some
	program. Here we add the program's name as an attribute
	of the user thread node that is calling exec
	"""
	exec_thread_tag = (DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
	if DCG.has_node(exec_thread_tag):
		# Under the current design, an exec event may change
		# the generation assigned to the AC
		exec_thread_attr = Node_attributes[exec_thread_tag]
		exec_thread_attr[DCG_NA_EXEC] = OCA[OCA_ARG_EXEC_NAME]
		exec_thread_attr[DCG_NA_GEN]  = OCA[OCA_ARG_GEN]
	else:
		print "ERROR: User thread node: %d calling exec does not exist in DCG" % OCA[OCA_ARG_AC_ID]
		raise AssertionError

def oca_fctl_lock(DCG, OCA):
    """
    The process is using the fcntl system call with the argument
    F_SETLKW to lock a file. Here we create a node for the file 
    being locked and also we create an edge from the user thread
    to the file and we also keep track of times the same user
    thread locks a file

    print "oca_fctl_lock"
    opener_tag = (DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
    if DCG.has_node(opener_tag):
        # Create the tag for the opened file node. If the file node does
        # not not already exist in the DCG then add it.
        #

	lock_id = OCA[OCA_ARG_PC_ID]
        lock_tag = (DCG_NT_FILE_LOCK, lock_id)

        if not DCG.has_node(lock_tag):
            DCG.add_node(lock_tag)
            Node_attributes[lock_tag] = {}
            lock_attr = Node_attributes[lock_tag]
            lock_attr[DCG_NA_TYPE]      = DCG_NT_FILE_LOCK
	    lock_attr[DCG_EA_STRING]    = "File (SysID: %s, Inode ID: %d)" % (OCA[OCA_ARG_PC_ID][0], OCA[OCA_ARG_PC_ID][1])

        # Set the edge STRING attribute that describes the edge, as
        # well as the one that notes the NPID
        #
        # FIXME: It is not clear why, but the edge attribute values
        # MUST BE STRINGS, even the signal number. If not, it causes
        # an exception in NX.graphviz_layout when we try to draw the
        # graph. When we start drawing only subsets of the full graph
        # this may no longer be necessary. Or, we might prefer to
        # create a copy of the graph for drawing purposes, that does
        # not have attributes.
        #
        edge_attr = create_DCG_edge_attr(DCG_ET_LOCK)
	edge_attr[DCG_EA_STRING] = "UT%d --LOCK--> File (SysID: %s, Inode ID: %d)" \
			% (OCA[OCA_ARG_AC_ID], OCA[OCA_ARG_PC_ID][0], OCA[OCA_ARG_PC_ID][1])

	if OCA[OCA_ARG_AC_ID] not in lock_count.keys():
		lock_count[OCA[OCA_ARG_AC_ID]] = 1
		edge_attr[DCG_EA_COUNT] = "UT%d --LOCK COUNT --> FILE(SysID: %s, Inode ID: %d) --> %d" \
				% (OCA[OCA_ARG_AC_ID], OCA[OCA_ARG_PC_ID][0], OCA[OCA_ARG_PC_ID][1], \
       				   lock_count[OCA[OCA_ARG_AC_ID]])
        	DCG.add_edge(opener_tag, lock_tag, edge_attr)
	else:
		lock_count[OCA[OCA_ARG_AC_ID]] = lock_count[OCA[OCA_ARG_AC_ID]]+1
		gr = DCG.get_edge(opener_tag,lock_tag)   
		gr[0][DCG_EA_COUNT] = "UT%d --LOCK COUNT --> FILE(SysID: %s, Inode ID: %d) --> %d" \
				% (OCA[OCA_ARG_AC_ID], OCA[OCA_ARG_PC_ID][0], OCA[OCA_ARG_PC_ID][1], \
       				   lock_count[OCA[OCA_ARG_AC_ID]])
    else:
        print "ERROR: Opener of OCA_FCNTL_LOCK is not a node in the DCG", OCA
    """
    pass

def oca_fctl_unlock(DCG, OCA):
    """ 
    The process is using the fcntl system call with the argument 
    F_SETLK to unlock the file. here we just add a edge from the 
    file to the user thread that is trying to unlock the file  

    print "oca_file_unlock"
    unlock_tag = (DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
    if DCG.has_node(unlock_tag):
        # Create the tag for the locked file node. If the locked file node does
        # not already exist in the DCG then this is an error.
        #
	lock_id = OCA[OCA_ARG_PC_ID]
        lock_tag = (DCG_NT_FILE_LOCK, lock_id)

        if DCG.has_node(lock_tag):
            # Set the edge STRING attribute that describes the edge
            #
            edge_attr = create_DCG_edge_attr(DCG_ET_UNLOCK)
	    edge_attr[DCG_EA_STRING] = "File (SysID: %s, Inode ID: %d) --UNLOCK--> UT%d" \
			    % (OCA[OCA_ARG_PC_ID][0], OCA[OCA_ARG_PC_ID][1], OCA[OCA_ARG_AC_ID])
	    
	    if OCA[OCA_ARG_AC_ID] not in unlock_count.keys():
		unlock_count[OCA[OCA_ARG_AC_ID]] = 1
		edge_attr[DCG_EA_COUNT] = "UT%d --UNLOCK COUNT --> FILE(SysID: %s Inode ID: %d) --> %d" \
				% (OCA[OCA_ARG_AC_ID], OCA[OCA_ARG_PC_ID][0], OCA[OCA_ARG_PC_ID][1], \
       				   unlock_count[OCA[OCA_ARG_AC_ID]])
                DCG.add_edge(lock_tag, unlock_tag, edge_attr)
	    else:
		unlock_count[OCA[OCA_ARG_AC_ID]] = unlock_count[OCA[OCA_ARG_AC_ID]]+1
		gr = DCG.get_edge(lock_tag,unlock_tag)   
		gr[0][DCG_EA_COUNT] = "UT%d --UNLOCK COUNT --> FILE(SysID: %s, Inode ID: %d) --> %d" \
				% (OCA[OCA_ARG_AC_ID], OCA[OCA_ARG_PC_ID][0], OCA[OCA_ARG_PC_ID][1], \
       				   unlock_count[OCA[OCA_ARG_AC_ID]])
        else:
            print "ERROR: File of OCA_FCNTL_LOCK is not a node in the DCG", OCA
    else:
        print "ERROR: locker of OCA_FCNTL_LOCK is not a node in the DCG", OCA
    """
    pass

# FIXME: These should probably just be attributes on the OCA_READ / OCA_WRITE
# events. There is no reason to change the type of the event because the file
# is locked or unlocked
#
def oca_lock_write(DCG, OCA):
    """
    The process is trying to write to the locked file using the
    sys_write system call. Here we just add a edge from the file 
    to the user thread

    print "oca_locked_write"

    lock_write_tag = (DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
    if DCG.has_node(lock_write_tag):
        # Create the tag for the locked file node. If the locked file node does
        # not already exist in the DCG then this is an error.
        #
	lock_id = OCA[OCA_ARG_PC_ID]
        lock_tag = (DCG_NT_FILE_LOCK, lock_id)

        if DCG.has_node(lock_tag):
            # Set the edge STRING attribute that describes the edge
            #
            edge_attr = create_DCG_edge_attr(DCG_ET_WRITE)
	    edge_attr[DCG_EA_STRING] = "UT%d -- Locked Write --> File (SysID: %s, Inode ID: %d)" % (OCA[OCA_ARG_AC_ID], OCA[OCA_ARG_PC_ID][0], OCA[OCA_ARG_PC_ID][1])
            DCG.add_edge(lock_write_tag, lock_tag, edge_attr)
        else:
            print "ERROR: File of OCA_LOCKED_WRITE is not a node in the DCG", OCA
    else:
        print "ERROR: locker of OCA_LOCKED_WRITE is not a node in the DCG", OCA
    """
    pass

def oca_lock_read(DCG, OCA):
    """
    The process is trying to read to the locked file using the
    sys_read system call. Here we just add a edge from the user  
    thread to the locked file

    print "oca_locked_read"

    lock_read_tag = (DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
    if DCG.has_node(lock_read_tag):
        # Create the tag for the locked file node. If the locked file node does
        # not already exist in the DCG then this is an error.
        #
	lock_id = OCA[OCA_ARG_PC_ID]
        lock_tag = (DCG_NT_FILE_LOCK, lock_id)

        if DCG.has_node(lock_tag):
            # Set the edge STRING attribute that describes the edge
            #
            edge_attr = create_DCG_edge_attr(DCG_ET_READ)
	    edge_attr[DCG_EA_STRING] = "File (SysID: %s, Inode ID: %d) --Locked Read--> UT%d" % (OCA[OCA_ARG_PC_ID][0], OCA[OCA_ARG_PC_ID][1], OCA[OCA_ARG_AC_ID])
            DCG.add_edge(lock_tag, lock_read_tag, edge_attr)
        else:
            print "ERROR: File of OCA_LOCKED_READ is not a node in the DCG", OCA
    else:
        print "ERROR: locker of OCA_LOCKED_READ is not a node in the DCG", OCA
    """
    pass

####################################################################
# Shared memory related definitions and operations
#
def oca_shm_attach(DCG, OCA):
    """
    A process attaches to an existing shared memory segment.

    Shared memory is a persistent communication channel that can be
    attached to by any number of processes. Once attached, the
    processes can use the segment to communicate arbitrary data.
    """
    # The process attaching to the shm segment must already be part 
    # of the DCG but the node representing the shm segment may or may 
    # not be
    #
    attacher_tag = (DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
    if DCG.has_node(attacher_tag):
        # Create the tag for the shm segment node. If the shm
	# segment node does not exist, create it.
        #

	seg_id = OCA[OCA_ARG_PC_ID]
        seg_tag = (DCG_PC_NODE, seg_id)
        if not DCG.has_node(seg_tag):
            DCG.add_node(seg_tag)
            Node_attributes[seg_tag]   = {}
            seg_attr                   = Node_attributes[seg_tag]
            seg_attr[DCG_NA_TYPE]      = DCG_NT_SHM
	    seg_attr[DCG_NA_MODE]      = OCA[OCA_ARG_MODE]
	    seg_attr[DCG_NA_STRING]    = OCA[OCA_ARG_PC_NAME]

        edge_attr = create_DCG_edge_attr(DCG_ET_SHMAT)
	edge_attr[DCG_EA_STRING] = "%s --Shmat--> %s" % (OCA[OCA_ARG_AC_NAME], OCA[OCA_ARG_PC_NAME])
        DCG.add_edge(attacher_tag, seg_tag, edge_attr)
    else:
	    print "ERROR: Attacher of OCA_SHM_ATTACH is not a node in the DCG", OCA

def oca_shm_detach(DCG, OCA):
    """
    A process detaches from an existing shared memory segment.

    Shared memory is a persistent communication channel that can be
    attached to by any number of processes. Once attached, the
    processes can use the segment to communicate arbitrary data.
    """
    # The process attaching to the shm segment and the shm segment
    # itself must already be part of the DCG
    #
    detacher_tag = (DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
    if DCG.has_node(detacher_tag):

	# Create an edge to show that our process detached from the
	# shm segment
	#
	seg_id = OCA[OCA_ARG_PC_ID]
        seg_tag = (DCG_PC_NODE, seg_id)
        if DCG.has_node(seg_tag):
            edge_attr = create_DCG_edge_attr(DCG_ET_SHMDT)
	    edge_attr[DCG_EA_STRING] = "%s --Shmdt--> %s" % (OCA[OCA_ARG_AC_NAME], OCA[OCA_ARG_PC_NAME])
            DCG.add_edge(detacher_tag, seg_tag, edge_attr)
	else:
            print "ERROR: Tried to detach from shm segment not in the DCG", OCA
	    raise AssertionError
    else:
        print "ERROR: Detacher of OCA_SHM_DETACH is not a node in the DCG", OCA
	raise AssertionError

def oca_socket_create(DCG, OCA):
    """
    This is a for a socket create
    """
    #print "socket create"
    process_tag = (DCG_AC_NODE, OCA[OCA_ARG_PID])
    if DCG.has_node(process_tag):
	    socket_tag = (DCG_PC_NODE, OCA[OCA_ARG_PC_ID])
	    #print "OCA pid : ",OCA[OCA_ARG_PID]
	    if not DCG.has_node(socket_tag):
	       #print "socket node to be created"	
	       if OCA[OCA_ARG_PID] is not 1:
	      	     DCG.add_node(socket_tag)
               Node_attributes[socket_tag] = {}
               socket_attr = Node_attributes[socket_tag]
               socket_attr[DCG_NA_TYPE]      = CT_2_NT(PC_SOCKET)
	       socket_attr[DCG_NA_STRING]    = OCA[OCA_ARG_PC_NAME]  
	       socket_attr[DCG_NA_UNIQUE_SOCKET_NAME] = ""
            edge_attr = create_DCG_edge_attr(DCG_ET_OPEN)
	    edge_attr[DCG_EA_STRING] = "UT%d --socket--> socket %s" % (OCA[OCA_ARG_PID], OCA[OCA_ARG_PC_NAME])
	    if OCA[OCA_ARG_PID] is not 1:
		    print "PC NAME : ", OCA[OCA_ARG_PC_NAME]
	            DCG.add_edge(process_tag, socket_tag, edge_attr)
    else:
            print "process not in the graph", OCA
	    return

def oca_socket_accept(DCG, OCA):
     """
     This is for a socket accept
     """
     #print "socket accept"
     server_tag = (DCG_AC_NODE, OCA[OCA_ARG_PID])
     if not DCG.has_node(server_tag):
     	new_node = create_DCG_node_tag(DCG_AC_NODE, OCA[OCA_ARG_PID])
     	new_node_attr = Node_attributes[new_node]
     	new_node_attr[DCG_NA_TYPE] = DCG_NT_UTHREAD
     	new_node_attr[DCG_NA_STRING] = OCA[OCA_ARG_AC_NAME] 
	new_node_attr[DCG_NA_GEN]    = OCA[OCA_ARG_GEN]
	new_node_attr[DCG_NA_EXEC]   = OCA[OCA_ARG_EXEC_NAME]
     	DCG.add_node(new_node)

     if DCG.has_node(server_tag):
	 
	  socket_tag = (DCG_PC_NODE, OCA[OCA_ARG_PC_ID])
	  if not DCG.has_node(socket_tag):             
             DCG.add_node(socket_tag)
             Node_attributes[socket_tag] = {}
             socket_attr = Node_attributes[socket_tag]
             socket_attr[DCG_NA_TYPE]      = CT_2_NT(PC_SOCKET)
	     socket_attr[DCG_NA_STRING]    = OCA[OCA_ARG_PC_NAME]  
	     socket_attr[DCG_NA_UNIQUE_SOCKET_NAME] = OCA[OCA_ARG_SOCK_NAME]
          edge_attr = create_DCG_edge_attr(DCG_ET_OPEN)
	  edge_attr[DCG_EA_STRING] = "UT%d --socket--> socket %s" % (OCA[OCA_ARG_PID], OCA[OCA_ARG_PC_NAME])
          DCG.add_edge(server_tag, socket_tag, edge_attr)

# the next set of code is for creating an edge between the two socket end points

          if DCG.has_node(socket_tag):
     		for node in DCG.nodes():
	     		attr = Node_attributes[node]
	     		if attr[DCG_NA_TYPE] == DCG_NT_SOCKET:
				if not attr[DCG_NA_UNIQUE_SOCKET_NAME]:
					return
				if attr[DCG_NA_UNIQUE_SOCKET_NAME] == OCA[OCA_ARG_SOCK_NAME] and not socket_tag == node:
					endPointConnectingEdge = get_edge_wtype(DCG, DCG_ET_WRITE, node, socket_tag)	
					if not endPointConnectingEdge:
						edge_attr  = create_DCG_edge_attr(DCG_ET_WRITE)
						edge_attr[DCG_EA_STRING] = "%s --Connects to --> %s " % (attr[DCG_NA_STRING], socket_attr[DCG_NA_STRING])
						DCG.add_edge(node,socket_tag, edge_attr)
	
     else:
          print "server not in the graph", OCA
	  return
	
def oca_socket_connect(DCG, OCA):
     """
     This is for a socket connect
     """
    # print "socket connect"
     client_tag = (DCG_AC_NODE, OCA[OCA_ARG_PID])	
     if not DCG.has_node(client_tag):
     	new_node = create_DCG_node_tag(DCG_AC_NODE, OCA[OCA_ARG_PID])
     	new_node_attr = Node_attributes[new_node]
     	new_node_attr[DCG_NA_TYPE] = DCG_NT_UTHREAD
     	new_node_attr[DCG_NA_STRING] = OCA[OCA_ARG_AC_NAME] 
	new_node_attr[DCG_NA_GEN]    = OCA[OCA_ARG_GEN]
	new_node_attr[DCG_NA_EXEC]   = OCA[OCA_ARG_EXEC_NAME]
     	DCG.add_node(new_node)
     

     if DCG.has_node(client_tag):

        socket_tag = (DCG_PC_NODE, OCA[OCA_ARG_PC_ID])
       	if not DCG.has_node(socket_tag):
       		DCG.add_node(socket_tag)
       		Node_attributes[socket_tag] = {}
       		socket_attr = Node_attributes[socket_tag]
       		socket_attr[DCG_NA_TYPE]      = CT_2_NT(PC_SOCKET)
   		socket_attr[DCG_NA_STRING]    = OCA[OCA_ARG_PC_NAME]
		socket_attr[DCG_NA_UNIQUE_SOCKET_NAME] = OCA[OCA_ARG_SOCK_NAME]
	
       	edge_attr = create_DCG_edge_attr(DCG_ET_OPEN)
	edge_attr[DCG_EA_STRING] = "UT%d --socket--> socket %s" % (OCA[OCA_ARG_PID], OCA[OCA_ARG_PC_NAME])
       	DCG.add_edge(client_tag, socket_tag, edge_attr)
		
# the next set of code is for creating an edge between the two socket end points
	
	if DCG.has_node(socket_tag):
     		for node in Node_attributes.keys():
	     		attr = Node_attributes[node]
	     		if attr[DCG_NA_TYPE] == DCG_NT_SOCKET:
				if not attr[DCG_NA_UNIQUE_SOCKET_NAME]:
					return
				if attr[DCG_NA_UNIQUE_SOCKET_NAME] == OCA[OCA_ARG_SOCK_NAME] and not socket_tag == node:
					endPointConnectingEdge = get_edge_wtype(DCG, DCG_ET_WRITE, socket_tag, node)	
					if not endPointConnectingEdge:
						edge_attr  = create_DCG_edge_attr(DCG_ET_WRITE)
						edge_attr[DCG_EA_STRING] = "%s --Connects to --> %s " % (socket_attr[DCG_NA_STRING], attr[DCG_NA_STRING])
						DCG.add_edge(socket_tag, node, edge_attr)
     else:
        print "ERROR: Client is not a node in the DCG", OCA

def oca_socket_send(DCG, OCA):
      """
      This is for a process sending a message through a socket
      """
      #print "socket send"
      sender_tag = (DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
      if DCG.has_node(sender_tag):
		pc_id   = OCA[OCA_ARG_PC_ID]
		pc_tag  = (DCG_PC_NODE, pc_id)
		if pc_id[0] =="devpts":
			return
		if DCG.has_node(pc_tag):
			# Set the edge STRING attribute that describes the edge
			#
			sender_str = Node_attributes[sender_tag][DCG_NA_STRING]
			pc_str     = Node_attributes[pc_tag][DCG_NA_STRING]
			send_edge = get_edge_wtype(DCG, DCG_ET_WRITE, sender_tag, pc_tag)
			if send_edge:
				edge_attr = send_edge[2]
				count = int(edge_attr[DCG_EA_COUNT]) + OCA[OCA_ARG_SIZE]
				edge_attr[DCG_EA_COUNT] = `count`
			else:
				edge_attr  = create_DCG_edge_attr(DCG_ET_WRITE)
				edge_attr[DCG_EA_FD] = `OCA[OCA_ARG_FD]`
				edge_attr[DCG_EA_COUNT] = `OCA[OCA_ARG_SIZE]`
				edge_attr[DCG_EA_STRING] = "%s --Sent--> %s on FD %d" % (sender_str, pc_str, OCA[OCA_ARG_FD])
				print "OCA Send Pid : ", OCA[OCA_ARG_PID]
				DCG.add_edge(sender_tag, pc_tag, edge_attr)
		else:
			print "ERROR: Socket End point of a type of 'socket send' is not a node in the DCG"#, OCA
#			raise AssertionError
      else:
		print "ERROR: Sender of a type of 'socket send' is not a node in the DCG"#, OCA
#		raise AssertionError

def oca_socket_recv(DCG, OCA):
	"""
	This is for a process receiving a message through a socket
	"""
	#print "Socket recv"
	receiver_tag = (DCG_AC_NODE, OCA[OCA_ARG_AC_ID])
	if DCG.has_node(receiver_tag):
		pc_id   = OCA[OCA_ARG_PC_ID]
		pc_tag  = (DCG_PC_NODE, pc_id)
		if DCG.has_node(pc_tag):
			# Set the edge STRING attribute that describes the edge
			#
			receiver_str = Node_attributes[receiver_tag][DCG_NA_STRING]
			pc_str     = Node_attributes[pc_tag][DCG_NA_STRING]
			receiver_edge  = get_edge_wtype(DCG, DCG_ET_READ, receiver_tag, pc_tag)
			if receiver_edge:
				edge_attr = receiver_edge[2]
				count = int(edge_attr[DCG_EA_COUNT]) + OCA[OCA_ARG_SIZE]
				edge_attr[DCG_EA_COUNT] = `count`
			else:
				edge_attr  = create_DCG_edge_attr(DCG_ET_READ)
				edge_attr[DCG_EA_FD] = `OCA[OCA_ARG_FD]`
				edge_attr[DCG_EA_COUNT] = `OCA[OCA_ARG_SIZE]`
				edge_attr[DCG_EA_STRING] = "%s --Received--> %s on FD %d" % (receiver_str, pc_str, OCA[OCA_ARG_FD])
				print "OCA Recv Pid : ", OCA[OCA_ARG_PID]
				DCG.add_edge(receiver_tag, pc_tag, edge_attr)
		else:
			print "ERROR: Socket End Point of a type of 'socket recv' is not a node in the DCG"#, OCA
#			raise AssertionError
	else:
		print "ERROR: Receiver of a type of 'socket recv' is not a node in the DCG"#, OCA
#		raise AssertionError


####################################################################
#
# This dictionary represents the set of valid observed action types
# and the corresponding functions to call which will modify the graph
# to represent the implication of each observed action.
#
OCA_to_Graph_Action_Map = {
	OCA_ROOT_THREAD      : oca_root_thread,
	OCA_FORK             : oca_fork,
	OCA_ROOT_FD          : oca_root_fd,
	OCA_SIGNAL_SEND      : oca_signal_send,
	OCA_PIPE_CREATE      : oca_pipe,
	OCA_OPEN	     : oca_open,
	OCA_CLOSE	     : oca_close,
	OCA_READ	     : oca_read,
	OCA_WRITE	     : oca_write,
#	OCA_SHM_ATTACH       : oca_shm_attach,
#	OCA_SHM_DETACH       : oca_shm_detach,
#	OCA_PTRACE_ATTACH    : oca_ptrace_attach,
#	OCA_PTRACE_DETACH    : oca_ptrace_detach,
	OCA_EXEC             : oca_exec,
	OCA_SOCKET_CONNECT   : oca_socket_connect,
	OCA_SOCKET_ACCEPT    : oca_socket_accept,
	OCA_SOCKET_CREATE    : oca_socket_create,
	OCA_SOCKET_SEND_TO   : oca_socket_send,
	OCA_SOCKET_RECV_FROM : oca_socket_recv,
	OCA_SOCKET_SEND_MSG  : oca_socket_send,
	OCA_SOCKET_RECV_MSG  : oca_socket_recv
	#OCA_FCNTL_LOCK       : oca_fctl_lock,
	#OCA_FCNTL_UNLOCK     : oca_fctl_unlock,

	# FIXME: These should probably just be attributes on the OCA_READ / OCA_WRITE
	# events. There is no reason to change the type of the event because the file
	# is locked or unlocked
	#
	#OCA_LOCKED_READ : oca_lock_read,
	#OCA_LOCKED_WRITE: oca_lock_write
}

def add_OCA_to_DCG(DCG, OCA):
    """
    This routine takes the action on the graph G specified for the
    observation O. We assume the computation observation records are a
    dictionary whose elements define the type of observation and the
    data required to interpret how that observation affects the derived
    graph representation of the computation structure. This structure is
    what we are "discovering". 
    """
    if OCA.has_key(OCA_TYPE):
        if OCA_to_Graph_Action_Map.has_key(OCA[OCA_TYPE]):
            OCA_to_Graph_Action_Map[OCA[OCA_TYPE]](DCG, OCA)
        else:
            print "ERROR: Uknown OCA type", OCA
    else:
        print "ERROR: OCA missing Type key", OCA
        
# Rename the name displayed for a node in DCG with the given OCA_pid
# to new_name
#
def rename_uthread_node(DCG, OCA_pid, new_name,isDSUI):
    rtag = (DCG_AC_NODE, OCA_pid)
    if isDSUI == "True":
	    if DCG.has_node(rtag):
		    DCG.delete_node(rtag)
    else:
    	if DCG.has_node(rtag):
        	if Node_attributes[rtag].has_key(DCG_NA_STRING):
           	 Node_attributes[rtag][DCG_NA_STRING] = new_name
		else:
        	    print "Tried to rename on node with no name attribute: ", rtag
    	else:
        	print "Tried to rename a node that's not in the graph: ", rtag

######################################################################
# Graph drawing routines and methods
#
# We are also establishing conventions for how to present various
# kinds of relations and various types of information in visual form.
#
# The DCG_Drawing class embodies a list of DCG element equivalence
# classes to draw or not draw, as the full graph is liely to be too
# complex to use as the only representation. The set of variables in
# this class should correspond to the set of node and edge type values
# defined for the DCG. Beyond that, it is possible to imagine
# variables representing groups of classes as well. The methods of
# this class would support manipulating the configuration of the
# drawing as easy as possible, given that it is a complex problem.
#
# Each equivalence class has a flag indicating if it should be
# displayed or not, a list of DCG elements that are members of that
# equivalence class, and the set of parameters contolling how members
# of the class appear when drawn. The drawing parameters are generally
# passed through the NX code level into the matplotlib drawing
# routines. The matplotlib routine is named "scatter". Relevant parts
# of the manual page for scatter have been copied into these comments.
#
DCG_DRAW_FLAG     = "Draw Flag"
DCG_DRAW_LIST     = "Draw List"
DCG_DRAW_PARAMS   = "Draw Params"

# The Node Size Parameter It is in units of points^2.  It is either a
# scalar or an array of the same length as DCG_DRAW_LIST to give
# different sizes for each node.
#
DCG_DP_NODE_SIZE  = "Node Size"
 
# The value is a color and can be a single color format string, or a
# list of color specifications of length N. Standard X color names
# seem to be acceptable.
#
DCG_DP_NODE_COLOR = "Node Color"

# The ALPHA value is a floating point number [0.0,1.0] which produces
# complete transparence on the low end, and compelte opacity on the
# high end.
#
DCG_DP_NODE_ALPHA = "Node Aplha"

# Node shape is described as a "marker" parameter to the matplotlib
# scatter routine. It can take a number of different forms. The most
# convenient are:
#
#     's' : square
#     'o' : circle
#     '^' : triangle up
#     '>' : triangle right
#     'v' : triangle down
#     '<' : triangle left
#     'd' : diamond
#     'p' : pentagram
#     'h' : hexagon
#     '8' : octagon
#     '+' : plus
#     'x' : cross
# 
# However, if you wish to describe a custome shape you can use a tuple
# (numsides, style, angle), which will create a custom, regular
# symbol.
# 
#     numsides is the number of sides
# 
#     style is the style of the regular symbol:
#       0 : a regular polygon
#       1 : a star-like symbol
#       2 : an asterisk
# 
#     angle is the angle of rotation of the symbol
# 
# Finally, marker can be (verts, 0), verts is a sequence of (x,y)
# vertices for a custom scatter symbol.  Alternatively, use the
# kwarg combination marker=None,verts=verts.
# 
DCG_DP_NODE_SHAPE = "Node Shape"

UTHREAD_NODE_DRAW_PARAMS    = {DCG_DP_NODE_SIZE  : 700,  DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 'o', DCG_DP_NODE_COLOR : "red"}
PIPE_NODE_DRAW_PARAMS       = {DCG_DP_NODE_SIZE  : 700,  DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 's', DCG_DP_NODE_COLOR : "red"}
NAMED_PIPE_NODE_DRAW_PARAMS = {DCG_DP_NODE_SIZE  : 1100, DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 's', DCG_DP_NODE_COLOR : "red"}
SEM_NODE_DRAW_PARAMS        = {DCG_DP_NODE_SIZE  : 700,  DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 'd', DCG_DP_NODE_COLOR : "red"}
SHM_NODE_DRAW_PARAMS        = {DCG_DP_NODE_SIZE  : 700,  DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : '^', DCG_DP_NODE_COLOR : "red"}
FILE_LOCK_NODE_DRAW_PARAMS  = {DCG_DP_NODE_SIZE  : 700,  DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 'p', DCG_DP_NODE_COLOR : "red"}
SOCKET_NODE_DRAW_PARAMS     = {DCG_DP_NODE_SIZE  : 700,  DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 'h', DCG_DP_NODE_COLOR : "red"}
FUTEX_NODE_DRAW_PARAMS      = {DCG_DP_NODE_SIZE  : 700,  DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 'd', DCG_DP_NODE_COLOR : "orange"}
PTRACE_NODE_DRAW_PARAMS     = {DCG_DP_NODE_SIZE  : 700,  DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 'v', DCG_DP_NODE_COLOR : "blue"}
FILE_NODE_DRAW_PARAMS       = {DCG_DP_NODE_SIZE  : 400,  DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 'v', DCG_DP_NODE_COLOR : "brown"}
PSEUDOT_NODE_DRAW_PARAMS    = {DCG_DP_NODE_SIZE  : 400,  DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 'v', DCG_DP_NODE_COLOR : "purple"}
                                                                                                                                   
KTHREAD_NODE_DRAW_PARAMS    = {DCG_DP_NODE_SIZE  : 700, DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 'o', DCG_DP_NODE_COLOR : "yellow"}
HARDIRQ_NODE_DRAW_PARAMS    = {DCG_DP_NODE_SIZE  : 700, DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : '^', DCG_DP_NODE_COLOR : "yellow"}
SOFTIRQ_NODE_DRAW_PARAMS    = {DCG_DP_NODE_SIZE  : 700, DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 's', DCG_DP_NODE_COLOR : "yellow"}
MUTEX_NODE_DRAW_PARAMS      = {DCG_DP_NODE_SIZE  : 700, DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 'd', DCG_DP_NODE_COLOR : "yellow"}
RWLOCK_NODE_DRAW_PARAMS     = {DCG_DP_NODE_SIZE  : 700, DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 'd', DCG_DP_NODE_COLOR : "yellow"}
SEQLOCK_NODE_DRAW_PARAMS    = {DCG_DP_NODE_SIZE  : 700, DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 'd', DCG_DP_NODE_COLOR : "yellow"}
MEMORY_NODE_DRAW_PARAMS     = {DCG_DP_NODE_SIZE  : 700, DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : 'h', DCG_DP_NODE_COLOR : "yellow"}
MODULE_NODE_DRAW_PARAMS     = {DCG_DP_NODE_SIZE  : 700, DCG_DP_NODE_ALPHA : 1.0, DCG_DP_NODE_SHAPE : '8', DCG_DP_NODE_COLOR : "yellow"}
                                                                                                                                   
#################################################
# Edges
#################################################
#
# Edge display parameters. The color parameter can be any of the
# standard color specifications as described for nodes. Generally the
# color names will be the easiest, I think. The alpha value varies
# between 0.0 and 1.0, varying between full transparency and full
# opacity, respectively.
#
# The line style can be any of:
#        linestyle: ['solid' | 'dashed', 'dashdot', 'dotted' |  (offset, on-off-dash-seq) ]
#
DCG_DP_EDGE_WIDTH = "Edge Width"
DCG_DP_EDGE_COLOR = "Edge Color"
DCG_DP_EDGE_STYLE = "Edge Style"
DCG_DP_EDGE_ALPHA = "Edge Aplha"

FORK_EDGE_DRAW_PARAMS       = {DCG_DP_EDGE_ALPHA : 1.0, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "dotted", DCG_DP_EDGE_COLOR : "red" }
                            
PARENT_EDGE_DRAW_PARAMS     = {DCG_DP_EDGE_ALPHA : 1.0, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "dotted", DCG_DP_EDGE_COLOR : "blue" }
CHILD_EDGE_DRAW_PARAMS      = {DCG_DP_EDGE_ALPHA : 1.0, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "dotted", DCG_DP_EDGE_COLOR : "green" }
DESCENDANT_EDGE_DRAW_PARAMS = {DCG_DP_EDGE_ALPHA : 1.0, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "dotted", DCG_DP_EDGE_COLOR : "black" }
ANCESTOR_EDGE_DRAW_PARAMS   = {DCG_DP_EDGE_ALPHA : 1.0, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "dotted", DCG_DP_EDGE_COLOR : "orange" }
                            
SIGNAL_EDGE_DRAW_PARAMS     = {DCG_DP_EDGE_ALPHA : 1.0, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "dashed", DCG_DP_EDGE_COLOR : "blue" }
IN_FD_EDGE_DRAW_PARAMS      = {DCG_DP_EDGE_ALPHA : 1.0, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "dashed", DCG_DP_EDGE_COLOR : "green" }
IN_SHM_EDGE_DRAW_PARAMS     = {DCG_DP_EDGE_ALPHA : 1.0, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "dashed", DCG_DP_EDGE_COLOR : "purple" }
OPEN_EDGE_DRAW_PARAMS       = {DCG_DP_EDGE_ALPHA : 1.0, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "dotted", DCG_DP_EDGE_COLOR : "green" }
CLOSE_EDGE_DRAW_PARAMS      = {DCG_DP_EDGE_ALPHA : 0.5, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "solid",  DCG_DP_EDGE_COLOR : "green" }
READ_EDGE_DRAW_PARAMS       = {DCG_DP_EDGE_ALPHA : 1.0, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "dashed", DCG_DP_EDGE_COLOR : "orange" }
WRITE_EDGE_DRAW_PARAMS      = {DCG_DP_EDGE_ALPHA : 1.0, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "dashed", DCG_DP_EDGE_COLOR : "orange" }
LOCK_EDGE_DRAW_PARAMS       = {DCG_DP_EDGE_ALPHA : 1.0, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "dotted", DCG_DP_EDGE_COLOR : "green" }
UNLOCK_EDGE_DRAW_PARAMS     = {DCG_DP_EDGE_ALPHA : 0.5, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "solid",  DCG_DP_EDGE_COLOR : "green" }
USE_EDGE_DRAW_PARAMS        = {DCG_DP_EDGE_ALPHA : 1.0, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "dashed", DCG_DP_EDGE_COLOR : "brown" }

MASTER_EDGE_DRAW_PARAMS     = {DCG_DP_EDGE_ALPHA : 1.0, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "solid", DCG_DP_EDGE_COLOR : "orange" }
SLAVE_EDGE_DRAW_PARAMS      = {DCG_DP_EDGE_ALPHA : 1.0, DCG_DP_EDGE_WIDTH  : 2, DCG_DP_EDGE_STYLE : "solid", DCG_DP_EDGE_COLOR : "green" }

#################################################
# Labels
#################################################

DCG_DP_LABEL_FONT_FAMILY = "LF Family"
DCG_DP_LABEL_FONT_WEIGHT = "LF Weight"
DCG_DP_LABEL_FONT_SIZE   = "LF Size"
DCG_DP_LABEL_FONT_COLOR  = "LF Color"
DCG_DP_LABEL_ALPHA       = "Label Alpha"

DCG_NODE_LABEL_PARAMS = {
    DCG_DP_LABEL_FONT_FAMILY : "sans-serif",
    DCG_DP_LABEL_FONT_WEIGHT : "normal",
    DCG_DP_LABEL_FONT_SIZE   : 12,
    DCG_DP_LABEL_FONT_COLOR  : "black",
    DCG_DP_LABEL_ALPHA       : 1.0
}

###############################################################################
###############################################################################

class DCG_Drawing:
    """
    This class defines the methods for drawing DCG graphs, as well as
    the options controlling how they look. The set of components and
    relations represented by the DCG are likely to become quite
    complex, and so digrams of the entire DCG are likely to be
    comfusing. Instead of drawing the whole graph at once, it seems
    likely that users will create diagrams of different components of
    the DCG. In support of that goal, this class views the DCG as a
    set of equivalence classes related to various ways threads
    interact with each other. Display of each of these equivalence
    classes can be controlled individually.
    """
    def __init__(self, init_value=True, x_dim_in=8, y_dim_in=8, title=None):
        # Figure dimensions and title
        self.x_dim = x_dim_in
        self.y_dim = y_dim_in
        self.title = "Discovered Computation Graph"
        self.output_file = "full_dcg.png"
        self.output_dpi = 75

        # Flags controlling the drawing of various equivalence classes
        # for nodes in the DCG, For now let these be either True or
        # False flags and a list for accumulating instances of them in
        # the graph being drawn. As our conventions for drawing DCGs
        # progress, we may wish to the dictionary to provide a set of
        # specifications for parameters affecting how nodes are
        # displayed: color, shape, size, and perhaps others.
        #
        # The first set is the nodes related to user-level API components
        #
        self.uthread_nodes    = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : UTHREAD_NODE_DRAW_PARAMS    }
        self.sv_sem_nodes     = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : SEM_NODE_DRAW_PARAMS        }
        self.sv_shm_nodes     = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : SHM_NODE_DRAW_PARAMS        }
        self.pipe_nodes       = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : PIPE_NODE_DRAW_PARAMS       }
        self.named_pipe_nodes = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : NAMED_PIPE_NODE_DRAW_PARAMS }
        self.file_locks_nodes = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : FILE_LOCK_NODE_DRAW_PARAMS  }
        self.sockets_nodes    = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : SOCKET_NODE_DRAW_PARAMS     }
        self.futex_nodes      = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : FUTEX_NODE_DRAW_PARAMS      }
        self.ptrace_nodes     = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : PTRACE_NODE_DRAW_PARAMS     }
        self.file_nodes       = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : FILE_NODE_DRAW_PARAMS       }
        self.pseudot_nodes    = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : PSEUDOT_NODE_DRAW_PARAMS    }

        # This set are system level computation components that affect
        # computation behavior, but which are not part of the
        # application API. In other words, they are components that
        # are not visible to the developer writing a program.
        #
        self.kthread_nodes = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : KTHREAD_NODE_DRAW_PARAMS }
        self.hardIRQ_nodes = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : HARDIRQ_NODE_DRAW_PARAMS }
        self.softIRQ_nodes = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : SOFTIRQ_NODE_DRAW_PARAMS }
        self.mutex_nodes   = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : MUTEX_NODE_DRAW_PARAMS   }
        self.RWlock_nodes  = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : RWLOCK_NODE_DRAW_PARAMS  }
        self.SEQlock_nodes = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : SEQLOCK_NODE_DRAW_PARAMS }
        self.memory_nodes  = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : MEMORY_NODE_DRAW_PARAMS  }
        self.module_nodes  = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : MODULE_NODE_DRAW_PARAMS  }

        # Flags controlling the drawing of various equivalence classes
        # for edges in the DCG
        #
        self.fork_edges   = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : FORK_EDGE_DRAW_PARAMS   }
        self.signal_edges = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : SIGNAL_EDGE_DRAW_PARAMS }
        self.in_fd_edges  = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : IN_FD_EDGE_DRAW_PARAMS  }
        self.in_shm_edges = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : IN_SHM_EDGE_DRAW_PARAMS }
        self.open_edges   = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : OPEN_EDGE_DRAW_PARAMS   }
        self.close_edges  = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : CLOSE_EDGE_DRAW_PARAMS  }
        self.read_edges   = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : READ_EDGE_DRAW_PARAMS   }
        self.write_edges  = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : WRITE_EDGE_DRAW_PARAMS  }
        self.lock_edges   = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : LOCK_EDGE_DRAW_PARAMS   }
        self.unlock_edges = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : UNLOCK_EDGE_DRAW_PARAMS }
        self.use_edges    = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : USE_EDGE_DRAW_PARAMS    }
        self.master_edges = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : MASTER_EDGE_DRAW_PARAMS }
        self.slave_edges  = {DCG_DRAW_FLAG : init_value, DCG_DRAW_LIST : [], DCG_DRAW_PARAMS : SLAVE_EDGE_DRAW_PARAMS  }

        self.drawing_options_format_string = \
"""
DCG Drawing Options
-------------------
Figure Size (%s, %s)

Nodes representing User-level threads 
and objects used by them
--------------------------------
uthread_nodes    = %s
sv_sem_nodes     = %s
sv_shm_nodes     = %s
pipe_nodes       = %s
named_pipe_nodes = %s
file_locks_nodes = %s
sockets_nodes    = %s
futex_nodes      = %s
ptrace_nodes     = %s

Nodes representing Kernel threads
and objects residing only in the Kernel
---------------------------------------
kthread_nodes = %s
hardIRQ_nodes = %s
softIRQ_nodes = %s
mutex_nodes   = %s
RWlock_nodes  = %s
SEQlock_nodes = %s
memory_nodes  = %s
module_nodes  = %s

Edges representing actions by threads
--------------------------------------
fork_edges   = %s
signal_edges = %s
open_edges   = %s
close_edges  = %s
read_edges   = %s
write_edges  = %s
lock_edges   = %s
unlock_edges = %s
use_edges    = %s
master_edges = %s
slave_edges  = %s
"""
        # This list is used self.construct_lists to accumulate a list
        # of nodes in each equivalence class. THis is used by the
        # self.draw_graph_as_specified routine to draw only the
        # components desired.
        #
        self.drawing_lists_dict = {
            DCG_NT_UTHREAD    : self.uthread_nodes[DCG_DRAW_LIST],    
            DCG_NT_SHM        : self.sv_shm_nodes[DCG_DRAW_LIST],     
            DCG_NT_PIPE       : self.pipe_nodes[DCG_DRAW_LIST],       
            DCG_NT_NAMED_PIPE : self.named_pipe_nodes[DCG_DRAW_LIST], 
            DCG_NT_SOCKET     : self.sockets_nodes[DCG_DRAW_LIST],    
            DCG_NT_PTRACE     : self.ptrace_nodes[DCG_DRAW_LIST],
	    DCG_NT_FILE	      : self.file_nodes[DCG_DRAW_LIST],
	    DCG_NT_PSEUDOT    : self.pseudot_nodes[DCG_DRAW_LIST],
		#DCG_NT_SEM        : self.sv_sem_nodes[DCG_DRAW_LIST],     
		#DCG_NT_FILE_LOCK  	: self.file_locks_nodes[DCG_DRAW_LIST], 
		#DCG_NT_FUTEX      : self.futex_nodes[DCG_DRAW_LIST],
		#DCG_NT_KTHREAD    : self.kthread_nodes[DCG_DRAW_LIST],    
		#DCG_NT_HARDIRQ    : self.hardIRQ_nodes[DCG_DRAW_LIST],    
		#DCG_NT_SOFTIRQ    : self.softIRQ_nodes[DCG_DRAW_LIST],    
		#DCG_NT_MUTEX      : self.mutex_nodes[DCG_DRAW_LIST],      
		#DCG_NT_RWLOCK     : self.RWlock_nodes[DCG_DRAW_LIST],     
		#DCG_NT_SEQLOCK    : self.SEQlock_nodes[DCG_DRAW_LIST],    
		#DCG_NT_MEMORY     : self.memory_nodes[DCG_DRAW_LIST],     
		#DCG_NT_MODULE     : self.module_nodes[DCG_DRAW_LIST],     
            DCG_ET_FORK       : self.fork_edges[DCG_DRAW_LIST],       
            DCG_ET_SIGNAL     : self.signal_edges[DCG_DRAW_LIST],     
            DCG_ET_IN_FD      : self.in_fd_edges[DCG_DRAW_LIST],     
            DCG_ET_IN_SHM     : self.in_shm_edges[DCG_DRAW_LIST],     
            DCG_ET_OPEN       : self.open_edges[DCG_DRAW_LIST],       
            DCG_ET_CLOSE      : self.close_edges[DCG_DRAW_LIST],      
            DCG_ET_READ       : self.read_edges[DCG_DRAW_LIST],       
            DCG_ET_WRITE      : self.write_edges[DCG_DRAW_LIST],      
            DCG_ET_LOCK       : self.lock_edges[DCG_DRAW_LIST],       
            DCG_ET_UNLOCK     : self.unlock_edges[DCG_DRAW_LIST],     
            DCG_ET_USE        : self.use_edges[DCG_DRAW_LIST],
            DCG_ET_MASTER     : self.master_edges[DCG_DRAW_LIST],
            DCG_ET_SLAVE      : self.slave_edges[DCG_DRAW_LIST]
            }

        # These are the lists of equivalence classes for nodes and edges
        # which can be marked as desired for drawing or not.
        #
        self.nodes_equivalence_classes_list = [
            self.uthread_nodes,    
            self.sv_sem_nodes,     
            self.sv_shm_nodes,     
            self.pipe_nodes,       
            self.named_pipe_nodes, 
            self.file_locks_nodes, 
            self.sockets_nodes,    
            self.futex_nodes,    
            self.ptrace_nodes,
            self.kthread_nodes,    
            self.hardIRQ_nodes,    
            self.softIRQ_nodes,    
            self.mutex_nodes,      
            self.RWlock_nodes,     
            self.SEQlock_nodes,    
            self.memory_nodes,     
            self.module_nodes,     
            ]

        self.edges_equivalence_classes_list = [
            self.fork_edges,       
            self.signal_edges,     
            self.open_edges,       
            self.close_edges,      
            self.read_edges,       
            self.write_edges,      
            self.lock_edges,       
            self.unlock_edges,     
            self.use_edges,
            self.master_edges,
            self.slave_edges
            ]

#########################################################################

    def construct_lists(self, DCG, input_node_attributes):
        """
        This routine loops through the nodes and edges of a DCG and 
        adds them to the equivalence class lists. In this way we can choose
        to draw any set or combinations of sets of nodes and edges that 
        we want. The theory being that the graph as a whole will often
        be too complex to be menaingful when drawn as a whole.
        """
        for node in DCG.nodes():
            node_type = input_node_attributes[node][DCG_NA_TYPE]
            self.drawing_lists_dict[node_type].append(node)

        for edge in DCG.edges():
            (from_node, to_node, edge_attr) = edge
            edge_type = edge_attr[DCG_EA_TYPE]
            self.drawing_lists_dict[edge_type].append(edge)


#########################################################################

    def draw_graph_as_specified(self, DCG, pos, node_attributes): 
        """
        Draw the nodes in the graph, as specified by the enabling of
        various equivalence classes in the options structure. Also,
        the display of each component follows the conventions
        specified in the set of parameters assoiciated with each
        equivalence class.
        """
        # Begin by creating a figure within which to do the drawing.  Turn
        # off the axis ticks.
        #
        PL.figure(figsize=(self.x_dim, self.y_dim))
        PL.xticks([])
        PL.yticks([])
        font = {'fontname'   : 'Helvetica',
                'color'      : 'k',
                'fontweight' : 'bold',
                'fontsize'   : 14}
        PL.title(self.title, font)

        # Draw the nodes in each equivalence class as specified
        # We handle drawing the shape of the node separately from 
        # the labels for each node. 
        #
        # For each equivalence class we see if we are supposed to draw
        # nodes within it, and if it is not empty. IF so, we draw the
        # node shapes, and then generate the lables and draw them.
        #
        for ec in self.nodes_equivalence_classes_list:
            if ec[DCG_DRAW_FLAG] and len(ec[DCG_DRAW_LIST]) > 0:
                # Draw the nodes, and then draw the labels after
                # accumulating the list of labels
                #
                NX.draw_networkx_nodes(DCG, pos, 
                                           nodelist   = ec[DCG_DRAW_LIST], 
                                           node_size  = ec[DCG_DRAW_PARAMS][DCG_DP_NODE_SIZE],  
                                           node_color = ec[DCG_DRAW_PARAMS][DCG_DP_NODE_COLOR], 
                                           node_shape = ec[DCG_DRAW_PARAMS][DCG_DP_NODE_SHAPE], 
                                           alpha      = ec[DCG_DRAW_PARAMS][DCG_DP_NODE_ALPHA])
                # Now make a dictionary indexed by the node keys, with
                # the values being the string representation of the
                # node, which will be the labels in the graph.
                #
                node_label_dict = {}
                for node in ec[DCG_DRAW_LIST]:
                    node_attr = node_attributes[node]
                    node_label_dict[node] = node_attr[DCG_NA_STRING]
                
                NX.draw_networkx_labels(DCG, pos, 
                                        labels      = node_label_dict, 
                                        font_family = DCG_NODE_LABEL_PARAMS[DCG_DP_LABEL_FONT_FAMILY],
                                        font_weight = DCG_NODE_LABEL_PARAMS[DCG_DP_LABEL_FONT_WEIGHT],
                                        font_size   = DCG_NODE_LABEL_PARAMS[DCG_DP_LABEL_FONT_SIZE  ],
                                        font_color  = DCG_NODE_LABEL_PARAMS[DCG_DP_LABEL_FONT_COLOR ],
                                        alpha       = DCG_NODE_LABEL_PARAMS[DCG_DP_LABEL_ALPHA      ])

        # Now draw the graph edges. Each of the equivalence
        # classes can follow different display conventions to
        # distinguish them.
        #
        for ec in self.edges_equivalence_classes_list:
            if ec[DCG_DRAW_FLAG] and len(ec[DCG_DRAW_LIST]) > 0:
                NX.draw_networkx_edges(DCG, pos, 
                                           edgelist   = ec[DCG_DRAW_LIST], 
                                           style      = ec[DCG_DRAW_PARAMS][DCG_DP_EDGE_STYLE], 
                                           edge_color = ec[DCG_DRAW_PARAMS][DCG_DP_EDGE_COLOR], 
                                           width      = ec[DCG_DRAW_PARAMS][DCG_DP_EDGE_WIDTH], 
                                           alpha      = ec[DCG_DRAW_PARAMS][DCG_DP_EDGE_ALPHA])
                        
        # Now, after drawing everything, we should save the figure we
        # created.
        #
        PL.savefig(self.output_file, dpi=self.output_dpi)
                        
#########################################################################

    def __str__(self):
        return self.drawing_options_format_string %  \
            (self.x_dim, self.y_dim, 
             self.uthread_nodes[DCG_DRAW_FLAG],
             self.sv_sem_nodes[DCG_DRAW_FLAG],
             self.sv_shm_nodes[DCG_DRAW_FLAG],
             self.pipe_nodes[DCG_DRAW_FLAG],
             self.named_pipe_nodes[DCG_DRAW_FLAG],
             self.file_locks_nodes[DCG_DRAW_FLAG],
             self.sockets_nodes[DCG_DRAW_FLAG],
             self.futex_nodes[DCG_DRAW_FLAG],
	     self.ptrace_nodes[DCG_DRAW_FLAG],
             self.kthread_nodes[DCG_DRAW_FLAG],
             self.hardIRQ_nodes[DCG_DRAW_FLAG],
             self.softIRQ_nodes[DCG_DRAW_FLAG],
             self.mutex_nodes[DCG_DRAW_FLAG],
             self.RWlock_nodes[DCG_DRAW_FLAG],
             self.SEQlock_nodes[DCG_DRAW_FLAG],
             self.memory_nodes[DCG_DRAW_FLAG],
             self.module_nodes[DCG_DRAW_FLAG],
             self.fork_edges[DCG_DRAW_FLAG],
             self.signal_edges[DCG_DRAW_FLAG],
             self.open_edges[DCG_DRAW_FLAG],
             self.close_edges[DCG_DRAW_FLAG],
             self.read_edges[DCG_DRAW_FLAG],
             self.write_edges[DCG_DRAW_FLAG],
             self.lock_edges[DCG_DRAW_FLAG],
             self.unlock_edges[DCG_DRAW_FLAG],
             self.use_edges[DCG_DRAW_FLAG],
	     self.master_edges[DCG_DRAW_FLAG],
	     self.slave_edges[DCG_DRAW_FLAG]) 
