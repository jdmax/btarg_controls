import telnetlib
import re


class AMI136():
    '''Handle connection to AMI Model 136 via serial over ethernet.
    '''

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
        '''Read level.'''
        values = []
        try:
            self.tn.write(bytes(f"LEVEL\n", 'ascii'))  # 0 means it will return all channels
            data = self.tn.read_until(b'\n', timeout=self.timeout).decode('ascii')  # read until carriage return
            ms = self.read_regex.findall(data)
            for m in ms:
                values.append(float(m))
            return values

        except Exception as e:
            print(f"AMI136 read failed on {self.host}: {e}")
            raise OSError('AMI136 read')
