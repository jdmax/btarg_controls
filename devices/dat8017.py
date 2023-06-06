from pyModbusTCP.client import ModbusClient
from softioc import builder

class Device():
    """Makes library of PVs needed for LS336 and provides methods connect them to the device

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

        for channel in settings['channels'].keys():  # set up PVs for each channel, calibrations are values of dict
            if "None" in channel: continue
            self.pvs[channel] = builder.aIn(channel)
            self.calibs[channel] = settings['channels'][channel]

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
        """8017 has no sets"""
        pass

    def do_reads(self):
        '''Match variables to methods in device driver and get reads from device'''
        try:
            new_reads = {}
            readings = self.t.read_all()
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                new_reads[channel] = readings[i] * self.calibs[channel]

            for key, value in new_reads.items():
                self.pvs[key].set(value)
        except OSError:
            self.reconnect()
        return


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
            self.m =  ModbusClient(host=self.host, port=self.port, unit_id=1, auto_open=True)
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