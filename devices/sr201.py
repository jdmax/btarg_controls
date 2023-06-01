import telnetlib
import re
from softioc import builder

class Device():
    """Makes library of PVs needed for the SR-201 relay and provides methods connect them to the device

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

        for channel in settings['channels'].keys():  # set up PVs for each channel, calibrations are values of dict
            if "None" in channel: continue
            self.pvs[channel] = builder.aOut(channel, on_update_name=self.do_sets)

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
        """Set SR201 state"""
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        chan = str(self.channels.index(pv_name) + 1)
        try:
            values = self.t.switch(new_value, chan)
            self.pvs[pv_name].set(values[int(chan)-1])  # set returned value
        except OSError:
            self.reconnect()

    def do_reads(self):
        '''Match variables to methods in device driver and get reads from device'''
        try:
            self.new_reads = {}
            readings = self.t.read_all()
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                self.new_reads[channel] = readings[i]
        except OSError:
            self.reconnect()
        return

    def update_pvs(self):
        '''Set new values from the reads to the PVs'''
        try:
            for key, value in self.new_reads.items():
                self.pvs[key].set(value)
        except OSError:
            self.reconnect()
        except Exception as e:
            print(f"PV set failed: {e}")


class DeviceConnection():
    '''Handle connection to ethernet relay via Telnet.
    '''

    def __init__(self, host, port, timeout):
        '''Open connection to SR-201 relays
        Arguments:
            host: IP address
            port: Port of device
            timeout: Telnet timeout in secs
        '''
        self.host = host
        self.port = port
        self.timeout = timeout

        self.ok_regex = re.compile(b'(\d{8})')
        self.read_regex = re.compile('(\d)(\d)(\d)(\d)(\d)(\d)(\d)(\d)')

    def open_telnet(self):
        '''
        Open connection to SR-201
        '''
        try:
            self.tn = telnetlib.Telnet(self.host, port=self.port, timeout=self.timeout)
        except Exception as e:
            print(f"SR-201 relay open connection failed on {self.host}: {e}")

    def close_telnet(self):
        '''
        Close connection to SR-201
        '''
        try:
            self.tn.close()
        except Exception as e:
            print(f"SR-201 relay close connection failed on {self.host}: {e}")

    def switch(self, state, chan):
        '''
        Open connection, then send command, then close connection.
        state is boolean (false is open), chan is channel string '1' or '2'.
        '''
        try:
            self.open_telnet()
            if state:
                command = '1' + chan
            else:
                command = '2' + chan
            self.tn.write(bytes(command,'ascii'))
            i, match, data = self.tn.expect([self.ok_regex], timeout = 2)   # read full response
            self.close_telnet()
            out = data.decode('ascii')
            m = self.read_regex.search(out)
            values = [float(x) for x in m.groups()]
            return values
        except Exception as e:
            print(f"SR201 set failed on {self.host}: {e}")
            raise OSError('SR201 set')

    def read_all(self):
        '''
        Open connection, then send command, then close connection.
        state is boolean (false is open), chan is channel string '1' or '2'.
        '''
        try:
            self.open_telnet()
            command = '0X'
            self.tn.write(bytes(command,'ascii'))
            i, match, data = self.tn.expect([self.ok_regex], timeout = 2)   # read full response
            self.close_telnet()
            out = data.decode('ascii')
            m = self.read_regex.search(out)
            values = [float(x) for x in m.groups()]
            return values
        except Exception as e:
            print(f"SR201 read failed on {self.host}: {e}")
            raise OSError('SR201 set')
