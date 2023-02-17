from redisproxy.proxy import RedisProxy
from redisproxy.models import AutoOffsetReset
from redisproxy.queueconsumer import QueueConsumerProxy
from redisproxy.channelconsumer import ChannelConsumerProxy
from redisproxy.streamconsumer import StreamConsumerProxy
from redisproxy.protocols import ConsumerProtocol
from typing import cast, Union, Dict

rediscli = RedisProxy()


def runcode() -> None:
    keys = "topic1,topic2,topic3"
    rediscli.delete(keys)
    print("delete old key ok")
    # qc = cast(ConsumerProtocol, QueueConsumerProxy.from_proxy(rediscli, keys))
    # qc = cast(ConsumerProtocol, ChannelConsumerProxy.from_proxy(rediscli, keys))
    # qc = cast(ConsumerProtocol, StreamConsumerProxy.from_proxy(rediscli, keys))
    # qc = cast(ConsumerProtocol, StreamConsumerProxy.from_proxy(rediscli, keys, auto_offset_reset=AutoOffsetReset.earliest))

    client_id = "testnode1"
    group_id = "testgroup1"
    for topic in keys.split(","):
        rediscli.xgroup_destroy(topic, group_id)
        print(f"delete group {group_id} for topic {topic} ok")
        # rediscli.xgroup_create(topic, group_id, mkstream=True)
        rediscli.xgroup_create(topic, group_id, id='0-0', mkstream=True)
        print(f"create group {group_id} for topic {topic} ok")
    # qc = cast(ConsumerProtocol, StreamConsumerProxy.from_proxy(rediscli, keys, client_id=client_id, group_id=group_id))
    qc = cast(ConsumerProtocol, StreamConsumerProxy.from_proxy(rediscli, keys, client_id=client_id, group_id=group_id, auto_offset_reset=AutoOffsetReset.earliest))

    value: Union[str, Dict[str, str]]
    with qc.watch() as records:
        for record in records:
            if isinstance(record.value, bytes):
                value = record.value.decode("utf-8")
            else:
                value = record.value
            print(f"get msg {value} from topic {record.topic}")


def main() -> None:
    rediscli.initialize_from_url("redis://localhost:6379/0?decode_responses=true")
    runcode()


if __name__ == "__main__":
    main()
