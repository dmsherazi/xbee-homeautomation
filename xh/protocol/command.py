import logging
import threading

from .. import encoding, enumutil
from ..deps import Enum
from . import Frame, FrameRegistry, Registry


log = logging.getLogger('Command')



class Command(Frame):
	# The fields expected to be in a command dict.
	FIELD = Enum(
		# sequence; packed number
		'frame_id',

		# command name; ascii
		'command',

		# value sent with or received from command; packed number
		'parameter',

		# status code; packed number
		'status',

		# 16-bit network address of the responder for remote commands
		'source_addr',

		# 64-bit
		'source_addr_long',
	)


	# Recognized command names (alphabetized).
	NAME = Enum(
		'%V', # InputVolts (voltage level on Vcc pin)
		'D0', # configure IO pin DIO0 / AD0 / COMM
		'D1', # configure IO pin DIO1 / AD1
		'D2', # configure IO pin DIO2 / AD2
		'D3', # configure IO pin DIO3 / AD3
		'D4', # configure IO pin DIO4
		'D5', # configure IO pin DIO5 / ASSOC
		'D6', # configure IO pin DIO6 / RTS
		'D7', # configure IO pin DIO7 / CTS
		# 'D8', # configure IO pin DIO8: not yet supported acc. docs
		'EE', # encryption enable (0 or 1)
		'ID', # network id
		'IR', # IO sample rate (see SampleRate)
		'IS', # force sample on all digital, analog inputs
		'KY', # xh.encoding.NumberToString(xh.Config.LINK_KEY)
		'MY', # node's network ID (0 for coordinator)
		'ND', # NodeDiscover
		'NI', # string node name
		'NT', # discover timeout
		'P0', # configure IO pin DIO10 / PWM / RSSI
		'P1', # configure IO pin DIO11
		'P2', # configure IO pin DIO12
		# 'P3', # configure IO pin DIO13: not yet supported acc. docs
		'PO', # polling rate
		'PR', # PullUpResistor (bit field for internal resistors)
		'SH', # serial (high bits)
		'SI', # sleep immediately
		'SL', # serial (low bits)
		'SM', # SleepMode
		'SN', # NumberOfSleepPeriods
		'SO', # sleep options
		'SP', # SleepPeriod
		'ST', # TimeBeforeSleep
		'V+', # voltage supply monitoring (threshold for vcc sampling)
		'WH', # WakeHostTimer
		'WR', # write configuration to non-volatile memory
	)


	# Response status.
	STATUS = Enum(
		'OK',			# must be index 0
		'ERROR',		# 1
		'INVALID_COMMAND',	# 2
		'INVALID_PARAMETER',	# 3
		'TRANSMIT_FAILURE',	# 4
	)


	# max frame ID (must fit in 1 byte)
	_MAX_FRAME_ID = 255
	_MIN_FRAME_ID = 1
	# next unclaimed frame ID for a command to send
	__sendingFrameId = _MIN_FRAME_ID
	__frameIdLock = threading.Lock()

	# For sending, keep an Xbee object singleton and make thread-safe.
	_XbeeSingleton = None
	__xbeeSingletonLock = threading.Lock()


	def __init__(self, name, responseFrameId=None, dest=None,
		fromCommandName=None):
		"""
		@param dest 64-bit destination address. If given, this Command
			will be sent to the given remote note.
		@param fromCommandName for subclasses: the Command.NAME value
			parsed from the API dict (probably the same as @param
			name)
		"""
		if responseFrameId is None:
			frameType = Frame.TYPE.at
		else:
			frameType = Frame.TYPE.at_response

		if dest is not None:
			if frameType is not Frame.TYPE.at:
				raise ValueError('cannot set dest for response')

		Frame.__init__(self, frameType=frameType)

		self.__remoteNetworkAddress = None
		self.__remoteSerial = None

		if responseFrameId is None:
			with Command.__frameIdLock:
				next = Command.__sendingFrameId
				self.__frameId = next
				next += 1
				if (next > Command._MAX_FRAME_ID):
					next = Command._MIN_FRAME_ID
				Command.__sendingFrameId = next
			if dest is not None:
				self.__remoteSerial = int(dest)
		else:
			self.__frameId = int(responseFrameId)

		if name not in Command.NAME:
			raise ValueError('Name "%s" not in NAME enum.' % name)
		self.__name = name
		self.__parameter = None
		self.setStatus(None)


	def getFrameId(self):
		return self.__frameId


	def getName(self):
		return self.__name


	def isRemote(self):
		return self.getRemoteSerial() is not None


	def getRemoteNetworkAddress(self):
		return self.__remoteNetworkAddress


	def getRemoteSerial(self):
		return self.__remoteSerial


	def setStatus(self, status):
		if not (status is None or status in Command.STATUS):
			raise ValueError(
				'Status "%s" not None or in STATUS enum.'
				% status)
		self.__status = status


	def getStatus(self):
		return self.__status


	def setParameter(self, parameter):
		self.__parameter = parameter


	def getParameter(self):
		return self.__parameter


	def getNamedValues(self, includeParameter=True):
		d = Frame.getNamedValues(self)
		d.update({
			'remoteAddr': self.getRemoteNetworkAddress(),
			'remoteSerial': self.getRemoteSerial(),
		})
		if includeParameter:
			d.update({'parameter': self.getParameter()})
		return d


	def __str__(self):
		status = self.getStatus()
		namedStrings = {
			'id': self.getFrameId(),
			'name': self.getName(),
			'status': status and (' (%s)' % status) or '',
			'param': self._FormatNamedValues(self.getNamedValues()),
		}
		return ('#%(id)d %(name)s%(status)s%(param)s'
			% namedStrings)


	def _updateFromDict(self, d, usedKeys):
		"""
		Parse status, parameter, and any class-specific fields from a
		response dict.
		"""
		Frame._updateFromDict(self, d, usedKeys)

		statusKey = str(Command.FIELD.status)
		status = d.get(statusKey)
		if status is not None:
			status = Command.STATUS[encoding.StringToNumber(status)]
			self.setStatus(status)
			usedKeys.add(statusKey)

		paramKey = str(Command.FIELD.parameter)
		parameter = d.get(paramKey)
		if parameter is not None:
			self.parseParameter(parameter)
			usedKeys.add(paramKey)

		srcKey = str(Command.FIELD.source_addr)
		src = d.get(srcKey)
		if src is not None:
			self.__remoteNetworkAddress = (
				encoding.StringToNumber(src))
			usedKeys.add(srcKey)

			srcLongKey = str(Command.FIELD.source_addr_long)
			self.__remoteSerial = encoding.StringToNumber(
				d[srcLongKey])
			usedKeys.add(srcLongKey)


	def parseParameter(self, encoded):
		"""
		Parse the Command's response parameter into specific datum/data
		for the Command subclass. By default, parsed as a single number.
		@param encoded byte string from the API
		"""
		self.setParameter(self._parseParameterDefault(encoded))


	def _parseParameterDefault(self, encoded):
		"""
		By default, parse a parameter as a packed number. Warn if the
		command may not actually have a numeric parameter.
		@return The parameter parsed as a number.
		"""
		parameter = encoding.StringToNumber(encoded)
		if self.getName() not in (
			Command.NAME.__getattribute__('%V'),
			Command.NAME.ID,
			Command.NAME.MY,
			Command.NAME.NI,
			Command.NAME.NT,
			Command.NAME.SH,
			Command.NAME.SL,
		):
			log.warning(('uncertain conversion of encoded parameter'
				+ ' "%s" to number 0x%X for command %s')
				% (encoded, parameter, self.getName()))
		return parameter


	@classmethod
	def SetXbeeSingleton(cls, xb):
		cls._XbeeSingleton = xb


	def send(self, xb=None):
		"""
		Send this Command.
		@param xb The Xbee API object to use to send the Command. If not
			provided, tries to send using the Xbee singleton.
		To use the Xbee singleton, it must have been set using
		setXbeeSingleton. If the singleton is used, a lock is acquired
		around sending (and this method is thread-safe), otherwise the
		caller is responsible for thread safety.
		"""
		log.debug('sending %s' % self)

		if xb is None:
			if Command._XbeeSingleton is None:
				raise RuntimeError('No xb kwarg provided to '
					+ 'send and Xbee singleton not set '
					+ '(see setXbeeSingleton).')
			senderXbee = Command._XbeeSingleton
		else:
			senderXbee = xb

		kwargs = {
			'command': str(self.getName()),
			'frame_id': self._encodedFrameId(),
			'parameter': self._encodedParameter(),
		}
		if self.isRemote():
			kwargs['dest_addr_long'] = (
				encoding.NumberToSerialString(
					self.getRemoteSerial()))
			sendFn = senderXbee.remote_at
		else:
			sendFn = senderXbee.at

		if senderXbee is Command._XbeeSingleton:
			with Command.__xbeeSingletonLock:
				sendFn(**kwargs)
		else:
			sendFn(**kwargs)


	def _encodedFrameId(self):
		return encoding.NumberToString(self.getFrameId())


	def _encodedParameter(self):
		p = self.getParameter()
		if p is None:
			return None
		else:
			return encoding.NumberToString(p)


	@classmethod
	def _CreateFromDict(cls, d, usedKeys):
		frameIdKey = str(Command.FIELD.frame_id)
		frameId = d.get(frameIdKey)
		frameId = encoding.StringToNumber(d[frameIdKey])
		usedKeys.add(frameIdKey)

		nameKey = str(Command.FIELD.command)
		name = d.get(nameKey)
		if name is not None:
			name = enumutil.FromString(Command.NAME, name)
			usedKeys.add(nameKey)

		commandClass = CommandRegistry.get(name)
		if commandClass:
			c = commandClass(responseFrameId=frameId,
				fromCommandName=name)
		else:
			c = Command(name, responseFrameId=frameId)

		return c



CommandRegistry = Registry(Command.NAME)
CommandRegistry.__doc__ = ('Which Command.NAME is to be parsed '
	+ 'by which Command subclass.')



FrameRegistry.put(Frame.TYPE.at_response, Command)
FrameRegistry.put(Frame.TYPE.remote_at_response, Command)
