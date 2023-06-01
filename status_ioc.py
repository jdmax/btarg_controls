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

    device_name = settings['all_iocs']['prefix'] + ':STAT'
    builder.SetDeviceName(device_name)

    i = StatusIOC(settings, states)

    builder.LoadDatabase()
    softioc.iocInit(dispatcher)

    #async def loop():
    #    while True:
    #       pass
        #   await d.loop()

    #dispatcher(loop)  # put functions to loop in here
    softioc.interactive_ioc(globals())


class StatusIOC:
    """
    Handles status changes. Make PVs to control each states changes.
    """

    def __init__(self, settings, states):
        """
        Make control PVs for status changes
        """
        self.settings = settings
        self.states = states
        self.pvs = {}
        self.status = self.states['options']['status']
        self.species = self.states['options']['species']

        status_list = [[name,i] for i, name in enumerate(self.status)]  # make list of tuples for mbbout call
        species_list = [[name,i] for i, name in enumerate(self.species)]

        self.pvs['status'] = builder.mbbOut('status', *status_list, on_update_name=self.stat_update)
        self.pvs['species'] = builder.mbbOut('species', *species_list, on_update_name=self.stat_update)


    def stat_update(self, i, pv):
        """
        Multiple Choice PV has changed for the state or species
        """
        print(i,pv)
        self.pv_spec.get()][0]
        state = self.states[self.pv_stat.get()][0]
        print(state,species)





if __name__ == "__main__":
    asyncio.run(main())