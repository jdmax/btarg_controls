from pyModbusTCP.client import ModbusClient
from softioc import builder, alarm


class Device():
    """Makes library of PVs needed for the DAT8130 relays and provides methods connect them to the device

    Attributes:
        pvs: dict of Process Variables keyed by name
        channels: channels of device
        new_reads: dict of most recent reads from device to set into PVs
    """

    def __init__(self, device_name, settings):
        '''Make PVs needed for this device and put in pvs dict keyed by name
        '''
        self.device_name = device_name
        self.settings = settings
        self.channels = settings['channels']
        self.pvs = {}
        self.new_reads = {}
        self.calibs = {}
        #sevr = {'HHSV': 'MAJOR', 'HSV': 'MINOR', 'LSV': 'MINOR', 'LLSV': 'MAJOR', 'DISP': '0'}
        sevr = {'DISP': '0'}

        for i, channel in enumerate(
                settings['channels']):  # set up PVs for each channel, calibrations are values of dict
            if "None" in channel: continue
            if i < 4:  # Digital OUT channels first
                self.pvs[channel] = builder.boolOut(channel, on_update_name=self.do_sets)
            else:  # Digital IN next
                self.pvs[channel] = builder.boolIn(channel, **sevr)

    def connect(self):
        '''Open connection to device, read status of outs and set to PVs'''
        try:
            self.t = DeviceConnection(self.settings['ip'], self.settings['port'], self.settings['timeout'])
            self.read_outs()
        except Exception as e:
            print(f"Failed connection on {self.settings['ip']}, {e}")

    def read_outs(self):
        "Read and set OUT PVs at the start of the IOC"
        try:  # set initial out PVs
            values = self.t.read_coils()
            for i, channel in enumerate(self.channels[:4]):  # set all
                if "None" in channel: continue
                self.pvs[self.channels[i]].set(values[i])
        except OSError:
            self.reconnect()

    def reconnect(self):
        print("Connection failed. Attempting reconnect.")
        del self.t
        self.connect()

    def do_sets(self, new_value, pv):
        """Set DO state"""
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        num = self.channels.index(pv_name)
        try:
            values = self.t.set_coil(num, new_value)
            for i, channel in enumerate(self.channels[:4]):  # set all
                if "None" in channel: continue
                self.pvs[self.channels[i]].set(values[i])
                self.remove_alarm(channel)
        except OSError:
            self.set_alarm(pv_name,'WRITE')
            self.reconnect()
        except TypeError:
            self.reconnect()

    async def do_reads(self):
        '''Match variables to methods in device driver and get reads from device'''
        try:
            readings = self.t.read_inputs()
            for i, channel in enumerate(self.channels[4:9]):
                if "None" in channel: continue
                self.pvs[channel].set(readings[i])
                self.remove_alarm(channel)
        except OSError:
            for i, channel in enumerate(self.channels[4:9]):
                if "None" in channel: continue
                self.set_alarm(channel)
            self.reconnect()
        except TypeError:
            self.reconnect()
        else:
            return True

    def set_alarm(self, channel):
        """Set alarm and severity for channel"""
        self.pvs[channel].set_alarm(severity=1, alarm=alarm.READ_ALARM)

    def remove_alarm(self, channel):
        """Remove alarm and severity for channel"""
        self.pvs[channel].set_alarm(severity=0, alarm=alarm.NO_ALARM)


class DeviceConnection():
    """Handle connection to Datexel 8130.
    """

    def __init__(self, host, port, timeout):
        """Open connection to DAT8017
        Arguments:
            host: IP address
            port: Port of device
            timeout: Telnet timeout in secs
        """
        self.host = host
        self.port = port
        self.timeout = timeout

        try:
            self.m = ModbusClient(host=self.host, port=int(self.port), unit_id=1, auto_open=True)
        except Exception as e:
            print(f"Datexel 8130 connection failed on {self.host}: {e}")

    def read_inputs(self):
        '''Read all channels.'''
        try:
            values = self.m.read_coils(504, 8)  # read all 8 channels starting at 40
            return values
        except Exception as e:
            print(f"Datexel 8130 read failed on {self.host}: {e}")
            raise OSError('8130 read')

    def read_coils(self):
        '''Read all out channels.'''
        try:
            return self.m.read_coils(488, 4)
        except Exception as e:
            print(f"Datexel 8130 read failed on {self.host}: {e}")
            raise OSError('8130 read')

    def set_coil(self, num, state):
        '''Flip channel to state. DO channels from 0 to 3'''
        try:
            self.m.write_single_coil(488 + num, state)
            return self.read_coils()
        except Exception as e:
            print(f"Datexel 8130 write failed on {self.host}: {e}")
            raise OSError('8130 write')
