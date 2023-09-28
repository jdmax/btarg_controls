import yaml
from softioc import builder, alarm
import aioca
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

#        pvlist = []
#        for status in self.status:
#            for pv in self.states[status]:
#                #if isinstance(self.states[status][pv][self.species[0]], list):
#                pvlist.append(pv)
#        self.watchlist = set(pvlist)

        self.pvs['status'] = builder.mbbOut('status', *self.status, on_update_name=self.stat_update)  # come from states.yaml
        self.pvs['species'] = builder.mbbOut('species', *self.species, on_update_name=self.stat_update)

        prod_states = ['Empty', 'Full', 'Solid', 'Full+Solid', 'Not Ready']
        self.pvs['production'] = builder.mbbIn('production', *prod_states)

        flag_states = ['Empty', 'Cu-Sn', 'Carbon']
        self.pvs['flag'] = builder.mbbIn('Flag_state', *flag_states)



    async def stat_update(self, i, pv):
        """
        Multiple Choice PV has changed for the state or species. Go through and caput changes from states file.
        """
        #pv_name = pv.replace(self.device_name + ':', '')  # remove device name from PV to get bare pv_name
        j = self.pvs['status'].get()
        k = self.pvs['species'].get()
        status = self.states['options']['status'][j]
        species = self.states['options']['species'][k]

        print("Changing status to", status, species)

        group = []
        for pv in self.states[status]:  # set values and alarms for this state. Adds all puts to a group and runs concurrently.
            if isinstance(self.states[status][pv][species], list):
                group.append(self.try_put(pv+'.HIHI', self.states[status][pv][species][0]))
                group.append(self.try_put(pv+'.HIGH', self.states[status][pv][species][1]))
                group.append(self.try_put(pv+'.LOW', self.states[status][pv][species][2]))
                group.append(self.try_put(pv+'.LOLO', self.states[status][pv][species][3]))
            else:
                group.append(self.try_put(pv, self.states[status][pv][species]))
                #await self.try_put(pv, self.states[status][pv][species])
        await asyncio.gather(*group)   # Run group concurrently

        # write out to file
        last = {'status': j, 'species': k}
        with open('last.yaml', 'w') as f:  # Dump this setting to file
            yaml.dump(last, f)

        print("Change done.", status, species)

    async def try_put(self, pv, value):
        try:
            await aioca.caput(self.device_name + ":" + pv, value)
        except aioca.CANothing as e:
            print("Put error:", e, self.device_name + ":" + pv, value)

    async def connect(self):
        '''Restore state to last used, or default if none'''
        try:
            with open('last.yaml') as f:  # Load last settings from yaml
                last = yaml.safe_load(f)
        except FileNotFoundError:
            last = {'status': 0, 'species': 0}

        for pv in last:      # set to PVs
            self.pvs[pv].set(last[pv])
        #await self.stat_update(0, 'pv')

        print('Restored previous state:', last)

    async def do_reads(self):
        '''Read status from other PVs to determine production status'''
        if self.settings['prod_pv']:
            try:
                group = []
                c = {}    # dict of current status keyed on PV name
                full_status = []
                for pvname in self.settings['full_status']:
                    group.append(self.a_get(c, pvname+'.STAT'))
                    full_status.append(pvname+'.STAT')
                group.append(self.a_get(c, 'TGT:BTARG:Flag_MI'))
                group.append(self.a_get(c, 'TGT:BTARG:Flag_pos_1'))   # left flag
                group.append(self.a_get(c, 'TGT:BTARG:Flag_pos_2'))   # right flag
                await asyncio.gather(*group)

                if c['TGT:BTARG:Flag_MI'] < c['TGT:BTARG:Flag_pos_1'] + 1:
                    self.pvs['flag'].set(1)
                elif c['TGT:BTARG:Flag_MI'] > c['TGT:BTARG:Flag_pos_2'] - 1:
                    self.pvs['flag'].set(2)
                else:
                    self.pvs['flag'].set(0)

                stat = self.status[self.pvs['status'].get()]

                not_alarming = True
                for pv in full_status:
                    if not c[pv] == 0:
                        not_alarming = False
                if not_alarming:
                    if self.pvs['flag'].get() == 0:
                        if 'Empty' in stat:
                            self.pvs['production'].set(0)  # Empty
                        elif 'Fill' in stat:
                            self.pvs['production'].set(1)  # Full
                    else:
                        if 'Empty' in stat:
                            self.pvs['production'].set(2)  # Empty + Solid
                        elif 'Fill' in stat:
                            self.pvs['production'].set(3)  # Full + Solid
                else:
                    self.pvs['production'].set(4)    # Not Ready
            except aioca.CANothing as e:
                print("Caget error:", e)
                self.pvs['production'].set(4, severity=2, alarm=alarm.STATE_ALARM)
                self.pvs['flag'].set_alarm(severity=2, alarm=alarm.STATE_ALARM)
            except Exception as e:
                print("Production status determination error:", e)
                self.pvs['production'].set(4, severity=2, alarm=alarm.STATE_ALARM)
                self.pvs['flag'].set_alarm(severity=2, alarm=alarm.STATE_ALARM)

        return True

    async def a_get(self, dict, pv):
        '''Put pv status from aioca get in passed dict'''
        dict[pv] = await aioca.caget(pv)