import telnetlib
import re


class SR201():
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

