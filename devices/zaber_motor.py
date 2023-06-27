import asyncio
from zaber_motion import Units
from zaber_motion.ascii import Connection
from softioc import builder, alarm
from time import sleep


class Device():
    """Makes library of PVs needed for Zaber Motor Controller and provides methods connect them to the device

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
        sevr = {'HHSV': 'MAJOR', 'HSV': 'MINOR', 'LSV': 'MINOR', 'LLSV': 'MAJOR', 'DISP': '0'}

        for channel in settings['channels']:  # set up PVs for each channel, calibrations are values of dict
            if "None" in channel: continue
            self.pvs[channel+"_VI"] = builder.aIn(channel+"_VI", **sevr)
            self.pvs[channel+"_VC"] = builder.aOut(channel+"_VC", on_update_name=self.do_sets, **sevr)
            self.pvs[channel+"_home"] = builder.boolOut(channel+"_home", on_update_name=self.do_sets)
            self.pvs[channel+"_away"] = builder.boolOut(channel+"_away", on_update_name=self.do_sets)
            self.pvs[channel+"_stop"] = builder.boolOut(channel+"_stop", on_update_name=self.do_sets)

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
        """Set Zaber MCC states"""
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        p = pv_name.split("_")[0]  # pv_name root
        chan = self.channels.index(p)
        try:
            if '_VC' in pv_name:  # valve controller commands
                self.pvs[p+"_VI"].set(self.t.move_to(chan, new_value))  # set returned value
            elif '_home' in pv_name:
                if new_value:
                    self.pvs[p+"_VI"].set(self.t.home(chan))  # set returned value
                    self.pvs[p+"_home"].set(False)
            elif '_away' in pv_name:
                if new_value:
                    self.pvs[p+"_VI"].set(self.t.away(chan))  # set returned value
                    self.pvs[p+"_away"].set(False)
            elif '_stop' in pv_name:
                if new_value:
                    self.pvs[p+"_VI"].set(self.t.stop(chan))  # set returned value
                    self.pvs[p+"_stop"].set(False)
        except OSError:
            self.reconnect()
        return

    def do_reads(self):
        '''Match variables to methods in device driver and get reads from device. Set to PVs.'''
        try:
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                self.pvs[channel+"_VI"].set(self.t.get_pos(i))
                self.remove_alarm(channel + '_VI')
        except OSError:
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                self.set_alarm(channel + '_VI')
            self.reconnect()
        return

    def set_alarm(self, channel):
        """Set alarm and severity for channel"""
        self.pvs[channel].set_alarm(severity=1, alarm=alarm.READ_ALARM)

    def remove_alarm(self, channel):
        """Remove alarm and severity for channel"""
        self.pvs[channel].set_alarm(severity=0, alarm=alarm.NO_ALARM)


class DeviceConnection():
    '''Handle connection to Zaber motor controller for all axes
    '''

    def __init__(self, host, port, timeout):
        '''Open connection to motor controller
        Arguments:
            host: IP address
            port: Port of device
            timeout: Telnet timeout in secs
        '''
        self.host = host
        self.axes = []

        try:
            self.con = Connection.open_tcp(host, Connection.TCP_PORT_CHAIN)
            device_list = self.con.detect_devices()
            device = device_list[0]
            for i in range(0, device.axis_count):
                self.axes.append(device.get_axis(i+1))
        except Exception as e:
            print(f"Zaber motor connection failed on {self.host}: {e}")


    def get_pos(self, axis):   # not async! Wait until not busy, then return position
        while self.axes[axis].is_busy():
            sleep(0.2)
        return self.axes[axis].get_position(Units.ANGLE_DEGREES)

    def move_to(self, axis, location):
        self.axes[axis].move_absolute(location, Units.ANGLE_DEGREES)
        return self.get_pos(axis)

    def move_relative(self, axis, degrees):
        self.axes[axis].move_relative(degrees, Units.ANGLE_DEGREES)
        return self.get_pos(axis)

    def stop(self, axis):
        self.axes[axis].stop()
        return self.get_pos(axis)

    def home(self, axis):
        self.axes[axis].home()
        return self.get_pos(axis)

    def away(self, axis):
        self.axes[axis].generic_command('tools gotolimit away pos 1 0')
        return self.get_pos(axis)
