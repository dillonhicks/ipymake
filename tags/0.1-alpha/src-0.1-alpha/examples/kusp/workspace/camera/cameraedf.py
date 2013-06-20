import struct

def camera_command(binary):
	length = len(binary)	
	format=`length`+"s"
	string = struct.unpack(format,binary)
	string = string[0].split(" ")
	return string
