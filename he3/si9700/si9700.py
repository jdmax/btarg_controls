import telnetlib
import re

class SI9700():
    '''Handle connection to Scientific Instruments 9700 heater controller via RS232 to Ethernet.
    '''
    def __init__(self, host, port, timeout):        
        '''Open connection to Heater Controller
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
            print(f"SI-9700 connection failed on {self.host}: {e}")
            
        self.heater_regex = re.compile('\d{2}.\d{2}')

        self.heater_response_regex = re.compile(b'\d{2}.\d{2}\r')
    def read_heater(self):
        '''Read heater and return. Will not read if you go too fast. Delay maybe 10 secs?'''
        try:
            self.tn.write(b"HTR?\r")
            i, match, data = self.tn.expect([self.heater_response_regex], timeout = 2)   # read until ok response
            print(data)
            out = data.decode('ascii')
            ms = self.heater_regex.findall(out)
            values  = [float(x) for x in ms]
            return values
            
        except Exception as e:
            print(f"SI-9700 read failed on {self.host}: {e}")
