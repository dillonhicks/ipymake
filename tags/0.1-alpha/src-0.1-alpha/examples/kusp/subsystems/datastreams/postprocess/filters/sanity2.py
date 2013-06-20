"""Filters to determine whether the datastream is as it should be."""

#Try to make a single filter that detects all errors. Maybe have a parameter that specifies a file to write the errors to?

from datastreams.postprocess2 import filtering
from datastreams.postprocess2 import entities
from datastreams import namespaces
import random
import sys

class trouble_maker(filtering.Filter):
	"""Screws up the incoming data stream in order to test sanity filters.

	Creates holes and out-of-order events."""


	def initialize(self):
		self.entities = []

	def process(self, entity):

		rand = random.random()

		#Randomly destroy events
		if rand >= 0.9:
		    return
		#Randomly place events out of order (will pass them on later)
		elif rand <= 0.1:
			self.entities.append(entity)
		#Else, send it on as normal
		else:
			self.send(entity)


	def finalize(self):
		#Send on the entities that were supposed to be out of order
		while self.entities:
			rand = random.randrange(0, len(self.entities))
			self.send(self.entities.pop(rand))
			
		print "Data stream is now screwed up."

class error_detect(filtering.Filter):
    """Detects errors in the datastream.
        Currently can only detect holes and out-of-order, but can be added onto."""
     
    expected_parameters = {
        "hole" : {
            "types" : "boolean",
            "doc" : "Whether or not to check for holes",
            "default" : True
        },
        "order" : {
            "types" : "boolean",
            "doc" : "Whether or not to check for holes",
            "default" : True
        },
        "order_key" : {
            "types" : "string",
            "doc" : "Time units to order by",
            "default" : "tsc"
        },
        "output" : {
            "types" : "string",
            "doc" : "Output file to send error information",
            "default" : "-",
        }
    }
        
    def initialize(self):
        if self.params["output"] == "-":
            self.outfile = sys.stdout
                
        self.hole = self.params["hole"]
        self.order = self.params["order"]
        self.key = self.params["order_key"]
            
        self.entities = []
        self.vals = {}
        self.max_seen = {}
        self.count = 0
        
    def process(self, entity):
        #If we are checking for holes
        if self.hole:
            #get sequence number and clocksource
            seqtime = entity.get_time_object("log", "sequence")
            seq = seqtime.get_value()
            fname = seqtime.get_clocksource()
                
            #Create dictionaries of sequence numbers
            if seq > 1:
                if fname not in self.vals:
                    self.vals[fname] = [seq]
                    self.max_seen[fname] = seq
                else:
                    #max_seen[fname] contains highest sequence number for fname
                    if seq > self.max_seen[fname]:
                        self.max_seen[fname] = seq
                    self.vals[fname].append(seq)
        #If we are checking for order
        if self.order:
            self.entities.append(entity)
            self.count = self.count + 1
                
        #Pass entity through pipeline
        self.send(entity)
            
    def finalize(self):
        #If we are checking for holes
        if self.hole:
            for fname in self.vals:
			#Sort by sequence number
			self.vals[fname].sort()

			for i in range(2, self.max_seen[fname]+1):
				s = self.vals[fname][0]
				#Is the sequence number correct?
				if s == i:
					#If it is, remove correct data
					self.vals[fname] = self.vals[fname][1:]
				else:
					#If not, there must be hole
					self.outfile.write("Missing entity sequence number "+`i`+
							" for "+fname + "\n")
                        
        #If we are checking for order
        if self.order:
            for count in range(0, self.count - 2):
                if self.entities[count+1].get_log_time()[self.key].get_value() < self.entities[count].get_log_time()[self.key].get_value():
                    stri = "Out of order data " + `self.entities[count]` + " at time " + \
                            `self.entities[count].get_log_time()[self.key].get_value()` + "\n"
                    self.outfile.write(stri)
        #Close output file
        if self.outfile != sys.stdout:
            self.outfile.close()


class hole_seq(filtering.Filter):
	"""Checks for a hole in the datastream by sequence numbers.

	   Prints out warning if there is. """

	def initialize(self):
		self.vals = {}
		self.max_seen = {}

	def process(self, entity):
		seqtime = entity.get_time_object("log","sequence")
		seq = seqtime.get_value()
		fname = seqtime.get_clocksource()

		#Create dictionaries of sequence numbers
		if seq > 1:
			if fname not in self.vals:
				self.vals[fname] = [seq]
				self.max_seen[fname] = seq
			else:
				# max_seen[fname] contains highest sequence number for fname
				if seq > self.max_seen[fname]:
					self.max_seen[fname] = seq
				self.vals[fname].append(seq)
		#Pass the entity through the pipeline
		self.send(entity)


	def finalize(self):
		for fname in self.vals:
			#Sort by sequence number
			self.vals[fname].sort()

			for i in range(2, self.max_seen[fname]+1):
				s = self.vals[fname][0]
				#Is the sequence number correct?
				if s == i:
					#If it is, remove correct data
					self.vals[fname] = self.vals[fname][1:]
				else:
					#If not, there must be hole
					self.warn("Missing entity sequence number "+`i`+
							" for "+fname)


class order_time(filtering.Filter):
	"""Determines if the datastream is in order according to time."""

	#I'm not sure if I should do it in place, may be more efficient at the end

	expected_parameters = {
		"sort_key" : {
			"types": "string",
			"doc" : "Time units to order by",
			"default": "tsc"
		},
		"num_prev" : {
			"types": "integer",
			"doc" : "The number of previous entities to output",
			"default": 10
		},
	}


	def initialize(self):
		self.entities = []
		self.key = self.params["sort_key"]

		self.prev = self.params["num_prev"]
		self.count = 0


	def process(self, entity):
		#Add entity to list of entities
		self.entities.append(entity)
		self.count = self.count + 1

		#Need to determine how to output the bad data properly. Currently just outputting the single out of order data at the end.
		"""
		#If the most recent entity occurred earlier than the previous one, output the most recent data
		#FIXME: Consider issue of multiple out of order entities in a row--output could be confusing
		#this is a dirty fix with count
		if self.count > 1:
			if self.entities[-1].get_log_time()[self.key].get_value() < self.entities[-2].get_log_time()[self.key].get_value():
				if self.count - self.prev >= 1:
					li = self.entities[-1 - self.prev:]
				else:
					li = self.entities[:]
				self.warn("Out of order data and two previous events: " +`li` +
					" at time " + `self.entities[-1].get_log_time()[self.key].get_value()`)"""
		self.send(entity)

	def finalize(self):
		for count in range(0, self.count - 2):
			if self.entities[count+1].get_log_time()[self.key].get_value() < self.entities[count].get_log_time()[self.key].get_value():
				stri = "Out of order data  " + `self.entities[count]` + " at time " + \
					   `self.entities[count].get_log_time()[self.key].get_value()`
				print stri
