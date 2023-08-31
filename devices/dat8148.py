from pyModbusTCP.client import ModbusClient
from softioc import builder, alarm

class Device():
    """Makes library of PVs needed for the DAT8148 DIO and provides methods connect them to the device

    Attributes:
        pvs: dict of Process Variables keyed by name
        channels: channels of device
    """

    def __init__(self, device_name, settings):
        '''Make PVs needed for this device and put in pvs dict keyed by name
        '''
        self.device_name = device_name
        self.settings = settings
        self.channels = settings['channels']
        self.pvs = {}
        sevr = {'HHSV': 'MAJOR', 'HSV': 'MINOR', 'LSV': 'MINOR', 'LLSV': 'MAJOR', 'DISP': '0'}

        for channel in settings['channels'].keys():  # set up PVs for each channel, calibrations are values of dict
            if "None" in channel: continue
            self.pvs[channel] = builder.aIn(channel, **sevr)

    def connect(self):
        '''Open connection to device'''
        try:
            self.t = DeviceConnection(self.settings['ip'], self.settings['port'], self.settings['timeout'])
        except Exception as e:
            print(f"Failed connection on {self.settings['ip']}, {e}")

    def reconnect(self):
        del self.t
        print("Connection failed. Attempting reconnect.")
        self.connect()

    def do_sets(self, new_value, pv):
        """8148 has no sets"""
        pass

    async def do_reads(self):
        """Match variables to methods in device driver and get reads from device. Set to PVs."""
        try:
            readings = self.t.read_all()
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                self.pvs[channel].set(readings[i])
                self.remove_alarm(channel)
        except OSError:
            for i, channel in enumerate(self.channels):
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
    """Handle connection to Datexel 8148 digital input. Unit has 16 digital read channels.
    """

    def __init__(self, host, port, timeout):
        '''Open connection to DAT8148
        Arguments:
            host: IP address
            port: Port of device
            timeout: Telnet timeout in secs
        '''
        self.host = host
        self.port = port
        self.timeout = timeout

        try:
            self.m = ModbusClient(host=self.host, port=int(self.port), unit_id=1, auto_open=True)
        except Exception as e:
            print(f"Datexel 8148 connection failed on {self.host}: {e}")

    def read_all(self):
        '''Read all input coils.'''
        try:
            values = self.m.read_coils(496,16)  # read all 16 channels starting at 496. Order is 8-16 then 0-7.
            return values[8:] + values[:8]  # switch around order to get 0-15

        except Exception as e:
            print(f"Datexel 8148 read failed on {self.host}: {e}")
            raise OSError('8148 read')