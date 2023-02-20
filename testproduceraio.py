from pyredishelper.proxy import RedisProxy
from pyredishelper.protocols import AioProducerProtocol, AioStreamProducerProtocol
from pyredishelper.queueproducer import QueueProducerHelper
from pyredishelper.channelproducer import ChannelProducerHelper
from pyredishelper.streamproducer import StreamProducerHelper
from typing import cast
import asyncio

rediscli = RedisProxy()


async def runcode() -> None:
    # qp = cast(AioProducerProtocol, QueueProducerHelper.from_proxy(rediscli))
    # qp = cast(AioProducerProtocol, ChannelProducerHelper.from_proxy(rediscli))
    qp = cast(AioStreamProducerProtocol, StreamProducerHelper.from_proxy(rediscli, maxlen=20))
    async with qp.mount() as producer:
        for i in range(10):
            topicnum = i % 3 + 1
            # await producer.publish(f"topic{topicnum}",  f"test {i}"})
            await producer.publish(f"topic{topicnum}", {"key": "a key", "value": f"{i}y"})
            print(f"send test{i} to topic{topicnum}")
            await asyncio.sleep(0.1)


async def main() -> None:
    rediscli.initialize_from_url("redis+async://localhost:6379/0?decode_responses=true")
    await runcode()


if __name__ == "__main__":
    asyncio.run(main())
