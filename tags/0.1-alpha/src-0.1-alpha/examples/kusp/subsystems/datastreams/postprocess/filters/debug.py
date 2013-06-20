from datastreams.postprocess import filtering
from datastreams import namespaces

class debug(filtering.Filter):
	def process(self, entity):
		ed = self.namespace.get_entity_spec(entity.get_cid())
		
		print entity.get_family_name(), entity.get_name(), entity.get_cid(),entity.get_nanoseconds(),
		
		if entity.get_type() == namespaces.EVENTTYPE:
			print entity.get_tag(), entity.get_extra_data()
		else:
			print
		self.send(entity)

