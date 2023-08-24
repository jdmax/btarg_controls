import yaml
from softioc import builder, alarm
from aioca import caget, caput, camonitor, connect
import asyncio


class Device():
    """
    SoftIOC to handle status changes. Makes PVs to control changes of state and species.
    """

    def __init__(self, device_name, settings):
        """
        Make control PVs for status changes
        """
        self.settings = settings
        self.device_name = device_name

        with open('states.yaml') as f:  # Load states from YAML config file
            self.states = yaml.safe_load(f)

        self.pvs = {}
        self.status = self.states['options']['status']
        self.species = self.states['options']['species']

        status_list = [[name,0] for i, name in enumerate(self.status)]  # make list of tuples for mbbout call
        species_list = [[name,0] for i, name in enumerate(self.species)]
        pvlist = []
        for status in self.status:
            for pv in self.states[status]:
                #if isinstance(self.states[status][pv][self.species[0]], list):
                pvlist.append(pv)
        self.watchlist = set(pvlist)
        #print(self.watchlist)

        self.pvs['status'] = builder.mbbOut('status', *status_list, on_update_name=self.stat_update)  # come from states.yaml
        self.pvs['species'] = builder.mbbOut('species', *species_list, on_update_name=self.stat_update)


    async def stat_update(self, i, pv):
        """
        Multiple Choice PV has changed for the state or species. Go through and caput changes from states file.
        """
        #pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        j = self.pvs['status'].get()
        k = self.pvs['species'].get()
        status = self.states['options']['status'][j]
        species = self.states['options']['species'][k]

        group = []
        for pv in self.states[status]:  # set values and alarms for this state. Adds all puts to a group and runs concurrently.
            if isinstance(self.states[status][pv][species], list):
                group.append(self.try_put(pv+'.HIHI', self.states[status][pv][species][0]))
                group.append(self.try_put(pv+'.HIGH', self.states[status][pv][species][1]))
                group.append(self.try_put(pv+'.LOW', self.states[status][pv][species][2]))
                group.append(self.try_put(pv+'.LOLO', self.states[status][pv][species][3]))
            else:
                group.append(self.try_put(pv, self.states[status][pv][species]))
        await asyncio.gather(*group)   # Run group concurrently

        # write out to file
        last = {'status': j, 'species': k}
        with open('last.yaml', 'w') as f:  # Dump this setting to file
            yaml.dump(last, f)

    async def try_put(self, pv, value):
        try:
            await caput(pv, value)
        except Exception as e:
            print(e)

    def connect(self):
        '''Restore state to last used, or default if none'''
        try:
            with open('last.yaml') as f:  # Load last settings from yaml
                last = yaml.safe_load(f)
        except FileNotFoundError:
            last = {'status': 0, 'species': 0}

        for pv in last:      # set to PVs
            self.pvs[pv].set(last[pv])
        self.stat_update(0, 'pv')
        print('Restored previous state:', last)

    def do_reads(self):
        '''This IOC doesn't use reads'''
        pass