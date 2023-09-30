from pyModbusTCP.client import ModbusClient
from softioc import builder, alarm

class Device():
    """Makes library of PVs needed for DAT8017 ADC and provides methods connect them to the device

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
        self.new_reads = {}
        self.calibs = {}
        sevr = {'HHSV': 'MAJOR', 'HSV': 'MINOR', 'LSV': 'MINOR', 'LLSV': 'MAJOR', 'DISP': '0'}

        for channel in settings['channels']:  # set up PVs for each channel, calibrations are values of dict
            if "None" in channel: continue
            self.pvs[channel] = builder.aIn(channel, **sevr)
            self.calibs[channel] = settings['calibration'][channel]

    async def connect(self):
        '''Open connection to device'''
        try:
            self.t = DeviceConnection(self.settings['ip'], self.settings['port'], self.settings['timeout'])
        except Exception as e:
            print(f"Failed connection on {self.settings['ip']}, {e}")

    async def reconnect(self):
        '''Delete connection and try again'''
        del self.t
        print("Connection failed. Attempting reconnect.")
        await self.connect()

    def do_sets(self, new_value, pv):
        """8017 has no sets"""
        pass

    async def do_reads(self):
        '''Match variables to methods in device driver and get reads from device'''
        try:
            readings = self.t.read_all()
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                if isinstance(self.calibs[channel], int):   # do conversion from 4-20 mA to psi using max range calib
                    p = (readings[i]/1000)*(self.calibs[channel]/16) - 25
                    self.pvs[channel].set(p)
                else:
                    self.pvs[channel].set(readings[i])
                self.remove_alarm(channel)
        except OSError as e:
            print(e)
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                self.set_alarm(channel)
            await self.reconnect()
        except TypeError as e:
            print(e)
            await self.reconnect()
        else:
            return True

    def set_alarm(self, channel):
        """Set alarm and severity for channel"""
        self.pvs[channel].set_alarm(severity=1, alarm=alarm.READ_ALARM)

    def remove_alarm(self, channel):
        """Remove alarm and severity for channel"""
        self.pvs[channel].set_alarm(severity=0, alarm=alarm.NO_ALARM)

class DeviceConnection():
    '''Handle connection to Datexel 8017-V and 8017-I. Communication to both is the same,
    with the 8 read channels at the same addresses. Difference will be in calibration.
    '''

    def __init__(self, host, port, timeout):
        '''Open connection to DAT8017
        Arguments:
            host: IP address
            port: Port of device
            timeout: Telnet timeout in secs
        '''
        self.host = host
        self.port = port
        self.timeout = timeout

        try:
            self.m =  ModbusClient(host=self.host, port=int(self.port), unit_id=1, auto_open=True)
        except Exception as e:
            print(f"Datexel 8017 connection failed on {self.host}: {e}")

    def read_all(self):
        '''Read all channels.'''
        try:
            values = self.m.read_input_registers(40,8)  # read all 8 channels starting at 40
            return values

        except Exception as e:
            print(f"Datexel 8017 read failed on {self.host}: {e}")
            raise OSError('8017 read')