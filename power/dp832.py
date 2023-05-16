import telnetlib
import re
import time

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
            command = f":APPLY? CH{channel}\n"
            self.tn.write(bytes(command, 'ascii'))   # Reading
            data = self.tn.read_until(b'\n', timeout=self.timeout).decode('ascii')  # read until carriage return
            m = self.read_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values   # return voltage, current as list

        except Exception as e:
            print(f"DP832 read sp failed on {self.host}: {e},{command},{data}")
            raise OSError('DP832 read sp')

    def read(self, channel):
        '''Read voltage, current measured for given channel (1,2,3).'''
        try:
            command = f":MEASURE:ALL? CH{channel}\n"
            self.tn.write(bytes(command, 'ascii'))   # Reading
            data = self.tn.read_until(b'\n', timeout=self.timeout).decode('ascii')  # read until carriage return
            m = self.read_sp_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values   # return voltage, current as list

        except Exception as e:
            print(f"DP832 read failed on {self.host}: {e}, {command},{data}")
            raise OSError('DP832 read')

    def set(self, channel, voltage, current):
        '''Set current and voltage for given channel'''
        try:
            self.tn.write(bytes(f":APPLY CH{channel},{voltage},{current}\n", 'ascii'))
            time.sleep(0.2)
            return self.read_sp(channel)   # return voltage, current as list

        except Exception as e:
            print(f"DP832 set failed on {self.host}: {e}")
            raise OSError('DP832 set')


    def read_state(self, channel):
        '''Read output state for given channel.
        Arguments:
            channel: out put channel (1 to 4)
        '''
        try:
            self.tn.write(bytes(f"OUTPUT? CH{channel}\n", 'ascii'))
            data = self.tn.read_until(b'\n', timeout=self.timeout).decode('ascii')  # read until carriage return
            state = True if 'ON' in data else False
            return state

        except Exception as e:
            print(f"DP832 outmode read failed on {self.host}: {e}")
            raise OSError('DP832 outmode read')

    def set_state(self, channel, state):
        '''Setup output state on (true) or off (false).
        Arguments:
            channel: out put channel (1 to 4)
            state: False=Off, True=On
        '''
        out = 'ON' if state else 'OFF'
        try:
            self.tn.write(bytes(f":OUTPUT CH{channel},{out}\n", 'ascii'))
            time.sleep(0.2)
            return self.read_state(channel)
        except Exception as e:
            print(f"DP832 out set failed on {self.host}: {e}")
            raise OSError('DP832 out set')
