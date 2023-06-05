import asyncio
from zaber_motion import Units
from zaber_motion.ascii import Connection
from softioc import builder


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

        for channel in settings['channels'].keys():  # set up PVs for each channel, calibrations are values of dict
            if "None" in channel: continue
            self.pvs[channel+"_VI"] = builder.aIn(channel+"_VI")
            self.pvs[channel+"_VC"] = builder.aOut(channel+"_VC", on_update_name=self.do_sets)
            self.pvs[channel+"_home"] = builder.aOut(channel+"_home", on_update_name=self.do_sets)
            self.pvs[channel+"_away"] = builder.aOut(channel+"_away", on_update_name=self.do_sets)
            self.pvs[channel+"_stop"] = builder.aOut(channel+"_stop", on_update_name=self.do_sets)

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
        chan = str(self.channels.index(pv_name) + 1)
        try:
            if '_VC' in pv_name:  # valve controller commands
                value = await self.t.move_to(chan, new_value)
                self.pvs[p+"_VI"].set(value)  # set returned value
            if '_home' in pv_name:
                value = await self.t.home(chan)
                self.pvs[p+"_VI"].set(value)  # set returned value
            if '_away' in pv_name:
                value = await self.t.away(chan)
                self.pvs[p+"_VI"].set(value)  # set returned value
            if '_stop' in pv_name:
                value = await self.t.stop(chan)
                self.pvs[p+"_VI"].set(value)  # set returned value
        except OSError:
            self.reconnect()
        return

    def do_reads(self):
        '''Match variables to methods in device driver and get reads from device. Set to PVs.'''
        try:
            new_reads = {}
            for i, channel in enumerate(self.channels):
                if "None" in channel: continue
                new_reads[channel] = self.t.get_pos(i+1)

            for key, value in new_reads.items():
                self.pvs[key].set(value)
        except OSError:
            self.reconnect()
        return


class DeviceConnection():
    '''Handle connection to Zaber motor controller for all axes
    '''

    def __init__(self, host):
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


    async def get_pos(self, axis, location):
        return await self.axes[axis].get_position()

    async def move_to(self, axis, location):
        await self.axes[axis].move_absolute(location, Units.ANGLE_DEGREES)
        return await self.get_pos(axis)

    async def move_relative(self, axis, degrees):
        await self.axes[axis].move_relative(degrees, Units.ANGLE_DEGREES)
        return await self.get_pos(axis)

    async def stop(self, axis):
        await self.axes[axis].stop()
        return await self.get_pos(axis)

    async def home(self, axis):
        await self.axes[axis].home()
        return await self.get_pos(axis)

    async def away(self, axis):
        await self.axes[axis].generic_command('tools gotolimit away pos 1 0')
        return await self.get_pos(axis)

# from zaber example:
#axis1_coroutine = axis1.move_absolute_async(3, Units.LENGTH_CENTIMETRES)
#axis2_coroutine = axis2.move_absolute_async(3, Units.LENGTH_CENTIMETRES)

#move_coroutine = asyncio.gather(axis1_coroutine, axis2_coroutine)

#loop = asyncio.get_event_loop()
#loop.run_until_complete(move_coroutine)