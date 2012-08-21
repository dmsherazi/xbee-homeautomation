__all__ = [
	'Data',

	'Sample',
	'AnalogSample',
	'DigitalSample',
]

import logging
log = logging.getLogger('xh.protocol.Data')

from ..deps import Enum
from .. import Encoding, EnumUtil
from . import Frame, FrameRegistry, PIN, Registry
import datetime



class Data(Frame):
	FIELD = Enum(
		'source_addr',
		'source_addr_long',
		'samples',
	)


	# Ex: '2012 Jun 17 23:24:18 UTC'
	DATETIME_FORMAT = '%Y %b %d %H:%M:%S UTC'


	def __init__(self, setTimestampToNow=True):
		Frame.__init__(self, frameType=Frame.TYPE.rx_io_data_long_addr)
		self._sourceAddress = None
		self._sourceAddressLong = None
		self._samples = []
		if setTimestampToNow:
			self.setTimestampToNow()
		else:
			self._timestamp = None


	def setTimestampToNow(self):
		self._timestamp = datetime.datetime.utcnow()


	def getTimestamp(self):
		"""
		@return the UTC creation timestamp of the sample data
		"""
		return self._timestamp


	def formatTimestamp(self):
		return datetime.datetime.strftime(
			self.getTimestamp(), self.DATETIME_FORMAT)


	def getSourceAddress(self):
		return self._sourceAddress


	def getSourceAddressLong(self):
		return self._sourceAddressLong


	def getSamples(self):
		return list(self._samples)


	def getNamedValues(self):
		d = Frame.getNamedValues(self)
		samples = self.getSamples()
		if not samples:
			samples = None
		d.update({
			'sourceAddress': self.getSourceAddress(),
			'sourceAddressLong': self.getSourceAddressLong(),
			'samples': samples,
		})
		return d


	def __str__(self):
		s = 'data'
		t = self.getTimestamp()
		if t is None:
			t = ''
		else:
			t = ' ' + self.formatTimestamp()
		return '%s%s%s' % (s, t,
			self._FormatNamedValues(self.getNamedValues()))


	@classmethod
	def _CreateFromDict(cls, d, usedKeys):
		data = cls()

		sourceAddrKey = str(cls.FIELD.source_addr)
		data._sourceAddress = Encoding.StringToNumber(d[sourceAddrKey])
		usedKeys.add(sourceAddrKey)

		sourceAddrLongKey = str(cls.FIELD.source_addr_long)
		data._sourceAddressLong = Encoding.StringToNumber(
			d[sourceAddrLongKey])
		usedKeys.add(sourceAddrLongKey)

		samplesKey = str(cls.FIELD.samples)
		data._samples = []
		for sd in d[samplesKey]:
			data._samples += Sample.CreateFromDict(sd)
		usedKeys.add(samplesKey)

		return data



class Sample:
	PIN_TYPE = Enum(
		'adc',		# analog sample
		'dio',		# digital sample
	)
	_Registry = Registry(PIN_TYPE)


	def __init__(self, pinName):
		if pinName not in PIN:
			raise ValueError('Pin %r not in Constants.PIN Enum.'
				% pinName)
		self.__pinName = pinName


	def getPinName(self):
		return self.__pinName


	def __str__(self):
		return '%s(%s, %s)' % (
			self.__class__.__name__,
			self.getPinName(),
			self._formatValue(),
		)


	@classmethod
	def CreateFromDict(cls, d):
		for key, numericValue in d.iteritems():
			pinTypeStr, pinNum = key.split('-')
			pinNum = int(pinNum)
			pinType = EnumUtil.FromString(cls.PIN_TYPE, pinTypeStr)

			concreteClass = cls._Registry.get(pinType)
			yield concreteClass.CreateFromRawValues(
				pinNum, numericValue)



class AnalogSample(Sample):
	_PIN_NUM_VCC = 7


	def __init__(self, pinName, volts):
		Sample.__init__(self, pinName)
		self.__volts = float(volts)


	def getVolts(self):
		"""
		Get the voltage measured on the sampled analog pin. Note that
		with the exception of VCC, the maximum value ADC pins can sense
		is 1.2v.
		"""
		return self.__volts


	def _formatValue(self):
		return 'volts=%.3f' % self.getVolts()


	@classmethod
	def CreateFromRawValues(cls, pinNum, numericValue):
		if pinNum == cls._PIN_NUM_VCC:
			pinName = PIN.VCC
		else:
			pinName = EnumUtil.FromString(PIN, 'AD%d' % pinNum)
		return cls(pinName, Encoding.NumberToVolts(numericValue))


Sample._Registry.put(Sample.PIN_TYPE.adc, AnalogSample)



class DigitalSample(Sample):
	def __init__(self, pinName, isSet):
		Sample.__init__(self, pinName)
		self.__isSet = bool(isSet)


	def getIsSet(self):
		return self.__isSet


	def _formatValue(self):
		return str(self.getIsSet())


	@classmethod
	def CreateFromRawValues(cls, pinNum, numericValue):
		pinName = EnumUtil.FromString(PIN, 'DIO%d' % pinNum)
		if numericValue in (True, False):
			bit = numericValue
		else:
			bit = Encoding.NumberToBoolean(numericValue)
		return cls(pinName, bit)


Sample._Registry.put(Sample.PIN_TYPE.dio, DigitalSample)



FrameRegistry.put(Frame.TYPE.rx_io_data_long_addr, Data)
