"""
Centralized imports and module setup.
"""

import logging
logging.basicConfig(
        format='[%(levelname)s %(name)s] %(message)s',
        level=logging.DEBUG)
import sys, os, time
import optparse

try:
	import serial
except ImportError, e:
	'Required: pySerial from http://pyserial.sourceforge.net/'
	raise e
try:
	import xbee
except ImportError, e:
	'Required: python-xbee from http://code.google.com/p/python-xbee/'
	raise e

import Config
