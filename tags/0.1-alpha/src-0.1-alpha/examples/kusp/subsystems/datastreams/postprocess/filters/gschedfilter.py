
"""
==============================================================
:mod:`gschedfilter` Group Scheduling Post Processing Filters
==============================================================
    :synopsis: A Data Streams Post Processing filter for the extracting
        and narration of Group Scheduling Data Stream events.

.. moduleauthor:: Dillon Hicks <hhicks@ittc.ku.edu>

**Current Version: 1.0**

This filter was created for Group Scheduling event
narration.  The ability to narrate Group Scheduling with Data
Streams will be an invaluable tool for debugging our growing
number of Group Scheduling examples. When Group Scheduling malfunctions
completely, it normally does preceding a kernel panic. Being able to
see the last events that led up to the panic will greatly reduce
the amount of time we spend scratching our heads trying to figure
out where it died, and allow us to spend more time on the more in
important problem of why it malfunctioned.

Module Changes
===============

*Version* *(YYYY-MM-DD)*: *Changes*

* 1.0 (2009-09-25): Created :class:`GSFilter`.

"""
import sys
import time
from datastreams.postprocess import filtering
from datastreams.postprocess import entities
from datastreams import namespaces
from pygsched.gshierarchy import GSThread, GSGroup, GSHierarchy 
import pygsched.gsgraphviz as gsgraph

class GSFilter(filtering.Filter):
    """
    Finds and filters the Data Stream Kernel Interface 
    pipeline entities that are related to Group Scheduling. 
    The filtered instrumentation points originate from gsched_core.c.
        
    FILTERED EVENTS:
    
    * DSTRM_DEBUG_DECL(GSCHED, DEBUG);
    * DSTRM_EVENT_PRINTF(GSCHED, GRP_CREATE, 0,
                          "%s|%s", name, sdf_name);
    * DSTRM_EVENT_PRINTF(GSCHED, GRP_DESTROY, 0,
                          "%s|%s", name, group -> sdf -> name);
    * DSTRM_EVENT_PRINTF(GSCHED, REGISTER, 0, sched -> name);
    * DSTRM_EVENT_PRINTF(GSCHED, UNREGISTER, 0, sched -> name);
    * DSTRM_EVENT_PRINTF(GSCHED, MEM_JOIN, 0, "%s|%d|%s",
                           member_name, pid, group_name);
    * DSTRM_EVENT_PRINTF(GSCHED, NAME_BOUND, 0, "%d|%s|%s",
                task -> pid, cargs -> ccsm_name, cargs -> group_name);                      
    * DSTRM_EVENT_PRINTF(GSCHED, NAME_REGISTER, 0, "%d|%s|%s",
                 current -> pid, cargs -> ccsm_name, cargs -> group_name);
    * DSTRM_EVENT_PRINTF(GSCHED, GRP_JOIN, 0, "%s|%s|%s",
                   addgroup_name, group_name, member_name);                     
    * DSTRM_EVENT_PRINTF(GSCHED, GRP_SET, 0, group -> name);                     
    * DSTRM_EVENT_PRINTF(GSCHED, MEM_SET, 0,
                     "%s|%s", member -> name, group -> name);
     
    * DSTRM_EVENT_PRINTF(GSCHED, MEM_LEAVE, 0, "%s|%s",
                                   member -> name, group -> name);
    * DSTRM_EVENT_PRINTFGSCHED, GRP_LEAVE, 0, "%s|%s", 
                           member->name, group->name);
  
    """
    expected_parameters = {
            "outfile" : {
                         'types' : 'string',
                         'doc'   : 'The path of the outfile to print to.',
                         'default' : ''
                         },
            
            "consume" : {
                         "types" : "boolean",
                         "doc" : "Whether to delete matching entities after processing",
                         "default" : False
                         },
    }

    def initialize(self):
        """The "initialize" hook provides a location for declaring
        global variables and reading in any filter options or
        configuration file arguments specified by the
        expected_parameters dictionary. It is called before any other
        portion of the filter. The hook takes in a reference to "self"
        which is, as the name indicates, the filter itself. To create
        a global variable, just add the variable in dotted notation to
        "self".
        """
        
        #####################################
        #   Filter Entity Pointers
        #####################################
        
        # GS Debug Declaration
        #
        self.gsched_debug_ptr = self.get_ns_pointer("GSCHED/DEBUG")
        
        # GS-Group functions
        # 
        self.group_set_parameters_ptr = self.get_ns_pointer("GSCHED/GRP_SET")
        self.group_create_ptr = self.get_ns_pointer("GSCHED/GRP_CREATE")
        self.group_destroy_ptr = self.get_ns_pointer("GSCHED/GRP_DESTROY")
        self.group_join_ptr = self.get_ns_pointer("GSCHED/GRP_JOIN")
        self.group_leave_ptr = self.get_ns_pointer("GSCHED/GRP_LEAVE")       
        
        # GS-Member functions
        self.member_join_ptr = self.get_ns_pointer("GSCHED/MEM_JOIN")
        self.member_leave_ptr = self.get_ns_pointer("GSCHED/MEM_LEAVE")
        self.member_set_parameters_ptr = self.get_ns_pointer("GSCHED/MEM_SET")
                
        # This list is created to make all of the namespace pointers
        # iterable. So there can be a simple 'catch-all' loop 
        # for group scheduling events in process().
        #
        self.pointers_list = [
                            self.gsched_debug_ptr,
                            self.group_set_parameters_ptr,
                            self.group_create_ptr,
                            self.group_destroy_ptr,
                            self.group_join_ptr,
                            self.group_leave_ptr,
                            self.member_join_ptr,
                            self.member_leave_ptr,
                            self.member_set_parameters_ptr,
                            ]
        
        
        ################################
        #  Filter Configuration Options
        ################################

        # This last parameter will simply determine if the events used
        # to generate the above intervals will be passed on to any
        # following filters, or destroyed.
        self.consume = self.params["consume"]
   
        if 'outfile' in self.params:
            # User specified an file path to which to write
            # the Group Scheduling Events, Attempt to open
            # specified file for writing.
            #
            try:
                self.outstream = open(self.params['outfile'], 'w')
            except IOError, eargs:
                # Nope, it isn't writable due to an IOError. 
                # Let them know the error and warn them that
                # the default action is to fallback to stdout
                # as an output stream if the output they 
                # specify fails to initialize.
                #
                print 'Error: GSFilter.finalize : %s' % eargs
                print 'Warning: Falling back to output stream sys.stdout'
                self.outstream = sys.stdout
        else:
            self.outstream = sys.stdout

        # Make times relative to make them easier to read.
        self.start_time = None
                        
    def process(self, entity):
        """ The "process" hook must be implemented when creating a
        custom filter. It is also the only hook which receives the
        events flowing down the pipeline. The 'filtering' happens
        here. 
        """
        match = False

        # The first event indicates the start time.
        if not self.start_time:
            self.start_time = entity.get_nanoseconds()


        action = {
            'MEM_JOIN' : lambda member_name, parent_name, type, pid :\
            'task %s joined group "%s" under the name "%s"' % (pid, parent_name, member_name),
            'GRP_JOIN' : lambda member_name, parent_name, type, group_name :\
                'group "%s" joined group "%s" under the name "%s"' % (group_name, parent_name, member_name),
            'GRP_CREATE' : lambda group_name, sdf :\
                'a group named "%s" using sdf "%s" was created' % (group_name, sdf),
            'MEM_SET' : lambda member_name, group_name :\
                'a member variable was set for member "%s" of group "%s"' % (member_name, group_name),
            'GRP_SET' : lambda group_name :\
                'a group variable was set for group "%s"' % (group_name),
            'MEM_LEAVE' : lambda member_name, group_name :\
                'task member "%s" left group "%s"' % (member_name, group_name),
            'GRP_LEAVE' : lambda member_name, group_name :\
                'group member "%s" left group "%s"' % (member_name, group_name),
            'GRP_DESTROY' : lambda group_name, sdf :\
                'group "%s" was destroyed' % (group_name),
            'DEBUG' : lambda msg :\
                'WARNING: %s' % msg
            }

        for pointer in self.pointers_list:
            if entity.get_cid() == pointer.get_cid():
                match = True

                name = entity.get_name()
                extra_data = entity.get_extra_data().split('|')

                # Compute relative time to the beginning of the evnet log.
                time = (entity.get_nanoseconds() - self.start_time) / 10**3
                print entity.get_pid(), time, name, extra_data
                print >> self.outstream, 'Task %s: At time %d us, %s.' % (entity.get_pid(), time, action[name](*extra_data))
                
        if (not match) or (match and not self.consume):
            self.send_output("default", entity)


    def finalize(self):
                    
        # Check to see if the pointer to 
        # stdout is the same as the pointer
        # to our outstream.
        #
        if 'outfile' in self.params:
            # It isn't so close the file. 
            # If our outstream was stdout you probably wouldn't
            # want to close it.
            #
            self.outstream.close()
        


class BuildGSHFilter(filtering.Filter):
    """
    Finds and filters the Data Stream Kernel Interface 
    pipeline entities that are related to Group Scheduling. 
    The filtered instrumentation points originate from gsched_core.c.
        
    FILTERED EVENTS:
    
    * DSTRM_DEBUG_DECL(GSCHED, DEBUG);
    * DSTRM_EVENT_PRINTF(GSCHED, GRP_CREATE, 0,
                          "%s|%s", name, sdf_name);
    * DSTRM_EVENT_PRINTF(GSCHED, GRP_DESTROY, 0,
                          "%s|%s", name, group -> sdf -> name);
    * DSTRM_EVENT_PRINTF(GSCHED, REGISTER, 0, sched -> name);
    * DSTRM_EVENT_PRINTF(GSCHED, UNREGISTER, 0, sched -> name);
    * DSTRM_EVENT_PRINTF(GSCHED, MEM_JOIN, 0, "%s|%d|%s",
                           member_name, pid, group_name);
    * DSTRM_EVENT_PRINTF(GSCHED, NAME_BOUND, 0, "%d|%s|%s",
                task -> pid, cargs -> ccsm_name, cargs -> group_name);                      
    * DSTRM_EVENT_PRINTF(GSCHED, NAME_REGISTER, 0, "%d|%s|%s",
                 current -> pid, cargs -> ccsm_name, cargs -> group_name);
    * DSTRM_EVENT_PRINTF(GSCHED, GRP_JOIN, 0, "%s|%s|%s",
                   addgroup_name, group_name, member_name);                     
    * DSTRM_EVENT_PRINTF(GSCHED, GRP_SET, 0, group -> name);                     
    * DSTRM_EVENT_PRINTF(GSCHED, MEM_SET, 0,
                     "%s|%s", member -> name, group -> name);
     
    * DSTRM_EVENT_PRINTF(GSCHED, MEM_LEAVE, 0, "%s|%s",
                                   member -> name, group -> name);
    * DSTRM_EVENT_PRINTFGSCHED, GRP_LEAVE, 0, "%s|%s", 
                           member->name, group->name);
  
    """
    expected_parameters = {
            "outfile" : {
                         'types' : 'string',
                         'doc'   : 'The path of the outfile to print to.',
                         'default' : ''
                         },
            
            "consume" : {
                         "types" : "boolean",
                         "doc" : "Whether to delete matching entities after processing",
                         "default" : False
                         },
    }

    def initialize(self):
        """The "initialize" hook provides a location for declaring
        global variables and reading in any filter options or
        configuration file arguments specified by the
        expected_parameters dictionary. It is called before any other
        portion of the filter. The hook takes in a reference to "self"
        which is, as the name indicates, the filter itself. To create
        a global variable, just add the variable in dotted notation to
        "self".
        """
        
        #####################################
        #   Filter Entity Pointers
        #####################################
        
        # GS Debug Declaration
        #
        self.gsched_debug_ptr = self.get_ns_pointer("GSCHED/DEBUG")
        
        # GS-Group functions
        # 
        self.group_set_parameters_ptr = self.get_ns_pointer("GSCHED/GRP_SET")
        self.group_create_ptr = self.get_ns_pointer("GSCHED/GRP_CREATE")
        self.group_destroy_ptr = self.get_ns_pointer("GSCHED/GRP_DESTROY")
        self.group_join_ptr = self.get_ns_pointer("GSCHED/GRP_JOIN")
        self.group_leave_ptr = self.get_ns_pointer("GSCHED/GRP_LEAVE")       
        
        # GS-Member functions
        self.member_join_ptr = self.get_ns_pointer("GSCHED/MEM_JOIN")
        self.member_leave_ptr = self.get_ns_pointer("GSCHED/MEM_LEAVE")
        self.member_set_parameters_ptr = self.get_ns_pointer("GSCHED/MEM_SET")
        
        # Scheduler functions
        #
        self.register_scheduler_ptr = self.get_ns_pointer("GSCHED/REGISTER")
        self.unregister_scheduler_ptr = self.get_ns_pointer("GSCHED/UNREGISTER")
        
        # CCSM functions
        #
        self.register_ccsm_name_ptr = self.get_ns_pointer("GSCHED/NAME_REGISTER")
        self.bound_ccsm_name_ptr = self.get_ns_pointer("GSCHED/NAME_BOUND")
        
        # This list is created to make all of the namespace pointers
        # iterable. So there can be a simple 'catch-all' loop 
        # for group scheduling events in process().
        #
        self.pointers_list = [
                            self.gsched_debug_ptr,
                            self.group_set_parameters_ptr,
                            self.group_create_ptr,
                            self.group_destroy_ptr,
                            self.group_join_ptr,
                            self.group_leave_ptr,
                            self.member_join_ptr,
                            self.member_leave_ptr,
                            self.member_set_parameters_ptr,
                            self.register_scheduler_ptr,
                            self.unregister_scheduler_ptr,
                            self.register_ccsm_name_ptr,
                            self.bound_ccsm_name_ptr
                            ]
        
        
        ################################
        #  Filter Configuration Options
        ################################

        # This last parameter will simply determine if the events used
        # to generate the above intervals will be passed on to any
        # following filters, or destroyed.
        self.consume = self.params["consume"]

        # The outpath for the GSCHED narration.
        self.outpath = None
        if self.params.has_key('outfile'):
            self.outpath = self.params['outfile']
        else:
            self.outpath = 'gsh_postprocess_graph.svg'
        ##############################################
        #  Filtered Event Structures For Finalize
        ##############################################
                
        # List of gsched events taken from the pipeline.
        self.gsched_events = []

       
    def process(self, entity):
        """ The "process" hook must be implemented when creating a
        custom filter. It is also the only hook which receives the
        events flowing down the pipeline. The 'filtering' happens
        here. 
        """
        match = False

        for pointer in self.pointers_list:
            if entity.get_cid() == pointer.get_cid():
                match = True
                name = entity.get_name()
                extra_data = entity.get_extra_data()
                self.gsched_events.append("%s | %s"%(name, extra_data))
                
        if (not match) or (match and not self.consume):
            self.send_output("default", entity)


    def finalize(self):
        """
        
        Most unreadable code ever made, but undeniably awesome.
        
        GRP_CREATE  | socket_pipeline|sdf_seq
        GRP_JOIN    | socket_pipeline_mem|gsched_top_seq_group|group|socket_pipeline
        MEM_JOIN    | thread-2|socket_pipeline|task|2909
        MEM_SET     | thread-2|socket_pipeline
        MEM_JOIN    | thread-0|socket_pipeline|task|2910
        MEM_SET     | thread-0|socket_pipeline
        MEM_JOIN    | thread-1|socket_pipeline|task|2911
        MEM_SET     | thread-1|socket_pipeline
        MEM_JOIN    | thread-3|socket_pipeline|task|2912
        MEM_SET     | thread-3|socket_pipeline
        GRP_LEAVE   | socket_pipeline_mem|gsched_top_seq_group
        GRP_DESTROY | socket_pipeline|sdf_seq
        """
         
        members = {}
        
        actions = {'GRP_CREATE' : self.__create_group,
                   
                   'GRP_JOIN'   : lambda members, member_name, parent_name, type, group_name :\
                                    self.__group_join_group(members, group_name, parent_name), 
                   
                   'MEM_JOIN'   : lambda members, member_name, parent_name, type, pid :\
                                    self.__create_thread(members, member_name, pid) or \
                                    self.__thread_join_group(members, member_name, parent_name) }
        
        for gsched_event in self.gsched_events:
            #print >> self.outstream, 'GSCHEDEVENT: ', gsched_event
            fields = gsched_event.split('|')
            #print fields
            for i in range(len(fields)):
                fields[i] = fields[i].strip()
            
            if fields[0] in actions.keys():
                actions[fields[0]](members, *fields[1:])
            
        root_group = None
        for mem in members.values():
            if isinstance(mem, GSGroup):
                if mem.get_parent() is None:
                    root_group = mem
                    break

        
        if not root_group is None:
            if self.outpath:
                gsgraph.image_from_gsh(root_group, outpath=self.outpath)
            else:
                gsgraph.image_from_gsh(root_group)

    
    def __create_group(self, members, group_name, sdf_name):
        #print >> self.outstream, 'create group'
        members[group_name] = GSGroup(group_name, sdf_name)
        
    
    def __create_thread(self, members, thread_name, data):
        #print >> self.outstream, 'create thread'
        members[thread_name] = GSThread(thread_name, doc=data)
    
    def __thread_join_group(self, members, thread_name, parent_name):
        #print >> self.outstream, 'thread join group'
        if not parent_name in members.keys():
            self.__create_group(members, parent_name, 'sdf-not-specified')
        if not thread_name in members.keys():
            self.__create_thread(members, thread_name, 'Created By Inference')
        
        parent_group = members[parent_name]
        gsthread = members[thread_name]
        parent_group.add_member(gsthread)
        
    def __group_join_group(self, members, group_name, parent_name ):
        #print >> self.outstream, 'group join group'
        if not group_name in members.keys():
            self.__create_group(members, group_name, 'sdf-not-specified')
        if not parent_name in members.keys():
            self.__create_group(members, parent_name, 'sdf-not-specified')
        
        parent_group = members[parent_name]
        gsgroup = members[group_name]
        parent_group.add_member(gsgroup)
        
    
