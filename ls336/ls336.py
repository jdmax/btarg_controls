import telnetlib
import re


class LS336():
    '''Handle connection to Lakeshore Model 336 via Telnet. 
    '''

    def __init__(self, host, port, timeout):
        '''Open connection to Lakeshore 218
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
            print(f"LS336 connection failed on {self.host}: {e}")

        self.read_regex = re.compile('([+-]\d+.\d+),([+-]\d+.\d+),([+-]\d+.\d+),([+-]\d+.\d+)')
        self.pid_regex = re.compile('([+-]\d+.\d+),([+-]\d+.\d+),([+-]\d+.\d+)')
        self.out_regex = re.compile('(\d),(\d),(\d)')
        self.range_regex = re.compile('(\d)')
        self.setp_regex = re.compile('([+-]\d+.\d+)')
        # self.set_regex = re.compile('SP(\d) VALUE: (\d+.\d+)')
        # self.ok_response_regex = re.compile(b'!a!o!\s\s')

    def read_temps(self):
        '''Read temperatures for all channels.'''
        try:
            self.tn.write(bytes(f"KRDG? 0\n", 'ascii'))   # Kelvin reading
            data = self.tn.read_until(b'\n', timeout=2).decode('ascii')  # read until carriage return
            m = self.read_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values

        except Exception as e:
            print(f"LS336 pid read  failed on {self.host}: {e}")

    def set_pid(self, channel, P, I, D):
        '''Setup PID for given channel (1 or 2).'''
        try:
            self.tn.write(bytes(f"PID {channel},{P},{I},{D}\n", 'ascii'))
            self.tn.write(bytes(f"PID?\n", 'ascii'))
            data = self.tn.read_until(b'\n', timeout=2).decode('ascii')  # read until carriage return
            m = self.pid_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values

        except Exception as e:
            print(f"LS336 pid set failed on {self.host}: {e}")

    def read_pid(self, channel):
        '''Read PID for given channel (1 or 2).'''
        try:
            self.tn.write(bytes(f"PID?\n", 'ascii'))
            data = self.tn.read_until(b'\n', timeout=2).decode('ascii')  # read until carriage return
            m = self.pid_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values

        except Exception as e:
            print(f"LS336 pid read failed on {self.host}: {e}")

    def read_heater(self, channel):
        '''Read Heater output (%) for given channel (1 or 2).'''
        try:
            self.tn.write(bytes(f"HTR? {channel}\n", 'ascii'))
            data = self.tn.read_until(b'\n', timeout=2).decode('ascii')  # read until carriage return
            m = self.setp_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values[0]

        except Exception as e:
            print(f"LS336 heater read failed on {self.host}: {e}")

    def set_outmode(self, channel, mode, in_channel, powerup_on):
        '''Setup output and readback.
        Arguments:
            channel: out put channel (1 to 4)
            mode: 0=Off, 1=Closed Loop
            in_channel: input channel for control 0=None, 1=A to 4=D
            powerup_on: Output should remain on after power cycle? 1 is yes, 0 no.
        '''
        try:
            self.tn.write(bytes(f"OUTMODE {channel},{mode},{in_channel},{powerup_on}\n", 'ascii'))
            self.tn.write(bytes(f"OUTMODE? {channel}\n", 'ascii'))
            data = self.tn.read_until(b'\n', timeout=2).decode('ascii')  # read until carriage return
            m = self.out_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values[0]

        except Exception as e:
            print(f"LS336 outmode set  failed on {self.host}: {e}")

    def read_outmode(self, channel):
        '''Read output.
        Arguments:
            channel: out put channel (1 to 4)
        '''
        try:
            self.tn.write(bytes(f"OUTMODE? {channel}\n", 'ascii'))
            data = self.tn.read_until(b'\n', timeout=2).decode('ascii')  # read until carriage return
            m = self.out_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values[0]

        except Exception as e:
            print(f"LS336 outmode set  failed on {self.host}: {e}")

    def set_range(self, channel, hrange):
        '''Setup output and readback. Has no effect if outmode is off.
        Arguments:
            channel: output channel (1 to 4)
            hrange: 0=off, 1=Low, 2=Med, 3=High
        '''
        try:
            self.tn.write(bytes(f"RANGE {channel},{hrange}\n", 'ascii'))
            self.tn.write(bytes(f"RANGE? {channel}\n", 'ascii'))
            data = self.tn.read_until(b'\n', timeout=2).decode('ascii')  # read until carriage return
            m = self.range_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values[0]

        except Exception as e:
            print(f"LS336 range read failed on {self.host}: {e}")

    def read_range(self, channel):
        '''Read range. Has no effect if outmode is off.
        Arguments:
            channel: output channel (1 to 4)
        '''
        try:
            self.tn.write(bytes(f"RANGE? {channel}\n", 'ascii'))
            data = self.tn.read_until(b'\n', timeout=2).decode('ascii')  # read until carriage return
            m = self.range_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values[0]

        except Exception as e:
            print(f"LS336 range read failed on {self.host}: {e}")

    def set_setpoint(self, channel, value):
        '''Setup setpoint and read back.
        Arguments:
            channel: output channel (1 to 4)
            value: setpoint in units of loop sensor
        '''
        try:
            self.tn.write(bytes(f"SETP {channel},{value}\n", 'ascii'))
            self.tn.write(bytes(f"SETP? {channel}\n", 'ascii'))
            data = self.tn.read_until(b'\n', timeout=2).decode('ascii')  # read until carriage return
            m = self.setp_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values[0]

        except Exception as e:
            print(f"LS336 range set failed on {self.host}: {e}")

    def read_setpoint(self, channel):
        '''Setup setpoint and read back.
        Arguments:
            channel: output channel (1 to 4)
        '''
        try:
            self.tn.write(bytes(f"SETP? {channel}\n", 'ascii'))
            data = self.tn.read_until(b'\n', timeout=2).decode('ascii')  # read until carriage return
            m = self.setp_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values[0]

        except Exception as e:
            print(f"LS336 range set failed on {self.host}: {e}")
