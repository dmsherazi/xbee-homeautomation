#!/usr/bin/python
"""%prog command [options]
Issue commands to or read data from the XBee Home Automation system.
Examples:
 $ xh info # print information about a physically connected XBee
 $ xh init # initialize network PANID and encryption key
 $ xh setup --name 'Living Room' # set up and name a new sensor/control
"""

import logging
log = logging.getLogger('xh')

import sys, os, time, optparse
import xh
from xh.deps import serial, xbee

from serial.tools import list_ports
EXCLUDE_DEVICES = 'Bluetooth' # ignore in finding Serial ports

def getSerialCandidates():
	candidates = [d[0] for d in list_ports.comports()
		if EXCLUDE_DEVICES not in d[0]]
	if not candidates:
		raise RuntimeError('No candidates for serial devices found.')
	return candidates

def pickSerialDevice():
	serialDevices = getSerialCandidates()
	log.info('Found serial devices: %s' % serialDevices)
	if len(serialDevices) > 1:
		print 'Select serial device:'
		for i, device in enumerate(serialDevices):
			print '%d\t%s' % (i, device)
		iStr = raw_input('Number: ')
		i = int(iStr)
	else:
		i = 0
	return serialDevices[i]

log.info('started')
log.info('Type control-C to exit.')

def logData(rawData):
	try:
		command = xh.protocol.ParseCommandFromDict(rawData)
		log.info('received %s' % command)
	except:
		log.error('could not deal with data', exc_info=True)

try:
	xb = None
	serialDevice = pickSerialDevice()
	s = serial.Serial(serialDevice, xh.Config.SERIAL_BAUD)
	xb = xbee.XBee(s, callback=logData)
	log.info('Created XBee object.')
	for i, cmd in enumerate([
		#'MY', # node's network ID (0 for coordinator)
		'ID', # network ID
		#('ID', '\x3E\xF7'), # set network ID to 0x3EF7
		#('KY', '\x32\x10'), # set network key to 0x3210
		#('KY', xh.Encoding.NumberToString(xh.Config.LINK_KEY)),
		#'WR', # write network key
		#'EE', # encryption enable (0 or 1)
		#'SH', # serial (high bits)
		#'SL', # serial (low bits)
		#'NI', # string node name
		'%V', # Vcc voltage, value * 1200/1024.0 = mV
		'NT', # discovery timeout
		'ND'] # node discover
	):
		frameId = '%X' % i
		parameter = None
		if type(cmd) is tuple:
			cmd, parameter = cmd
		log.info('Sending %s with frame ID %s%s' %
			(cmd, frameId,
			(parameter and ' and parameter %s' % parameter) or ''))
		xb.at(command=cmd, frame_id=frameId, parameter=parameter)
	while True:
		time.sleep(0.02)
except KeyboardInterrupt as e:
	log.info('Got ^C.')
except Exception as e:
	log.error(e.message, exc_info=True)
finally:
	if xb:
		xb.halt()

log.info('exiting')
