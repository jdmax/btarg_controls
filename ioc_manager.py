from screenutils import Screen
import yaml
from softioc import softioc, builder, asyncio_dispatcher
import asyncio
import re
import time
import os.path
from threading import Thread


async def main():

    with open('screen_config.yaml') as f:  # Load settings from YAML config file
        screen_config = yaml.load(f, Loader=yaml.FullLoader)
    with open('settings.yaml') as f:  # Load settings from YAML config file
        settings = yaml.load(f, Loader=yaml.FullLoader)

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()

    device_name = settings['prefix'] + ':MAN'
    builder.SetDeviceName(device_name)

    i = IOCManager(device_name, settings, screen_config)

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)
    softioc.interactive_ioc(globals())


class IOCManager:
    """
    Handles screens which run iocs. Make PVs to control each ioc.
    """

    def __init__(self, device_name, settings, screen_config):
        """
        Make control PVs for each IOC. "pvs" dict is keyed on name (e.g. flow), PV is labeled as name + 'control' (e.g. flow_control)
        """
        self.device_name = device_name
        self.settings = settings
        self.screen_config = screen_config
        self.pvs = {}
        self.screens = {}     # Dict of all screens made for the iocs, keyed by screen name
        self.screen_pvs = {}  # Dict of lists of all PVs in each screen instance, keyed by screen name


        self.states = [(name,i) for i, name in enumerate(self.settings['states'])]  # make list of tuples for mbbout call
        self.species = [(name,i) for i, name in enumerate(self.settings['species'])]

        for name, value in screen_config['screens'].items():  # each IOC has controls to start, stop or reset
            self.pvs[name] = builder.mbbOut(name + '_control',
                                           ("Stop",0),
                                           ("Start",1),
                                           ("Reset",2),
                                           on_update_name=self.screen_update
                                           )
        self.pv_all = builder.mbbOut('all',
                                       ("Stop",0),
                                       ("Start",1),
                                       ("Reset",2),
                                       on_update=self.all_screen_update
                                       )
        self.pv_spec = builder.mbbOut('species', *self.species, on_update=self.spec_update)
        self.pv_stat = builder.mbbOut('state', *self.states, on_update=self.stat_update)

        self.ioc_regex = re.compile(f'{device_name}')

    def spec_update(self, i, pv):
        """
        Multiple Choice PV has changed for the species
        """

    def stat_update(self, i, pv):
        """
        Multiple Choice PV has changed for the state
        """

    def screen_update(self, i, pv):
        """
        Multiple Choice PV has changed for the given control PV. Follow command. 0=Stop, 1=Start, 2=Reset
        """
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        if i==0:
            self.stop_ioc(pv_name)
        elif i==1:
            if Screen(pv_name).exists:
                #self.reset_ioc(pv_name)   # if it already exists, restart it instead
                pass        # if it already exists, do nothing
            else:
                self.start_ioc(pv_name)
        elif i==2:
            self.reset_ioc(pv_name)

    def all_screen_update(self, i):
        """
        Do update for all iocs in config file.
        """
        for pv in self.screen_config['screens'].keys():
            self.screen_update(i, pv)

    def start_ioc(self, pv_name):
        """
        Start screen to run ioc, then run ioc. Get PV names from IOC after run.
        """
        name = pv_name.replace('_control', '')  # remove suffix from pv name to name screen

        self.st = StartThread(self, name)
        print("Starting thread", name)
        self.st.daemon = True
        self.st.start()

    def stop_ioc(self, pv_name):
        """
        Kill screen and ioc running within it.
        """
        name = pv_name.replace('_control', '')  # remove suffix from pv name to name screen

        print('Starting to kill', name)
        if Screen(name).exists:
            #Screen(name).kill()
            Screen(name).send_commands(f'screen - X - S {name} kill')
            print('Killing', name)
            self.pvs[name].set(0)
        if name in self.screens:
            del self.screens[name]

    def reset_ioc(self, pv_name):
        """
        Kill screen and ioc running within it, then restart.
        """
        name = pv_name.replace('_control', '')  # remove suffix from pv name to name screen

        self.stop_ioc(pv_name)
        self.start_ioc(pv_name)


class StartThread(Thread):
    '''Thread to interact with IOCs in screens. Each thread starts one ioc.'''

    def __init__(self, parent, name):
        Thread.__init__(self)
        self.parent = parent
        self.name = name

        print("Init thread", self.name)
    def run(self):
        '''
        Start screen to run ioc, then run ioc. Wait until started, then get PV names from IOC after run.
        '''
        screen = Screen(self.name, True)

        screen.send_commands('bash')
        screen.send_commands(f'python {self.parent.screen_config["screens"][self.name]["exec"]}')
        screen.enable_logs(self.parent.screen_config['screens'][self.name]['log_file'])
        screen.send_commands('softioc.dbl()')

        elapsed = 0
        pvs = []
        while True:           # wait until ioc starts to get response
            print("Waiting for logfile for", self.name)
            if os.path.getsize(self.parent.screen_config['screens'][self.name]['log_file']) > 200:
                with open(self.parent.screen_config['screens'][self.name]['log_file']) as f:
                    for line in f:
                        match = re.search(f'({self.parent.device_name}.+)\s', line)
                        if match:
                            pvs.append(match.group(0))
                self.parent.pvs[self.name].set(1)
                print(pvs)
                break
            time.sleep(1)
            elapsed += 1
            if elapsed > 20:
                print("Failed to start ioc, died waiting on log file.", self.name)
                break

if __name__ == "__main__":
    asyncio.run(main())