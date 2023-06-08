from pyModbusTCP.client import ModbusClient
from softioc import builder

class Device():
    """Makes library of PVs needed for DAT8130 and provides methods connect them to the device

    Attributes:
        pvs: dict of Process Variables keyed by name
        channels: channels of device
        new_reads: dict of most recent reads from device to set into PVs
    """

    def __init__(self, device_name, settings):
        '''Make PVs needed for this device and put in pvs dict keyed by name
        '''
        self.device_name = device_name
        self.settings = settings
        self.channels = settings['channels']
        self.pvs = {}
        self.new_reads = {}
        self.calibs = {}

        for i, channel in enumerate(settings['channels']):  # set up PVs for each channel, calibrations are values of dict
            if "None" in channel: continue
            if i < 4:   # Digital OUT channels first
                self.pvs[channel] = builder.boolOut(channel, on_update_name=self.do_sets)
            else:    # Digital IN next
                self.pvs[channel] = builder.aIn(channel)

    def connect(self):
        '''Open connection to device'''
        try:
            self.t = DeviceConnection(self.settings['ip'], self.settings['port'], self.settings['timeout'])
        except Exception as e:
            print(f"Failed connection on {self.settings['ip']}, {e}")

    def reconnect(self):
        del self.t
        print("Connection failed. Attempting reconnect.")
        self.connect()

    def do_sets(self, new_value, pv):
        """Set DO state"""
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        chan = str(self.channels.index(pv_name) + 1)
        try:
            values = self.t.switch(new_value, chan)
            self.pvs[pv_name].set(values[int(chan)-1])  # set returned value
        except OSError:
            self.reconnect()

    def do_reads(self):
        '''Match variables to methods in device driver and get reads from device'''
        try:
            new_reads = {}
            readings = self.t.read_all()
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                new_reads[channel] = readings[i] * self.calibs[channel]

            for key, value in new_reads.items():
                self.pvs[key].set(value)
        except OSError:
            self.reconnect()
        return


class DeviceConnection():
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
            print(f"Datexel 8130 connection failed on {self.host}: {e}")

    def read_all(self):
        '''Read all channels.'''
        try:
            values = self.m.read_input_registers(504,8)  # read all 8 channels starting at 40
            return values

        except Exception as e:
            print(f"Datexel 8130 read failed on {self.host}: {e}")
            raise OSError('8130 read')


    def switch(self, channel, state):
        '''Flip channel to state. DO channels from 0 to 3'''
        try:
            self.m.write_single_coil(488+channel, state)
            values = self.m.read_input_registers(488,4)  # read all 4 channels
            return values

        except Exception as e:
            print(f"Datexel 8130 write failed on {self.host}: {e}")
            raise OSError('8130 write')