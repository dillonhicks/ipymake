from datastreams.postprocess import filtering
from datastreams.postprocess import entities
from datastreams import namespaces

class graph(filtering.Filter):

	def initialize(self):
		self.cptr = self.get_ns_pointer("BP_PIPELINE/MSG_CONSUMED")
		self.pipelines = {}
		self.min_ts = None
		self.max_ts = None
		self.max_message_id = None

	def process(self, entity):
		if entity.get_cid() != self.cptr.get_cid():
			return

		d = entity.get_extra_data()
		pipeline_id = d['pipeline_id']
		message_id = d['message_id']

		if not self.pipelines.has_key(pipeline_id):
			self.pipelines[pipeline_id] = []

		log_time = entity.get_log_time()['tsc'].get_value()
		log_time = log_time / 100000

		if self.min_ts == None:
			self.min_ts = log_time
		elif log_time < self.min_ts:
			self.min_ts = log_time

		log_time = log_time - self.min_ts
		if self.max_ts == None:
			self.max_ts = log_time
		elif log_time > self.max_ts:
			self.max_ts = log_time

		if self.max_message_id == None:
			self.max_message_id = message_id
		elif message_id > self.max_message_id:
			self.max_message_id = message_id

		self.pipelines[pipeline_id].append((log_time, message_id))

	def finalize(self):
		gf = open("pipelines.gnu", 'w')
		gf.write("set terminal png transparent nocrop enhanced font arial 8 size	420,320\n")
		gf.write("set output \"pipelines.png\"\n")
		gf.write("set xlabel \"Time\"\n")
		gf.write("set ylabel \"Frames Processed\"\n")
		gf.write("plot [0:%d][0:%d] \\\n" % (self.max_ts, self.max_message_id))

		key_count = 0
		num_keys = len(self.pipelines.keys())
		for pipeline_id in self.pipelines:
			fn = "pipeline-%d.gnuplot.dat" % (pipeline_id,)

			key_count = key_count + 1
			if key_count == num_keys:
				gf.write("\"%s\" title \"pipe-%d\" with steps\n" % (fn,pipeline_id))
			else:
				gf.write("\"%s\" title \"pipe-%d\" with steps,\\\n" % (fn, pipeline_id))

			pf = open(fn, 'w')
			for ts, mid in self.pipelines[pipeline_id]:
				pf.write("%d %d\n" % (ts, mid))
			pf.close()

		gf.close()
