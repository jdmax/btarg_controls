import telnetlib
import re


class HFC():
    '''Handle connection to Teledyne Hastings HFC-D-303A via ethernet to serial.
    '''

    def __init__(self, host, port, timeout):
        '''Open connection to Flow Controller
        Arguments:
            host: IP address
            port: Port of device
            timeout: Telnet timeout in secs
        '''
        self.host = host
        self.port = port
        self.timeout = timeout

        self.read_regex = re.compile('Flow:\s+(-*\d+.\d+)\s')
        self.set_regex = re.compile('SetPoint:\s+(\d+.\d+)\s')
        self.mode_regex = re.compile('Valve Position:\s+x(\d)(\d)')
        self.ok_response_regex = re.compile(b'>')

        try:
            self.tn = telnetlib.Telnet(self.host, port=self.port, timeout=self.timeout)
            self.tn.write(b"S112=1\r")   # set verbose on
            i, match, data = self.tn.expect([self.ok_response_regex], timeout=2)  # read until ok response

        except Exception as e:
            print(f"HFC connection failed on {self.host}: {e}")

    def read(self):
        '''Read channel. Returns flow reading.'''
        try:
            self.tn.write(b"f\r")
            i, match, data = self.tn.expect([self.ok_response_regex], timeout=2)  # read until ok response
            out = data.decode('ascii')
            m = self.read_regex.search(out)
            value = float(m.groups()[0])
            return value

        except Exception as e:
            print(f"HFC read failed on {self.host}: {e}")
            raise OSError('HFC read')

    def set_setpoint(self, value):
        '''Set set point this channel.'''
        try:
            command = f"V4={value:.2f}\r"
            self.tn.write(bytes(command, 'ascii'))
            i, match, data = self.tn.expect([self.ok_response_regex], timeout=2)
            return True

        except Exception as e:
            print(f"HFC write setpoint failed on {self.host}: {e}")
            raise OSError('HFC write SP')

    def read_setpoint(self):
        '''Read set points and return it.'''
        values = []
        try:
            self.tn.write(bytes(f"V4\r", 'ascii'))
            i, match, data = self.tn.expect([self.ok_response_regex], timeout=2)
            out = data.decode('ascii')
            m = self.set_regex.search(out)
            value = float(m.groups()[0])
            return value

        except Exception as e:
            print(f"HFC read setpoint failed on {self.host}: {e}")
            raise OSError('HFC read SP')

    def set_mode(self, value):
        '''Set mode
         0 = DEFAULT
         1 = AUTO
         2 = HOLD
         3 = SHUT
         4 = PURGE
         5 = VARIABLE
         6 = ERROR'''
        try:
            command = f"V1={value:.2f}\r"
            self.tn.write(bytes(command, 'ascii'))
            i, match, data = self.tn.expect([self.ok_response_regex], timeout=2)
            return True

        except Exception as e:
            print(f"HFC write mode failed on {self.host}: {e}")
            raise OSError('HFC write mode')

    def read_mode(self):
        '''Read modes for all channels. Returns list of 4.'''
        try:
            self.tn.write(bytes(f"V3\r", 'ascii'))
            i, match, data = self.tn.expect([self.ok_response_regex], timeout=2)
            out = data.decode('ascii')
            m = self.mode_regex.search(out)
            value1 = m.groups()[0]
            value2 = m.groups()[1]
            if '1' in value1:  # get value return to match set mode values
                return 3   # closed
            elif '2' in value1:
                return 4   # open
            elif '3' in value1:
                return 2  # hold
            elif '4' in value1:
                return 5  # manual
            elif '5' in value1:
                return 1  # manual
        except Exception as e:
            print(f"HFC read modes failed on {self.host}: {e}")
            raise OSError('HFC read mode')

    def __del__(self):
        try:
            self.tn.close()
        except Exception as e:
            print(e)
