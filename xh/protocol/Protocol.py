"""
Convert to/from XBee API protocol values.
"""

__all__ = [
	'ParseCommandFromDict',
]

import logging
log = logging.getLogger('Protocol')

from .. import Encoding, EnumUtil, deps
from deps import Enum
from . import Command, InputVolts, NodeDiscover


DEVICE_TYPE = Enum(
	'COORDINATOR',	# must be index 0
	'ROUTER',	# 1
	'END_DEVICE',	# 2
)


# map from Command.NAME to the associated class
COMMAND_CLASSES = {
	Command.NAME.__getattribute__('%V'): InputVolts,
	Command.NAME.ND: NodeDiscover,
}


def ParseCommandFromDict(d):
	"""
	Parse common fields from a response dict and create a Command of the
	appropriate class.
	"""
	frameId = Encoding.PrintedStringToNumber(
		d[str(Command.FIELD.frame_id)])

	name = EnumUtil.FromString(Command.NAME, d['command'])

	status = d.get(str(Command.FIELD.status))
	if status is not None:
		status = Command.STATUS[Encoding.StringToNumber(status)]

	commandClass = COMMAND_CLASSES.get(name)
	if commandClass:
		c = commandClass(frameId=frameId)
	else:
		c = Command(name, frameId=frameId)
	c.mergeFromDict(d)
	return c

