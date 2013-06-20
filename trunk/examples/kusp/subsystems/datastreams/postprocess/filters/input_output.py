from datastreams.postprocess import filtering
from datastreams.postprocess import entities
import datastreams.postprocess.inputs as inputs
from datastreams import namespaces
import cPickle
import pickle
import struct

magic_size = struct.calcsize(inputs.magic_format)

class pickle(filtering.Filter):
    """Pickles an incoming datastream."""

    expected_parameters = {
        "protocol_version" : {
            "types" : "integer",
            "doc" : "Protocol version for pickling (0, 1, or 2)",
            "default" : 0
        },
        "filename" : {
            "types" : "string",
            "doc" : "Filename to pickle datastream to",
            "required" : True
        }
    }

    def initialize(self):
        #Open file, set file as pickle destination
        self.outfile = open(self.params["filename"], "wb")
        
        magicbin = struct.pack(inputs.magic_format,
                inputs.picklemagic)
        
        self.outfile.write(magicbin)
        
        self.outfile = open(self.params["filename"], "wb")

        self.pickler = cPickle.Pickler(self.outfile,
            self.params["protocol_version"])
    

    def process(self, entity):
        #Clear entity's namespace before pickling
        #Why clear namespace first?
        #entity.clear_cache()
        #Pickle entity
        self.pickler.dump(entity)
        #Send entity along pipeline
        self.send(entity)
          

    def finalize(self):
        self.pickler.dump(entities.PipelineEnd())
        self.outfile.close()

    def abort(self):
        self.outfile.close()
        os.remove(self.params["filename"])

class unpickle(filtering.Filter):
    """Unpickles a file."""

    #This is a quick solution--would prefer changing head filter to accomodate
    #pickled binary files
    

    expected_parameters = {
        "filename" : {
            "types" : "string",
            "doc" : "File name to unpickle data from",
            "required" : True
        }
    }

    def initialize(self):
        pass
        
    def process(self, entity):
        pass

    def finalize(self):
        #Open file
        self.infile = open(self.params["filename"], 'rb')
        
        # skip the magic number
        self.infile.read(magic_size)
        
        self.unpickler = cPickle.Unpickler(self.infile)
        entity = self.unpickler.load()
        
        #Get every entity from pickled file and send it along the pipeline
        while (entity.message != entities.PIPELINE_EOF or
				entity.message != entities.PIPELINE_ERROR):
            self.send(entity)
            entity = self.unpickler.load()
        
        self.infile.close()


