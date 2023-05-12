import telnetlib
import re

class DP832():
    '''Handle connection to Rigol DP832 via Telnet.
    '''

    def __init__(self, host, port, timeout):
        '''Open connection to Rigol DP832, required LAN option unlocked.
        30V/3A on Ch1, Ch2. 5V/3A Ch3.
        Arguments:
            host: IP address
        port: Port of device
        '''
        self.host = host
        self.port = port
        self.timeout = timeout

        try:
            self.tn = telnetlib.Telnet(self.host, port=self.port, timeout=self.timeout)
        except Exception as e:
            print(f"DP832 connection failed on {self.host}: {e}")

        self.read_regex = re.compile('CH\d:\d+V/\dA,(\d+.\d+),(\d+.\d+)')
        self.read_sp_regex = re.compile('(\d+.\d+),(\d+.\d+),(\d+.\d+)')

    def read_sp(self, channel):
        '''Read voltage, current measured for given channel (1,2,3).'''
        try:
            self.tn.write(bytes(f":APPLY? CH{channel}\n", 'ascii'))   # Reading
            data = self.tn.read_until(b'\n', timeout=2).decode('ascii')  # read until carriage return
            m = self.read_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values   # return voltage, current as list

        except Exception as e:
            raise OSError('DP832 read sp')
            print(f"DP832 read sp failed on {self.host}: {e}")

    def read(self, channel):
        '''Read voltage, current measured for given channel (1,2,3).'''
        try:
            self.tn.write(bytes(f":MEASURE:ALL? CH{channel}\n", 'ascii'))   # Reading
            data = self.tn.read_until(b'\n', timeout=2).decode('ascii')  # read until carriage return
            m = self.read_sp_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values   # return voltage, current as list

        except Exception as e:
            raise OSError('DP832 read')
            print(f"DP832 read failed on {self.host}: {e}")

    def set(self, channel, voltage, current):
        '''Set current and voltage for given channel'''
        try:
            print(channel, voltage, current)
            self.tn.write(bytes(f":APPLY CH{channel},{voltage},{current}\n", 'ascii'))
            self.tn.write(bytes(f":APPLY? CH{channel}\n", 'ascii'))   # Reading
            data = self.tn.read_until(b'\n', timeout=2).decode('ascii')  # read until carriage return
            print(f":APPLY CH{channel},{voltage},{current}\n","2",data)
            m = self.read_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values   # return voltage, current as list

        except Exception as e:
            raise OSError('DP832 set')
            print(f"DP832 set failed on {self.host}: {e}")


    def read_state(self, channel):
        '''Read output state for given channel.
        Arguments:
            channel: out put channel (1 to 4)
        '''
        try:
            self.tn.write(bytes(f"OUTPUT? CH{channel}\n", 'ascii'))
            data = self.tn.read_until(b'\n', timeout=2).decode('ascii')  # read until carriage return
            state = True if 'ON' in data else False
            return state

        except Exception as e:
            raise OSError('DP832 outmode read')
            print(f"DP832 outmode read failed on {self.host}: {e}")

    def set_state(self, channel, state):
        '''Setup output state on (true) or off (false).
        Arguments:
            channel: out put channel (1 to 4)
            state: False=Off, True=On
        '''
        out = 'ON' if state else 'OFF'
        try:
            self.tn.write(bytes(f":OUTPUT CH{channel},{out}\n", 'ascii'))
            return True
        except Exception as e:
            raise OSError('DP832 out set')
            print(f"DP832 out set failed on {self.host}: {e}")
