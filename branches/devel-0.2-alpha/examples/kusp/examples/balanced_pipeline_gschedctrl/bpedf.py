import struct

def pipeline_dd(binary):
	d = struct.unpack("ii", binary)
	return {'pipeline_id': d[0], 'message_id': d[1]}
