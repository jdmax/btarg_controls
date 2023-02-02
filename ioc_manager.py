from screenutils import Screen
import yaml
from softioc import softioc, builder, asyncio_dispatcher
import asyncio


async def main():

    with open('screen_config.yaml') as f:  # Load settings from YAML config file
        screen_config = yaml.load(f, Loader=yaml.FullLoader)
    with open('settings.yaml') as f:  # Load settings from YAML config file
        settings = yaml.load(f, Loader=yaml.FullLoader)

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()

    device_name = settings['prefix'] + ':MAN'
    builder.SetDeviceName(device_name)

    i = IOCManager(device_name, screen_config)

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    softioc.interactive_ioc(globals())


class IOCManager:
    """
    Handles screens which run iocs. Make PVs to control each ioc.
    """

    def __init__(self, device_name, screen_config):
        """
        Make control PVs for each IOC
        """
        self.device_name = device_name
        self.pvs = {}
        self.screens = {}    # Dict of all screens made for the iocs
        for key, value in screen_config.items():  # each IOC has controls to start, stop or reset
            self.pvs[key] = builder.mbbOut(key + '_control',
                                           ("Start",0),
                                           ("Stop",1),
                                           ("Reset",2),
                                           on_update_name=self.update
                                           )

    def update(self, i, pv):
        """
        Multiple Choice has changed, do the command. 0=Start, 1=Stop, 2=Reset
        """
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        if i==0:
            self.start_ioc(pv_name)

    def start_ioc(self, pv_name):
        """
        Start screen to run ioc, then run ioc.
        """
        screen_name = pv_name.replace('_control', '')  # remove suffix from pv name to name screen
        self.screens[screen_name] = Screen(screen_name, True)

        self.screens[screen_name].send_commands()  # first need to enter virtual environment to run, then start ioc


if __name__ == "__main__":
    asyncio.run(main())