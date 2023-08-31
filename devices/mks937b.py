import telnetlib
import re
from softioc import builder, alarm


class Device():
    """Makes library of PVs needed for MKS937b and provides methods connect them to the device

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

        for channel in settings['channels']:  # set up PVs for each channel
            if "None" in channel: continue
            self.pvs[channel] = builder.aIn(channel, **sevr)

    def connect(self):
        """Open connection to device"""
        try:
            self.t = DeviceConnection(self.settings['ip'], self.settings['port'],
                                      self.settings['address'], self.settings['timeout'])
        except Exception as e:
            print(f"Failed connection on {self.settings['ip']}, {e}")

    def reconnect(self):
        del self.t
        print("Connection failed. Attempting reconnect.")
        self.connect()

    def do_sets(self, new_value, pv):
        """MKS937b has no sets"""
        pass

    async def do_reads(self):
        '''Match variables to methods in device driver and get reads from device'''
        try:
            pres = self.t.read_all()
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                self.pvs[channel].set(pres[i])
                self.remove_alarm(channel)
        except OSError:
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                self.set_alarm(channel)
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
    '''Handle connection to MKS 937B pressure gauge controller via ethernet to serial adapter.
    '''

    def __init__(self, host, port, address, timeout):
        '''Open connection to MKS
        Arguments:
            host: IP address
            port: Port of device
        '''
        self.host = host
        self.port = port
        self.address = address
        self.timeout = timeout

        try:
            self.tn = telnetlib.Telnet(self.host, port=self.port, timeout=self.timeout)
        except Exception as e:
            print(f"MKS 937B connection failed on {self.host}: {e}")

        self.read_regex = re.compile('ACK(.*)\s(.*)\s(.*)\s(.*)\s(.*)\s(.*);FF')

    def read_all(self):
        '''Read pressures for all channels.'''
        try:
            command = "@" + self.address + "PRZ?;FF"  # @003PRZ?;FF
            self.tn.write(bytes(command, 'ascii'))
            data = self.tn.read_until(b';FF', timeout=self.timeout).decode('ascii')
            m = self.read_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values

        except Exception as e:
            print(f"MKS 937B read failed on {self.host}: {e}")
            raise OSError('MKS 937B read')
