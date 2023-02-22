from pyModbusTCP.client import ModbusClient

class DAT8017():
    '''Handle connection to Datexel 8017-V and 8017-I. Communication to both is the same,
    with the 8 read channels at the same addresses. Difference will be in calibration.
    '''

    def __init__(self, host, port, timeout):
        '''Open connection to DAT8017
        Arguments:
            host: IP address
            port: Port of device
            timeout: Telnet timeout in secs
        '''
        self.host = host
        self.port = port
        self.timeout = timeout

        try:
            self.m =  ModbusClient(host=self.host, port=self.port, unit_id=1, auto_open=True)
        except Exception as e:
            print(f"Datexel 8017 connection failed on {self.host}: {e}")

    def read_all(self):
        '''Read all channels.'''
        try:
            values = self.m.read_input_registers(40,8)  # read all 8 channels starting at 40
            return values

        except Exception as e:
            print(f"Datexel 8017 read failed on {self.host}: {e}")