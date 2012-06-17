"""
Conversion functions to pack/unpack values for XBee API communication.
"""

BYTE_BASE = 0x100
MILLIVOLTS_PER_VOLT = 1e-3

def NumberToPrintedString(n):
	"""
	Pack a number as a printed, hex-formatted string.
	"""
	return '%x' % n

def NumberToString(n):
	"""
	Pack a number of arbitrary size into (little-endian) a string.
	Example: 0x3ef7 => '\x3e\xf7'
	"""
	s = ''
	while n > 0:
		lowByte = n % BYTE_BASE
		s = chr(lowByte) + s
		n = n / BYTE_BASE
	return s

def PrintedStringToNumber(s):
	"""
	Unpack a %s-formatted number. (Try to return an int, then a float.)
	Example: '3' => 3 or '2.2' => 2.2
	"""
	try:
		return int(s)
	except ValueError, e:
		return float(s)

def StringToNumber(s):
	"""
	Unpack a (little-endian) string to a number.
	Example: '>\xf7' => 0x3ef7 or '\n\xe4' => 2788 (0x0ae4)
	"""
	n = 0
	for c in s:
		n *= BYTE_BASE
		n += ord(c)
	return n

def StringToVolts(s):
	"""
	Unpack a string to a number, and convert that number to volts on
	an analog input pin.
	"""
	return StringToNumber(s) * (1200.0 / 1024.0) * MILLIVOLTS_PER_VOLT

