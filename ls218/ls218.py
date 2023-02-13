import telnetlib
import re

class LS218():
    '''Handle connection to Lakeshore Model 218 via serial over ethernet. 
    '''
    def __init__(self, host, port, timeout):        
        '''Open connection to Lakeshore 218
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
            print(f"LS218 connection failed on {self.host}: {e}")
            
        self.read_regex = re.compile('([+-]\d+.\d+)')
         
    def read_all(self):
        '''Read temperatures for all channels.'''  
        values = []
        try: 
            self.tn.write(bytes(f"SRDG? 0\n",'ascii'))     # 0 means it will return all channels
            data = self.tn.read_until(b'\n', timeout = 2).decode('ascii')   # read until carriage return
            ms = self.read_regex.findall(data)
            for m in ms:
                values.append(float(m))
            return values
            
        except Exception as e:
            print(f"LS218 read failed on {self.host}: {e}")
        