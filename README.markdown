XBee Home Automation
====================

Tools for XBee-based sensor/control networks, with an emphasis on ease of setup, extensability, and ability to integrate with existing systems.

Examples
--------

Connect to the attached XBee, start plugins, and run a Python interpreter from which commands may be interactively sent to the local or remote XBees:

	$ xh.py run
	The xbee object is available as "xb". A received frame list is
	available from the Frame Logger plugin, available as "fl".
	Type control-D to exit.
	>>> xh.protocol.InputVolts().send()
	[INFO FrameLogger] received #1 %V (OK) volts=3.2390625
	>>> xh.protocol.InputSample(dest=0x13a200abcd1234).send()
	[INFO FrameLogger] received #2 IS (OK) remoteSerial=0x13a200abcd1234
	options=ACKNOWLEDGED samples=[AnalogSample(AD0, volts=0.002),
	AnalogSample(AD1, volts=0.166)] remoteAddr=0x372
	>>> ^D
	[INFO xh] exiting

Print information about a connected XBees and installed plugins:

	$ xh.py list
	[INFO xh] Plugins:
		Frame Logger (FrameLogger/) Log all received frames using the
		Python logging module.
		Temperature Logger (temperaturelogger/) Log temperature (and
		other) values from a sensing module. XBee 0x13a200abcd1234
	[INFO xh] XBees:
		NodeId status=0x0 NI='Attic' manufacturerId=0x101e
		addr=0x49b9 parentAddr=0xfffe deviceType=ROUTER profileId=0xc105
		serial=0x13a200ccdd0011
		NodeId status=0x0 NI='Living Room' manufacturerId=0x101e
		addr=0x372 parentAddr=0xfffe deviceType=ROUTER profileId=0xc105
		serial=0x13a200abcd1234

External Dependencies
---------------------

* Python >= 2.7 (uses argparse, introduced in 2.7)
* [Enum](http://pypi.python.org/pypi/enum/) for enumerations

Included Dependencies
---------------------

These dependencies are included as [git submodules](http://git-scm.com/book/en/Git-Tools-Submodules). After cloning (or when pulling to your clone of) this repository, use `git submodule update --init` to sync all the submodules.

* [pySerial](http://pyserial.sourceforge.net/) for communication over serial USB with the XBee device, using submodule [forked on github](https://github.com/makerbot/pyserial)
* [pysignals](https://github.com/theojulienne/PySignals) for decoupled communication (to and among plugins), using submodule [forked on github](https://github.com/markfickett/PySignals)
* [python-xbee](http://code.google.com/p/python-xbee/downloads/list) for low-level API-mode communication with the XBee device, using submodule [forked on github](https://github.com/markfickett/python-xbee)
* [Yapsy](http://sourceforge.net/projects/yapsy/) for plugin loading, using submodule [forked on github](https://github.com/markfickett/yapsy)


Related Work
------------
* [Indigo](http://www.perceptiveautomation.com/indigo/index.html) home automation server for Mac/iOS with Python plugins
* [INSTEON](http://www.insteon.net/products-home.html) home automation devices
* Digi
    * [XBee project gallery](http://www.idigi.com/blog/community/xbee-project-gallery/)
    * [XBee examples and guides](http://examples.digi.com/)
    * [Digi sensor modules](http://www.digi.com/wiki/developer/index.php/XBee_Sensors)
    * [iDigi Dia](http://www.digi.com/wiki/developer/index.php/IDigi_Dia_Wiki), a Python-based control / data-collection framework to run on Digi gateways ([example code](http://www.digi.com/wiki/developer/index.php/Google_Gadget_LTH_Sensor_Example))
* [Home Automation project by Arvis Cimermanis](http://www.arvisc.info/) using XBee
* [KillerBee](http://code.google.com/p/killerbee/) framework for expliting/attacking ZigBee networks
