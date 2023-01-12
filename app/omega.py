import telnetlib
import re

class Omega():
    '''Handle connection to Omega iSeries Temperature controller over telnet. 
    '''
    def __init__(self, host, port, timeout):        
        '''Open connection to Omega
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
            print(f"Omega connection failed on {self.host}: {e}")
            
        self.read_regex = re.compile('([+-]\d+.\d+)')   
        #self.set_regex = re.compile('SP(\d) VALUE: (\d+.\d+)')  
        #self.ok_response_regex = re.compile(b'!a!o!\s\s')    
         
    def set_setpoint(self):
        '''Change setpoint 1.'''  
        try: 
            self.tn.write(bytes(f"SRDG? 0\n",'ascii'))     # 0 means it will return all channels
            data = self.tn.read_until(b'\n', timeout = 2).decode('ascii')   # read until carriage return
            m = self.pid_regex.search(data)
            values  = [float(x) for x in m.groups()]
            return values
            
        except Exception as e:
            print(f"Omega read failed on {self.host}: {e}")
        