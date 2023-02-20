from pyredishelper.proxy import RedisProxy
from pyredishelper.protocols import ProducerProtocol, StreamProducerProtocol
from pyredishelper.queueproducer import QueueProducerHelper
from pyredishelper.channelproducer import ChannelProducerHelper
from pyredishelper.streamproducer import StreamProducerHelper
from typing import cast
import time

rediscli = RedisProxy()


def runcode() -> None:
    # qp = cast(ProducerProtocol, QueueProducerHelper.from_proxy(rediscli))
    # qp = cast(ProducerProtocol, ChannelProducerHelper.from_proxy(rediscli))
    qp = cast(StreamProducerProtocol, StreamProducerHelper.from_proxy(rediscli, maxlen=20))
    with qp.mount() as producer:
        for i in range(10):
            topicnum = i % 3 + 1
            producer.publish(f"topic{topicnum}", {"key": "a key", "value": f"{i}x"})
            print(f"send test{i} to topic{topicnum}")
            time.sleep(0.1)


def main() -> None:
    rediscli.initialize_from_url("redis://localhost:6379/0?decode_responses=true")
    runcode()


if __name__ == "__main__":
    main()
