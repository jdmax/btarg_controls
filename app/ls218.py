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
        '''
        self.host = host
        self.port = port
        self.timeout = timeout
        
        try:
            self.tn = telnetlib.Telnet(self.host, port=self.port, timeout=self.timeout)                  
        except Exception as e:
            print(f"LS336 connection failed on {self.host}: {e}")
            
        self.read_regex = re.compile('([+-]\d+.\d+)')   
        #self.set_regex = re.compile('SP(\d) VALUE: (\d+.\d+)')  
        #self.ok_response_regex = re.compile(b'!a!o!\s\s')    
         
    def read_temps(self):
        '''Read temperatures for all channels.'''  
        values = []
        try: 
            self.tn.write(bytes(f"SRDG? 0\n",'ascii'))     # 0 means it will return all channels
            data = self.tn.read_until(b'\n', timeout = 2).decode('ascii')   # read until carriage return
            ms = self.read_regex.find_all(data)
            for m in ms:
                values.append(float(m[1])) 
            return values
            
        except Exception as e:
            print(f"LS218 read failed on {self.host}: {e}")
        