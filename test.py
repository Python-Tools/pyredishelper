from redis.commands.core import DataAccessCommands
from redisproxy import RedisProxy
from typing import cast

rediscli = RedisProxy()


def runcode() -> None:
    r = cast(DataAccessCommands, rediscli)
    r.set('mykey', 'thevalueofmykey')
    res = r.get('mykey')
    print(res)


rediscli.initialize_from_url("redis://localhost:6379/0?decode_responses=true")
runcode()
