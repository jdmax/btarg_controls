import yaml
from softioc import softioc, builder, asyncio_dispatcher
import asyncio
from aioca import caget, caput, camonitor


async def main():

    with open('settings.yaml') as f:  # Load settings from YAML config file
        settings = yaml.load(f, Loader=yaml.FullLoader)
    with open('states.yaml') as f:  # Load states from YAML config file
        states = yaml.load(f, Loader=yaml.FullLoader)

    dispatcher = asyncio_dispatcher.AsyncioDispatcher()

    device_name = settings['general']['prefix'] + ':STAT'
    builder.SetDeviceName(device_name)

    i = StatusIOC(device_name, settings, states)

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    softioc.interactive_ioc(globals())


class StatusIOC:
    """
    Handles status changes. Make PVs to control each states changes.
    """

    def __init__(self, device_name, settings, states):
        """
        Make control PVs for status changes
        """
        self.settings = settings
        self.states = states
        self.device_name = device_name
        self.pvs = {}
        self.status = self.states['options']['status']
        self.species = self.states['options']['species']

        status_list = [[name,i] for i, name in enumerate(self.status)]  # make list of tuples for mbbout call
        species_list = [[name,i] for i, name in enumerate(self.species)]
        pvlist = []
        for status in self.states['options']['status']:
            for pv in self.states[status]:
                if isinstance(self.states[status][pv][self.states['options']['species'][0]], list):
                    pvlist.append(pv)
        self.watchlist = set(pvlist)
        print(self.watchlist)

        self.pvs['status'] = builder.mbbOut('status', *status_list, on_update_name=self.stat_update)
        self.pvs['species'] = builder.mbbOut('species', *species_list, on_update_name=self.stat_update)


    async def stat_update(self, i, pv):
        """
        Multiple Choice PV has changed for the state or species
        """
        pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        print(i,pv, pv_name)
        status = self.states['options']['status'][i]
        species = self.states['options']['species'][i]

        for pv in self.states[status]:  # set values and alarms for this state
            if isinstance(self.states[status][pv][species], list):
                await caput(pv+'.HIHI', self.states[status][pv][species][0])
                await caput(pv+'.HIGH', self.states[status][pv][species][1])
                await caput(pv+'.LOW', self.states[status][pv][species][2])
                await caput(pv+'.HIHI', self.states[status][pv][species][3])
            else:
                await caput(pv, self.states[status][pv][species])


if __name__ == "__main__":
    asyncio.run(main())