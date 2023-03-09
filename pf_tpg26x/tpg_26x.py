import telnetlib
import re

class TPG26x():
    '''Handle connection to Pfeiffer TPG-26x via RS232 to Ethernet.
    '''
    def __init__(self, host, port, timeout):        
        '''Open connection to Pressure Controller
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
        except Exception as e:
            print(f"TPG26x connection failed on {self.host}: {e}")
            
        self.read_regex = re.compile('READ:(\d+.\d+),(\d+.\d+),(\d+.\d+),(\d+.\d+),')
        
    def read_all(self):
        '''Read all channels. Returns list of 2 readings.'''
        enq = b"\x05"
        try:
            self.tn.write(b"PRX \r\n")
            i, match, data = self.tn.expect([b"\r\n"], timeout = 2)   # read until ok response
            out = data.decode('ascii')
            print(data)
            self.tn.write(enq)
            i, match, data = self.tn.expect([b"\r\n"], timeout = 2)   # read until ok response
            out = data.decode('ascii')
            print(data)
            #m = self.read_regex.search(out)
            #values  = [float(x) for x in m.groups()]
            return data
            
        except Exception as e:
            print(f"TPG26x read failed on {self.host}: {e}")
