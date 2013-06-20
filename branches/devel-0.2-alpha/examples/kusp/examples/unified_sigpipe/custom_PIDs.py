from datastreams.postprocess import filtering
from datastreams.postprocess import entities
from datastreams import namespaces
import os

#This is a really ugly solution to accessing the tags and filtering by PID.

class filter_PID(filtering.Filter):
    """This custom filter is used to find the thread PIDs for the 
    sigpipe example. These are then saved to a file for the purposes
    of a rough filter to get only those context switch events for the
    sigpipe example. """
    
    expected_parameters = {
        "filename" : {
            "types" : "string",
            "doc" : "Name of file to save thread PIDs to",
            "required" : True
        },
    }
    
    
    def initialize(self):
        self.ptr = self.get_ns_pointer("THREAD/THREAD_ID")
        self.outfile = open(self.params["filename"], "w") 
    
    def process(self, entity):
        if entity.get_cid() == self.ptr.get_cid():
            self.outfile.write(str(entity.get_tag()) + '\n')
            
        self.send(entity)
   
    def finalize(self):
        self.outfile.close()
        
        

class filter_context_events(filtering.Filter):
    """This filter is to be called after the filter_PID filter. 
    It retrieves the PID values from the file, and then checks if 
    the PIDs of the context switch events match up. If they do, they
    are passed on. """
    
    expected_parameters = {
        "filename" : {
            "types" : "string",
            "doc" : "Name of file to retrieve thread PIDs to",
            "required" : True
        },
        "discard" : {
            "types" : "boolean",
            "doc" : "If True, discard events with matching PIDs. If False, \
                    retain events with matching PIDs.",
            "default" : False
        },
    }
    
    def initialize(self):

        self.to_ptr = self.get_ns_pointer("SCHEDULER/SWITCH_TO")
        self.from_ptr = self.get_ns_pointer("SCHEDULER/SWITCH_FROM")
        
        self.discard = self.params["discard"]
        
        self.entities = []

        self.pids = []
        self.real_pids = []

    def process(self, entity): 
    
        #We have to find the PIDs here, because all the filters are initialized in the 
        #beginning. This would cause us not to find any PIDs in the file, as it would
        #not have been written to yet. 
        if not self.pids:
            self.infile = open(self.params["filename"], "r") 
            self.pids = self.infile.readlines()
            for pid in self.pids:
                pid = int(pid)
                self.real_pids.append(pid)
            
        #We create a list of entities to check PIDs later on
        self.entities.append(entity)

    def finalize(self):
    
        for entity in self.entities:
            if entity.get_cid() == self.to_ptr.get_cid() or entity.get_cid() == self.from_ptr.get_cid():
                #Only send entity if its tag matches one of the PIDs
                if (not self.discard) and entity.get_pid() in self.real_pids:
                    self.send(entity)
                elif self.discard and entity.get_pid() not in self.real_pids:
                    self.send(entity)
                    
        #If it is not a context switch event (a DSUI event), ignore it
    
        #Close file. Not removing in case it needs to be accessed in multiple places
        self.infile.close()
        
    
    
    
    
    
    
    
    
    
