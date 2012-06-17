from .. import Encoding
from . import Command, DEVICE_TYPE



class NodeDiscover(Command):
	def __init__(self, **kwargs):
		Command.__init__(self, Command.NAME.ND, **kwargs)

	def parseParameter(self, p):
		self.setParameter(ParseNodeDiscover(p))



def ParseNodeDiscover(s):
	"""
	Parse out the fields of a node-discovery (ND) response.
	"""
	d = {}
	i = 0
	n = len(s)

	# field (num bytes)

	# network Address (2)
	d['MY'] = Encoding.StringToNumber(s[i:i+2])
	i = i + 2

	# serial high (4)
	# serial low (4)
	serial = Encoding.StringToNumber(s[i:i+4])
	i = i + 4
	serial = serial * Encoding.BYTE_BASE**4
	serial = serial + Encoding.StringToNumber(s[i:i+4])
	i = i + 4
	d['SERIAL'] = serial

	# node identifier string (null-terminated)
	nameEnd = i
	while nameEnd < n and s[nameEnd] != chr(0):
		nameEnd = nameEnd + 1
	d['NI'] = s[i:nameEnd]
	i = nameEnd + 1

	# parent network address (2)
	d['PARENT_NETWORK ADDRESS'] = Encoding.StringToNumber(s[i:i+2])
	i = i + 2

	# device type (1)
	deviceType = Encoding.StringToNumber(s[i:i+1])
	d['DEVICE_TYPE'] = DEVICE_TYPE[deviceType]
	i = i + 1

	# status, "Reserved" (1)
	d['STATUS'] = Encoding.StringToNumber(s[i:i+1])
	i = i + 1

	# profile ID (2)
	d['PROFILE_ID'] = Encoding.StringToNumber(s[i:i+2])
	i = i + 2

	# manufacturer ID (2)
	d['MANUFACTURER_ID'] = Encoding.StringToNumber(s[i:i+2])
	i = i + 2

	return d

