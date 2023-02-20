import asyncio
from redis.commands.core import AsyncDataAccessCommands
from redishelper.proxy import RedisProxy
from typing import cast

rediscli = RedisProxy()


async def runcode() -> None:
    r = cast(AsyncDataAccessCommands, rediscli)
    await r.set('mykey', 'thevalueofmykeyaio')
    res = await r.get('mykey')
    print(res)


rediscli.initialize_from_url("redis+async://localhost:6379/0?decode_responses=true")
asyncio.run(runcode())
