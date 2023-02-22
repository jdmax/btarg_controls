from pyModbusTCP.client import ModbusClient

class DAT8148():
    '''Handle connection to Datexel 8148 digital input. Unit has 16 digital read channels.
    '''

    def __init__(self, host, port, timeout):
        '''Open connection to DAT8148
        Arguments:
            host: IP address
            port: Port of device
            timeout: Telnet timeout in secs
        '''
        self.host = host
        self.port = port
        self.timeout = timeout

        try:
            self.m = ModbusClient(host=self.host, port=self.port, unit_id=1, auto_open=True)
        except Exception as e:
            print(f"Datexel 8148 connection failed on {self.host}: {e}")

    def read_all(self):
        '''Read all channels.'''
        try:
            values = self.m.read_coils(505,16)  # read all 16 channels starting at 40
            return values

        except Exception as e:
            print(f"Datexel 8148 read failed on {self.host}: {e}")