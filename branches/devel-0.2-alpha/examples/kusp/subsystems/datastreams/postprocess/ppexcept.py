class PostprocessException(Exception):
	pass

class ConstructionException(PostprocessException):
	"""exceptions that happen when constructing the pipelines"""
	pass

class PipelineException(PostprocessException):
	pass

class InputSourceException(PostprocessException):
	pass

class FilterException(PostprocessException):
	pass

class InterlinkException(PostprocessException):
	pass

class UnknownModuleException(PostprocessException): 
	pass

class UnknownFilterException(PostprocessException): 
	pass

class FilterVerifyException(Exception):
	"""raise when filter instantiated with invalid parameters"""
	pass
