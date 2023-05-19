import telnetlib
import re
import serial

class THCD():
    '''Handle connection to Teledyne Hastings THCD-401 via Telnet.     
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
        
        try:
            self.tn = telnetlib.Telnet(self.host, port=self.port, timeout=self.timeout)                  
        except Exception as e:
            print(f"THCD connection failed on {self.host}: {e}")
            
        self.read_regex = re.compile('READ:(-*\d+.\d+|!RANGE!),(-*\d+.\d+|!RANGE!),(-*\d+.\d+|!RANGE!),(-*\d+.\d+)|!RANGE!,')
        self.set_regex = re.compile('SP(\d) VALUE: (\d+.\d+)')
        self.mode_regex = re.compile('SP(\d) MODE: \((\d)\)')
        self.ok_response_regex = re.compile(b'!a!o!\s\s')    
        
    def read_all(self):
        '''Read all channels. Returns list of 4 readings.'''        
        try:
            self.tn.write(b"ar\n")
            i, match, data = self.tn.expect([self.ok_response_regex], timeout = 2)   # read until ok response
            out = data.decode('ascii')
            m = self.read_regex.search(out)
            values = [float(x) if not 'RANGE' in x else 999 for x in m.groups()]
            return values
            
        except Exception as e:
            print(f"THCD read failed on {self.host}: {e}")
            raise OSError('THCD read')
        
    def set_setpoint(self, channel, value):
        '''Set set points for given channel.'''
        try:
            command = f"aspv {channel},{value:.2f}\n"
            self.tn.write(bytes(command,'ascii'))
            print(command)
            i, match, data = self.tn.expect([self.ok_response_regex], timeout = 2) 
            return True
            
        except Exception as e:
            print(f"THCD write setpoint failed on {self.host}: {e}")
            raise OSError('THCD write SP')
        
    def read_setpoints(self):
        '''Read set points for all channels. Returns list of 4 setpoints.'''     
        values = []
        try:
            self.tn.write(bytes(f"aspv?\n",'ascii'))
            i, match, data = self.tn.expect([self.ok_response_regex], timeout = 2) 
            out = data.decode('ascii')
            #print(out)
            ms = self.set_regex.findall(out)
            for m in ms:
                values.append(float(m[1]))
            return values              
            
        except Exception as e:
            print(f"THCD read setpoint failed on {self.host}: {e}")
            raise OSError('THCD read SP')

    def set_mode(self, channel, value):
        '''Set mode for given channel.'''
        try:
            self.tn.write(bytes(f"aspm {channel},{value}\n",'ascii'))
            i, match, data = self.tn.expect([self.ok_response_regex], timeout = 2)
            return True

        except Exception as e:
            print(f"THCD write mode failed on {self.host}: {e}")
            raise OSError('THCD write mode')

    def read_modes(self):
        '''Read modes for all channels. Returns list of 4.'''
        values = []
        try:
            self.tn.write(bytes(f"aspm?\n",'ascii'))
            i, match, data = self.tn.expect([self.ok_response_regex], timeout = 2)
            out = data.decode('ascii')
            ms = self.mode_regex.findall(out)
            for m in ms:
                values.append(int(m[1]))
            return values
        except Exception as e:
            print(f"THCD read modes failed on {self.host}: {e}")
            raise OSError('THCD read mode')


    def __del__(self):
        try:
            self.tn.close()
        except Exception as e:
            print(e)


class THCDserial():
    '''Handle connection to Teledyne Hastings THCD-401 via USB serial connection.
    '''

    def __init__(self):
        '''Open connection to Flow Controller
        Arguments:
            host: IP address
            port: Port of device
            timeout: Telnet timeout in secs
        '''
        self.port = '/dev/ttyUSB0'

        try:
            self.s = serial.Serial(self.port, baudrate=57600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=1)
        except Exception as e:
            print(f"THCD serial connection failed on {self.port}: {e}")

        self.read_regex = re.compile(
            'READ:(-*\d+.\d+|!RANGE!),(-*\d+.\d+|!RANGE!),(-*\d+.\d+|!RANGE!),(-*\d+.\d+)|!RANGE!,')
        self.set_regex = re.compile('SP(\d) VALUE: (\d+.\d+)')
        self.mode_regex = re.compile('SP(\d) MODE: \((\d)\)')
        self.ok_response_regex = re.compile(b'!a!o!\s\s')

    def read_all(self):
        '''Read all channels. Returns list of 4 readings.'''
        try:
            self.s.flushInput()
            self.s.flushOutput()

            self.s.write(("ar"+"\n").encode())
            self.s.readline().decode("utf-8")    # read back command
            out = self.s.readline().decode("utf-8")  # read back result
            self.s.readline().decode("utf-8")   # read back ok

            m = self.read_regex.search(out)
            values = [float(x) if not 'RANGE' in x else 999 for x in m.groups()]
            return values

        except Exception as e:
            print(f"THCD read failed on {self.host}: {e}")
            raise OSError('THCD read')

    def set_setpoint(self, channel, value):
        '''Set set points for given channel.'''
        try:
            self.s.flushInput()
            self.s.flushOutput()
            self.s.write((f"aspv {channel},{value}\n").encode())
            self.s.readline().decode("utf-8")    # read back command
            out = self.s.readline().decode("utf-8")   # read back ok
            return True

        except Exception as e:
            print(f"THCD write setpoint failed on {self.host}: {e}")
            raise OSError('THCD write SP')

    def read_setpoints(self):
        '''Read set points for all channels. Returns list of 4 setpoints.'''
        values = []
        try:
            self.s.flushInput()
            self.s.flushOutput()

            self.s.write((f"aspv?\n").encode())
            self.s.readline().decode("utf-8")    # read back command
            out = self.s.readline().decode("utf-8")  # read back result
            out += self.s.readline().decode("utf-8")  # read back result
            out += self.s.readline().decode("utf-8")  # read back result
            out += self.s.readline().decode("utf-8")  # read back result

            self.s.readline().decode("utf-8")   # read back ok
            ms = self.set_regex.findall(out)
            for m in ms:
                values.append(float(m[1]))
            return values

        except Exception as e:
            print(f"THCD read setpoint failed on {self.host}: {e}")
            raise OSError('THCD read SP')

    def set_mode(self, channel, value):
        '''Set mode for given channel.'''
        try:
            self.s.flushInput()
            self.s.flushOutput()
            self.s.write((f"aspm {channel},{value}\n").encode())
            self.s.readline().decode("utf-8")    # read back command
            out = self.s.readline().decode("utf-8")   # read back ok
            return True

        except Exception as e:
            print(f"THCD write mode failed on {self.host}: {e}")
            raise OSError('THCD write mode')

    def read_modes(self):
        '''Read modes for all channels. Returns list of 4.'''
        values = []
        try:
            self.s.flushInput()
            self.s.flushOutput()

            self.s.write((f"aspm?\n").encode())
            self.s.readline().decode("utf-8")    # read back command
            out = self.s.readline().decode("utf-8")  # read back result
            out += self.s.readline().decode("utf-8")  # read back result
            out += self.s.readline().decode("utf-8")  # read back result
            out += self.s.readline().decode("utf-8")  # read back result

            self.s.readline().decode("utf-8")   # read back ok

            ms = self.mode_regex.findall(out)
            for m in ms:
                values.append(int(m[1]))
            return values

        except Exception as e:
            print(f"THCD read modes failed on {self.host}: {e}")
            raise OSError('THCD read mode')

    def __del__(self):
        try:
            self.s.close()
        except Exception as e:
            print(e)

