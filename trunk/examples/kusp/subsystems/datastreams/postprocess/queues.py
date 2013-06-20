
import Queue

class PostprocessQueue(Queue.Queue):
	def receive(self, entity):
		self.put(entity)

	def startup(self):
		pass
