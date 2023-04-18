import asyncio
import zaber_motion

# from zaber example:
axis1_coroutine = axis1.move_absolute_async(3, Units.LENGTH_CENTIMETRES)
axis2_coroutine = axis2.move_absolute_async(3, Units.LENGTH_CENTIMETRES)

move_coroutine = asyncio.gather(axis1_coroutine, axis2_coroutine)

loop = asyncio.get_event_loop()
loop.run_until_complete(move_coroutine)