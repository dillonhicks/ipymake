"""gschedfilter.py 

A Data Streams Post Processing filter for the extracting
and narration of Group Scheduling Data Stream events.

@author: Dillon Hicks
@contact: hhicks[at]ittc[dot]ku[dot]edu
@organization: KUSP
@version: 1.0

@summary: This filter was created for Group Scheduling event
    narration.  The ability to narrate Group Scheduling with Data
    Streams will be an invaluable tool for debugging our growing
    number of Group Scheduling examples. When Group Scheduling dies
    completely, it normally dies with a kernel panic. Being able to
    see the last events that led up to the panic will greatly reduce
    the amount of time we spend scratching our heads trying to figure
    out where it died, and allow us to spend more time on the more in
    important problem of why it died.

@changes: 
    1.0: Original Code

"""
import sys
from datastreams.postprocess import filtering
from datastreams.postprocess import entities
from datastreams import namespaces

class GSFilter(filtering.Filter):
    """Finds and filters the Data Stream Kernel Interface 
        pipeline entities that are related to Group Scheduling. 
        The filtered instrumentation points originate from gsched_core.c.
        
    FILTERED EVENTS
   ===================
    
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

        # COMMENT ME 
        #
        self.outpath = None
        if self.params.has_key('output_file'):
            self.outpath = self.params['output_file']
   
        
        ##############################################
        #  Filtered Event Structures For Finalize
        ##############################################
        
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
                
                
        if (not match) or (match and not self.consume):
            self.send_output("default", entity)


    def finalize(self):
        """If we were to do so, here is where we would implement
        "finalize". The "finalize" hook is executed after all other
        portions of the filter. Because of this, one of the more
        common uses of the "finalize" portion of the filter is
        operations that require the entire event stream. The events
        received in "process" can simply be stored in a list or
        dictionary, and then the entire set of event data will be
        available here, as "finalize" will not be called until every
        event entering the filter has passed through "process". After
        performing post- processing on the entire set of events, those
        that the developer desires to pass on to the rest of the
        pipeline are sent using the same self.send_output command seen
        above.
        """
        
        if self.outpath:
            # User specified an file path to which to write
            # the Group Scheduling Events, Attempt to open
            # specified file for writing.
            #
            try:
                outstream = open(self.outpath, 'w')
            except IOError, eargs:
                # Nope, it isn't writable due to an IOError. 
                # Let them know the error and warn them that
                # the default action is to fallback to stdout
                # as an output stream if the output they 
                # specify fails to initialize.
                #
                print 'Error: GSFilter.finalize : %s' % eargs
                print 'Warning: Falling back to output stream sys.stdout'
                outstream = sys.stdout
        else:
            outstream = sys.stdout
        
        # Print all the events to the output stream.
        # 
        for gsched_event in self.gsched_events:
            print >> outfile, gsched_event
            
        # Check to see if the pointer to 
        # stdout is the same as the pointer
        # to our outstream.
        #
        if outstream != sys.stdout:
            # It isn't so close the file. 
            # If our outstream was stdout you probably wouldn't
            # want to close it.
            #
            outstream.close()
        