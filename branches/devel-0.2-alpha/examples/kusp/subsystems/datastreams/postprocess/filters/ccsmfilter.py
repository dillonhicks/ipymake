"""
:mod:`ccsmfilter` -- DSPP Filter for CCSM 
===========================================
    :synopsis: A Data Streams Post Processing filter for the extracting
        and narration of CCSM Data Stream events.

.. moduleauthor:: Dillon Hicks <hhicks[at]ittc[dot]ku[dot]edu>

"""

#not included in autodocs
"""
**Current Version 1.0**


Module Changes
==================

*Version* *(YYYY-MM-DD)* : *Changes*

* 1.0 : Original stable code.
* 1.1 (2009-11-04) : Added BuildCCSMSetFitler
"""

import sys
from datastreams.postprocess import filtering
from datastreams.postprocess import entities
from datastreams import namespaces
import pyccsm.ccsmgraphviz as ccsmgraph
from pyccsm.ccsmstructures import CCSMSet

class CCSMFilter(filtering.Filter):
    """Finds and filters the Data Stream Kernel Interface pipeline
        entities that are produced by CCSM (Computation Component Set
        Manager).  The filtered instrumentation points originate from
        ccsm_core.c.
        
    FILTERED EVENTS
   ===================
    
   
   * DSTRM_DEBUG_DECL(CCSM, DEBUG);
   * DSTRM_EVENT_DATA(CCSM, DELETE, 0, strnlen(set->name, CCSM_MAX_NAME_LEN), set->name, "print_string");
   * DSTRM_EVENT_PRINTF(CCSM, SET_CREATE, flags, set->name);
   * DSTRM_EVENT_PRINTF(CCSM, SET_DESTROY, 0, set->name);
   * DSTRM_EVENT_DATA(CCSM, CALLBACK, condition, strnlen(set->name, CCSM_MAX_NAME_LEN), set->name, "print_string");
   * DSTRM_EVENT_PRINTF(CCSM, COMP_CREATE, 0, set->name);
   * DSTRM_EVENT_PRINTF(CCSM, COMP_DESTROY, 0, set->name);
   * DSTRM_EVENT_PRINTF(CCSM, ADD, 0, "%s|%s", set->name, owner->name);
   * DSTRM_EVENT_PRINTF(CCSM, REMOVE, 0, "%s|%s", set->name, owner->name);
      
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
        
        # CCSM Data Stream Name Space pointers 
        #
        self.ccsm_debug_ptr = self.get_ns_pointer("CCSM/DEBUG")
        self.delete_ptr = self.get_ns_pointer("CCSM/DELETE")
        self.set_create_ptr = self.get_ns_pointer("CCSM/SET_CREAT")
        self.set_destroy_ptr = self.get_ns_pointer("CCSM/SET_DESTROY")
        self.callback_ptr = self.get_ns_pointer("CCSM/CALLBACK")
        self.comp_create_ptr = self.get_ns_pointer("CCSM/COMP_CREATE")
        self.comp_destroy_ptr = self.get_ns_pointer("CCSM/COMP_DESTROY")
        self.add_ptr = self.get_ns_pointer("CCSM/ADD")
        self.remove_ptr = self.get_ns_pointer("CCSM/REMOVE")
                    
        # This list is created to make all of the namespace pointers
        # iterable. So there can be a simple 'catch-all' loop 
        # for CCSM events in process().
        #
        self.pointers_list = [
                             self.ccsm_debug_ptr,
                             self.delete_ptr,
                             self.set_create_ptr,
                             self.set_destroy_ptr,
                             self.callback_ptr,
                             self.comp_create_ptr,
                             self.comp_destroy_ptr,
                             self.add_ptr,
                             self.remove_ptr
                            ]
        
        
        ################################
        #  Filter Configuration Options
        ################################

        # This last parameter will simply determine if the events used
        # to generate the above intervals will be passed on to any
        # following filters, or destroyed.
        self.consume = self.params['consume']

        # The outpath for the CCSM narration.
        self.outpath = None
        if self.params.has_key('outfile'):
            self.outpath = self.params['outfile']
   
        
        ##############################################
        #  Filtered Event Structures For Finalize
        ##############################################
                
        # List of ccsm events taken from the pipeline.
        self.ccsm_events = []
        
        
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
                self.ccsm_events.append('%s | %s' % (name, extra_data))
                
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
                print 'Error: CCSMFilter.finalize : %s' % eargs
                print 'Warning: Falling back to output stream sys.stdout'
                outstream = sys.stdout
        else:
            outstream = sys.stdout
        
        # Print all the events to the output stream.
        # 
        for ccsm_event in self.ccsm_events:
            print >> outstream, ccsm_event
            
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
        
class BuildCCSMSetFilter(filtering.Filter):
    """
    Development in Progress.
        
    FILTERED EVENTS
   ===================
    
   
   * DSTRM_DEBUG_DECL(CCSM, DEBUG);
   * DSTRM_EVENT_DATA(CCSM, DELETE, 0, strnlen(set->name, CCSM_MAX_NAME_LEN), set->name, "print_string");
   * DSTRM_EVENT_PRINTF(CCSM, SET_CREATE, flags, set->name);
   * DSTRM_EVENT_PRINTF(CCSM, SET_DESTROY, 0, set->name);
   * DSTRM_EVENT_DATA(CCSM, CALLBACK, condition, strnlen(set->name, CCSM_MAX_NAME_LEN), set->name, "print_string");
   * DSTRM_EVENT_PRINTF(CCSM, COMP_CREATE, 0, set->name);
   * DSTRM_EVENT_PRINTF(CCSM, COMP_DESTROY, 0, set->name);
   * DSTRM_EVENT_PRINTF(CCSM, ADD, 0, "%s|%s", set->name, owner->name);
   * DSTRM_EVENT_PRINTF(CCSM, REMOVE, 0, "%s|%s", set->name, owner->name);
      
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
        
        # CCSM Data Stream Name Space pointers 
        #
        self.ccsm_debug_ptr = self.get_ns_pointer("CCSM/DEBUG")
        self.delete_ptr = self.get_ns_pointer("CCSM/DELETE")
        self.set_create_ptr = self.get_ns_pointer("CCSM/SET_CREAT")
        self.set_destroy_ptr = self.get_ns_pointer("CCSM/SET_DESTROY")
        self.callback_ptr = self.get_ns_pointer("CCSM/CALLBACK")
        self.comp_create_ptr = self.get_ns_pointer("CCSM/COMP_CREATE")
        self.comp_destroy_ptr = self.get_ns_pointer("CCSM/COMP_DESTROY")
        self.add_ptr = self.get_ns_pointer("CCSM/ADD")
        self.remove_ptr = self.get_ns_pointer("CCSM/REMOVE")
                    
        # This list is created to make all of the namespace pointers
        # iterable. So there can be a simple 'catch-all' loop 
        # for CCSM events in process().
        #
        self.pointers_list = [
                             self.ccsm_debug_ptr,
                             self.delete_ptr,
                             self.set_create_ptr,
                             self.set_destroy_ptr,
                             self.callback_ptr,
                             self.comp_create_ptr,
                             self.comp_destroy_ptr,
                             self.add_ptr,
                             self.remove_ptr
                            ]
        
        
        ################################
        #  Filter Configuration Options
        ################################

        # This last parameter will simply determine if the events used
        # to generate the above intervals will be passed on to any
        # following filters, or destroyed.
        self.consume = self.params['consume']

        # The outpath for the CCSM narration.
        self.outpath = None
        if self.params.has_key('outfile'):
            self.outpath = self.params['outfile']
   
        
        ##############################################
        #  Filtered Event Structures For Finalize
        ##############################################
                
        # List of ccsm events taken from the pipeline.
        self.ccsm_events = []
        
        
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
                self.ccsm_events.append('%s | %s' % (name, extra_data))
                
        if (not match) or (match and not self.consume):
            self.send_output("default", entity)


    def finalize(self):
        """
        The method that will build and graph the set(s).
        """
        
        ccsm_sets = {}

        # This is overkill now but I am setting it up now so that
        # there is the possiblity of expanding this to have the same
        # graph building functionality of BuildGSHFilter.
        #
        actions_dict = {
            'ADD' : lambda member, set : self._add_set(member, set, ccsm_sets),
            
            }

        
        gen_event_data = (event.split('|') for event in self.ccsm_events)
        
        for ccsm_event in gen_event_data:
            if len(ccsm_event) > 2:
                action_name, member_name, set_name = ccsm_event
                action_name = action_name.strip()
                member_name = member_name.strip()
                
                actions_dict[action_name](member_name, set_name)
                
            else:
                # Nothing to do for these yet.
                pass
        
        root_sets = []
        for (name, set) in ccsm_sets.items():
            if set.get_parent() is None:
                root_sets.append(set)

        for (index, root_set) in enumerate(root_sets):
            gfilename = "%i_%s"%(index, self.outpath)
            ccsmgraph.create_image_from_ccsmh(root_set, outpath=gfilename)
        pass
        

    def _add_set(self, member, set, ccsm_sets):
        if not ccsm_sets.has_key(member):
            self._create_set(member, ccsm_sets)
        if not ccsm_sets.has_key(set):
            self._create_set(set, ccsm_sets)

        parent_set = ccsm_sets[set]
        member_set = ccsm_sets[member]
        parent_set.add_member(member_set)
        

    def _create_set(self, name, ccsm_sets):
        ccsm_sets[name] = CCSMSet(name)
