import telnetlib
import re
from softioc import builder


class Device():
    """Makes library of PVs needed for LS218 and provides methods connect them to the device

    Attributes:
        pvs: dict of Process Variables keyed by name
        channels: channels of device
    """

    def __init__(self, device_name, settings):
        """Make PVs needed for this device and put in pvs dict keyed by name
        """
        self.device_name = device_name
        self.settings = settings
        self.channels = settings['channels']
        self.pvs = {}
        sevr = {'HHSV': 'MAJOR', 'HSV': 'MINOR', 'LSV': 'MINOR', 'LLSV': 'MAJOR', 'DISP': '0'}


        for channel in settings['channels']:  # set up PVs for each channel
            if "None" in channel: continue
            self.pvs[channel] = builder.aIn(channel, **sevr)

    def connect(self):
        """Open connection to device"""
        try:
            self.t = DeviceConnection(self.settings['ip'], self.settings['port'], self.settings['timeout'])
        except Exception as e:
            print(f"Failed connection on {self.settings['ip']}, {e}")

    def reconnect(self):
        del self.t
        print("Connection failed. Attempting reconnect.")
        self.connect()

    def do_sets(self, new_value, pv):
        """AMI136 has no sets"""
        pass

    def do_reads(self):
        """Match variables to methods in device driver and get reads from device"""
        try:
            new_reads = {}
            levels = self.t.read()
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                new_reads[channel] = levels[i]

            for key, value in new_reads.items():
                self.pvs[key].set(value)
        except OSError:
            self.reconnect()
        return


class DeviceConnection():
    """Handle connection to AMI Model 136 via serial over ethernet.
    """

    def __init__(self, host, port, timeout):
        '''Open connection to AMI Model 136
        Arguments:
            host: IP address
            port: Port of device
            timeout: Telnet timeout in secs
        '''
        self.host = host
        self.port = port
        self.timeout = timeout

        try:
            self.tn = telnetlib.Telnet(self.host, port=self.port, timeout=self.timeout)
            self.tn.write(bytes(f"PERCENT\n", 'ascii'))  # ensure we are reading out in percent
            data = self.tn.read_until(b'\n', timeout=self.timeout).decode('ascii')
        except Exception as e:
            print(f"AMI136 connection failed on {self.host}: {e}")

        self.read_regex = re.compile('(\d+.\d+)')

    def read(self):
        """Read level from device."""
        values = []
        try:
            self.tn.write(bytes(f"LEVEL\n", 'ascii'))
            data = self.tn.read_until(b'\n', timeout=self.timeout).decode('ascii')  # read until carriage return
            ms = self.read_regex.findall(data)
            for m in ms:
                values.append(float(m))
            return values

        except Exception as e:
            print(f"AMI136 read failed on {self.host}: {e}")
            raise OSError('AMI136 read')
