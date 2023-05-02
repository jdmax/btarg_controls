import telnetlib
import re


class MKS937B():
    '''Handle connection to MKS 937B pressure gauge controller via Telnet.
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
            command = "@"+self.address+"PRZ?;FF"              # @003PRZ?;FF
            self.tn.write(bytes(command, 'ascii'))
            data = self.tn.read_until(b';FF', timeout=self.timeout).decode('ascii')
            m = self.read_regex.search(data)
            values = [float(x) for x in m.groups()]
            return values

        except Exception as e:
            raise OSError('MKS 937B read')
            print(f"MKS 937B read failed on {self.host}: {e}")
