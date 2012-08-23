#!/usr/bin/python
import argparse

parser = argparse.ArgumentParser(
formatter_class=argparse.RawDescriptionHelpFormatter,
description="""
Issue commands to or read data from the XBee Home Automation system.
Examples:
 $ %(prog)s run # attach to the pysically connected Xbee and run plugins
 $ %(prog)s list # list information about available Xbees and plugins
 $ %(prog)s setup --plugin 'Temperature Logger' --serial 0x1a23
"""
)

import logging
log = logging.getLogger('xh')

import code, time, os
import xh
from xh.deps import Enum, serial, xbee
from xh.protocol import *
from yapsy.PluginManager import PluginManagerSingleton

LOCAL_SCRIPT = os.path.join(os.path.dirname(__file__), 'xh.local.py')
FRAME_LOGGER_NAME = 'Frame Logger'

COMMAND = Enum(
	'list',
	'run',
	'setup',
)
parser.add_argument('command', choices=[str(c) for c in COMMAND])


def runLocalScript():
	if os.path.isfile(LOCAL_SCRIPT):
		log.info('running %s' % LOCAL_SCRIPT)
		execfile(LOCAL_SCRIPT)
	else:
		log.info('no local script to run at %s' % LOCAL_SCRIPT)


def getFrameLoggerPlugin():
	pm = PluginManagerSingleton.get()
	p = pm.getPluginByName(FRAME_LOGGER_NAME)
	return p.plugin_object


INTERACT_BANNER = ('The xbee object is available as "xb". A received frame list'
	+ ' is available from the Frame Logger plugin, available as "fl".'
	+ ' Type control-D to exit.')


def run():
	log.debug('collecting plugins')
	xh.SetupUtil.CollectPlugins()
	fl = getFrameLoggerPlugin()
	xh.SetupUtil.SetLoggerRedisplayAfterEmit(logging.getLogger())
	with xh.SetupUtil.InitializedXbee() as xb:
		log.info('connected to locally attached Xbee')
		xh.protocol.Command.SetXbeeSingleton(xb)
		with xh.SetupUtil.ActivatedPlugins():
			log.info('started')

			runLocalScript()

			xh.SetupUtil.RunPythonStartup()
			namespace = globals()
			namespace.update(locals())
			code.interact(banner=INTERACT_BANNER, local=namespace)

	log.info('exiting')


def list():
	with xh.SetupUtil.InitializedXbee() as xb:
		xh.protocol.Command.SetXbeeSingleton(xb)

		global nTimeoutMillis
		nTimeoutMillis = None
		nt = xh.protocol.NodeDiscoveryTimeout()
		id = nt.getFrameId()
		def recordNtCb(sender=None, signal=None, frame=None):
			global nTimeoutMillis
			if (hasattr(frame, 'getFrameId')
			and frame.getFrameId() == id):
				nTimeoutMillis = frame.getTimeoutMillis()
		xh.Signals.FrameReceived.connect(recordNtCb)
		nt.send()
		maxWaits = 20
		waitNum = 0
		while nTimeoutMillis is None:
			waitNum += 1
			if waitNum > maxWaits:
				log.error('timed out waiting for NT')
				return
			time.sleep(0.1)
		xh.Signals.FrameReceived.disconnect(recordNtCb)
		log.debug('Node discovery timeout is %dms.' % nTimeoutMillis)

		global nodeInfoList
		nodeInfoList = []
		nd = xh.protocol.NodeDiscover()
		id = nd.getFrameId()
		def recordNdCb(sender=None, signal=None, frame=None):
			global nodeInfoList
			if (hasattr(frame, 'getFrameId')
			and frame.getFrameId() == id):
				nodeInfoList.append(frame.getNodeId())
		xh.Signals.FrameReceived.connect(recordNdCb)
		nd.send()
		time.sleep(nTimeoutMillis/1000.0)
		xh.Signals.FrameReceived.disconnect(recordNdCb)
		log.info('Nodes:\n%s' %
			'\n'.join(['\t%s' % n for n in nodeInfoList]))


def setup():
	raise NotImplementedError()


COMMAND_TO_FN = {
	COMMAND.run: run,
	COMMAND.list: list,
	COMMAND.setup: setup,
}


def main():
	args = parser.parse_args()
	command = xh.EnumUtil.FromString(COMMAND, args.command)
	with xh.Config():
		log.debug('opened config')
		COMMAND_TO_FN[command]()


main()
