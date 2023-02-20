from pyredishelper.proxy import RedisProxy
from pyredishelper.models import AutoOffsetReset
from pyredishelper.queueconsumer import QueueConsumerHelper
from pyredishelper.channelconsumer import ChannelConsumerHelper
from pyredishelper.streamconsumer import StreamConsumerHelper
from pyredishelper.protocols import AioConsumerProtocol
from typing import cast, Union, Dict
import asyncio

rediscli = RedisProxy()


async def runcode() -> None:
    keys = "topic1,topic2,topic3"
    await rediscli.delete(keys)
    print("delete old key ok")
    # qc = cast(AioConsumerProtocol, QueueConsumerHelper.from_proxy(rediscli, keys))
    # qc = cast(AioConsumerProtocol, ChannelConsumerHelper.from_proxy(rediscli, keys))
    # qc = cast(AioConsumerProtocol, StreamConsumerHelper.from_proxy(rediscli, keys))
    # qc = cast(AioConsumerProtocol, StreamConsumerHelper.from_proxy(rediscli, keys, auto_offset_reset=AutoOffsetReset.earliest))

    client_id = "testnode1"
    group_id = "testgroup1"
    for topic in keys.split(","):
        await rediscli.xgroup_destroy(topic, group_id)
        print(f"delete group {group_id} for topic {topic} ok")
        # rediscli.xgroup_create(topic, group_id, mkstream=True)
        await rediscli.xgroup_create(topic, group_id, id='0-0', mkstream=True)
        print(f"create group {group_id} for topic {topic} ok")
    qc = cast(AioConsumerProtocol, StreamConsumerHelper.from_proxy(rediscli, keys, client_id=client_id, group_id=group_id))
    # qc = cast(AioConsumerProtocol, StreamConsumerHelper.from_proxy(rediscli, keys, client_id=client_id, group_id=group_id, auto_offset_reset=AutoOffsetReset.earliest))

    value: Union[str, Dict[str, str]]
    async with qc.watch() as records:
        async for record in records:
            if isinstance(record.value, bytes):
                value = record.value.decode("utf-8")
            else:
                value = record.value
            print(f"get msg {value} from topic {record.topic}")


async def main() -> None:
    rediscli.initialize_from_url("redis+async://localhost:6379/0?decode_responses=true")
    await runcode()


if __name__ == "__main__":
    asyncio.run(main())
