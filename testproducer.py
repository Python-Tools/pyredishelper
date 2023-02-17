from redisproxy.proxy import RedisProxy
from redisproxy.protocols import ProducerProtocol, StreamProducerProtocol
from redisproxy.queueproducer import QueueProducerProxy
from redisproxy.channelproducer import ChannelProducerProxy
from redisproxy.streamproducer import StreamProducerProxy
from typing import cast
import time

rediscli = RedisProxy()


def runcode() -> None:
    # qp = cast(ProducerProtocol, QueueProducerProxy.from_proxy(rediscli))
    # qp = cast(ProducerProtocol, ChannelProducerProxy.from_proxy(rediscli))
    qp = cast(StreamProducerProtocol, StreamProducerProxy.from_proxy(rediscli, maxlen=20))
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
