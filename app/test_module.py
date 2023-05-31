from softioc import builder

class Device():
    def __init__(self):
        self.pvs = {}
        self.pvs['Test'] = builder.aIn('Test')
        self.pvs['TestOut'] = builder.aOut('TestOut', on_update= self.update_ao)

    async def update_ao(self, value):
        await self.do_set(value)

    def do_set(self, value):
        print(value)