#!/usr/bin/env python


import operator
from datastreams.postprocess import filtering, entities
from datastreams.postprocess.dcg import *
from discovery.oca_definitions import *
import networkx as NX

"""
This is the original nx_filter. It's designed to process a stream of
OCA event types and create a network x graph of the computation
represented by this stream
"""

class discovery_graph(filtering.Filter):
	expected_parameters = {
                "x_dim_in" : {
                        "types" : "integer",
                        "doc" : "X dimension for nx graph",
                        "default" : 12,
                },
                "y_dim_in" : {
                        "types" : "integer",
                        "doc" : "Y dimension for nx graph",
                        "default" : 6,
                },
		"uthread_nodes" : {
			"types" : "boolean",
			"doc" : "Whether to display uthread_nodes",
			"default" : True
		},
		"named_pipe_nodes" : {
			"types" : "boolean",
			"doc" : "Whether to display named_pipe_nodes",
			"default" : True
		},
		"file_nodes" : {
			"types" : "boolean",
			"doc" : "Whether to display named_pipe_nodes",
			"default" : False
		},
		"pseudot_nodes" : {
			"types" : "boolean",
			"doc" : "Whether to display named_pipe_nodes",
			"default" : False
		},
		"fork_edges" : {
			"types" : "boolean",
			"doc" : "Whether to display fork_edges",
			"default" : True
		},
		"signal_edges" : {
			"types" : "boolean",
			"doc" : "Whether to display signal_edges",
			"default" : True
		},
		"open_edges" : {
			"types" : "boolean",
			"doc" : "Whether to display open_edges",
			"default" : True
		},
		"close_edges" : {
			"types" : "boolean",
			"doc" : "Whether to display close_edges",
			"default" : True
		},
		"read_edges" : {
			"types" : "boolean",
			"doc" : "Whether to display read_edges",
			"default" : False
		},
		"write_edges" : {
			"types" : "boolean",
			"doc" : "Whether to display write_edges",
			"default" : False
		},
		"master_edges" : {
			"types" : "boolean",
			"doc" : "Whether to display write_edges",
			"default" : True
		},
		"slave_edges" : {
			"types" : "boolean",
			"doc" : "Whether to display write_edges",
			"default" : True
		},
		"layout" : {
			"types" : "string",
			"doc" : "Specify layout of DC graph",
			"constraints" : ["twopi", "fdp", "circo", "neato", "dot"],
			"default" : "dot"
		},
		"consume" : {
			"types" : "boolean",
			"doc" : "Whether to delete matching entities after processing",
			"default" : False
		},
		"print_level" : {
			"types" : "integer",
			"doc" : "An option to specify the graph print out that is output " \
				"to the specified outfile. 0 means no print out. 1 is the " \
				"standard level. 2 and higher print more verbose information.",
			"default" : 0
		},
		"outfile" : {
			"types" : "string",
			"doc" : "Output file the text form of the graph will print to",
			"default" : "-"
		},

        }

        def initialize(self):
                
                self.drawing_options = DCG_Drawing(True, self.params["x_dim_in"], self.params["y_dim_in"])

                self.drawing_options.uthread_nodes[DCG_DRAW_FLAG]    = self.params["uthread_nodes"]
                self.drawing_options.named_pipe_nodes[DCG_DRAW_FLAG] = self.params["named_pipe_nodes"]
                self.drawing_options.file_nodes[DCG_DRAW_FLAG]       = self.params["file_nodes"]
                self.drawing_options.pseudot_nodes[DCG_DRAW_FLAG]    = self.params["pseudot_nodes"]
                self.drawing_options.fork_edges[DCG_DRAW_FLAG]       = self.params["fork_edges"]
                self.drawing_options.signal_edges[DCG_DRAW_FLAG]     = self.params["signal_edges"]
                self.drawing_options.open_edges[DCG_DRAW_FLAG]       = self.params["open_edges"]
                self.drawing_options.close_edges[DCG_DRAW_FLAG]      = self.params["close_edges"]
                self.drawing_options.read_edges[DCG_DRAW_FLAG]       = self.params["read_edges"]
                self.drawing_options.write_edges[DCG_DRAW_FLAG]      = self.params["write_edges"]
                self.drawing_options.master_edges[DCG_DRAW_FLAG]     = self.params["master_edges"]
                self.drawing_options.slave_edges[DCG_DRAW_FLAG]      = self.params["slave_edges"]


		self.OCA_actions_ptr    = self.get_ns_pointer("OCA/ACTIONS")

		self.consume = self.params["consume"]
		self.layout = self.params["layout"]
		self.print_level = self.params["print_level"]
		if self.params["outfile"] == "-":
			self.outfile = sys.stdout
		else:
			self.outfile = open(self.params["outfile"], "w")

    		self.DCG = NX.XDiGraph(multiedges=True)

		self.OCA_actions = [
			OCA_ROOT_THREAD,
			OCA_FORK,
			OCA_ROOT_FD,
			OCA_SIGNAL_SEND,
			OCA_PIPE_CREATE,
			OCA_OPEN,
			OCA_READ,
			OCA_WRITE,
			OCA_CLOSE,
			OCA_SHM_ATTACH,
			OCA_SHM_DETACH,
			OCA_SOCKET_CONNECT,
			OCA_SOCKET_ACCEPT,
			OCA_SOCKET_CREATE,
			OCA_SOCKET_SEND_TO,
			OCA_SOCKET_RECV_FROM,
			OCA_SOCKET_SEND_MSG,
			OCA_SOCKET_RECV_MSG,
			#OCA_FCNTL_LOCK,
			#OCA_FCNTL_UNLOCK,
			OCA_PTRACE_ATTACH,
			OCA_PTRACE_DETACH,
			OCA_EXEC,

			# TODO: Attach as attributes to the read and write events
			# whether or not the file is locked
			# OCA_LOCKED_READ,
			# OCA_LOCKED_WRITE
		]

		self.OCA_rename = [
			OCA_DSUI_THREAD_SIGNAL_CATCHER,
			OCA_DSUI_THREAD_LOGGING,
			OCA_DSUI_THREAD_BUFFER
		]

		self.Java_threads = [
			"Java Wrapper",
			"Java Watcher",
			"Java Native",
			"Java Signal",
			"Java Low Memory Detector",
			"Java Compiler",
			"Java VM",
			"Java GC",
			"Attach Listener"
		]

        def process(self, entity):
		match = False
		data = entity.get_extra_data()

		if data is None:
			#print "data is null : ",entity.get_name()
			return
	
		if data.has_key(OCA_TYPE):
			if data[OCA_TYPE] in self.OCA_actions:
				add_OCA_to_DCG(self.DCG, data)
				match = True
			elif data[OCA_TYPE] in self.OCA_rename:
				rename_uthread_node(self.DCG, data[OCA_ARG_PID], data[OCA_ARG_AC_NAME],"True")
				match = True
			elif data[OCA_TYPE] in self.Java_threads:
				rename_uthread_node(self.DCG, data[OCA_ARG_PID], data[OCA_ARG_AC_NAME],"False")
				match = True
				print data[OCA_ARG_AC_NAME]

		if not match or (match and not self.consume):
			self.send_output("default", entity)
			return

	def finalize(self):

		# Node_attributes is a globally defined dictionary of all of the
		# nodes and their attributes. It is defined in the dcg module.
		#
		if self.print_level > 0:
			self.pretty_print(self.DCG)
		else:
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
			pos = do_layout(self.DCG, self.layout)

			# Now draw the nodes and edges as specified by drawing_options.
    			# While we are using a unified layout, the only choosing we have
    			# to do is construction of node lists and edge lists. 
    			#
			self.drawing_options.construct_lists(self.DCG, Node_attributes)
			#rename_nodes(self.DCG)
			self.drawing_options.draw_graph_as_specified(self.DCG, pos, Node_attributes)	

	def pretty_print(self, DCG):

		print >> self.outfile, "DCG Graph:\n"
		keys = Node_attributes.keys()
		keys.sort(self.node_comp)
		for node in keys:
			na = Node_attributes[node]
			print >> self.outfile, "%s %s" % (na[DCG_NA_TYPE], na[DCG_NA_STRING])
			if na[DCG_NA_TYPE] == DCG_NT_UTHREAD:
				print >> self.outfile, "\tGeneration: ", na[DCG_NA_GEN]
				print >> self.outfile, "\tExec: ", na[DCG_NA_EXEC]
			
			edges = DCG.edges(node)
			if edges:
				print >> self.outfile, "\tHas edges to:"
				# Edges are a triple - (from_node, to_node, edge_attr)
				for edge in edges:
					to_node = Node_attributes[edge[1]]
					if to_node[DCG_NA_TYPE] == DCG_NT_PSEUDOT or to_node[DCG_NA_TYPE] == DCG_NT_FILE:
						if self.print_level > 0:
							print >> self.outfile, "\t\t%s %s" % (to_node[DCG_NA_TYPE], to_node[DCG_NA_STRING]),
							print >> self.outfile, "\t ( %s )" % (edge[2][DCG_EA_STRING])
					else:
						print >> self.outfile, "\t\t%s %s" % (to_node[DCG_NA_TYPE], to_node[DCG_NA_STRING]),
						print >> self.outfile, "\t ( %s )" % (edge[2][DCG_EA_STRING])
			else:
				print >> self.outfile, "\tHas 0 out edges"
			print >> self.outfile, ""

	def node_comp(self, x, y):
		"""
		Comparator for node sort. Sorts first by DCG_NA_TYPE, second by
		DCG_NA_STRING.
		"""
		if Node_attributes[x][DCG_NA_TYPE] > Node_attributes[y][DCG_NA_TYPE]:
			return 1
		elif Node_attributes[x][DCG_NA_TYPE] == Node_attributes[y][DCG_NA_TYPE]:
			if Node_attributes[x][DCG_NA_STRING] > Node_attributes[y][DCG_NA_STRING]:
				return 1
			else:
				return -1
		else:
			return -1

	def edges_comp(self, x, y):
		# TODO: Maybe consider sorting by time for edge printout
		"""
		Comparator for edges.
		
		x_attr = x[2]
		y_attr = y[2]
		if x_attr[DCG_EA_TYPE] == DCG_ET_INHERIT_FD:
			return 1
		elif x_attr[DCG_EA_TYPE] == DCG_ET_INHERIT_SHM:
			return 1
		else:
		"""
