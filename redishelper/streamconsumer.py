from .proxy import RedisProxy
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Optional, Union, Generator, AsyncGenerator, AsyncIterable, Iterable, cast, Dict
from types import MethodType
from redis import Redis
from redis.cluster import RedisCluster
from redis.asyncio import Redis as AioRedis
from .models import ConsumerRecord, AutoOffsetReset, Acks

from redis.commands.core import AsyncDataAccessCommands, DataAccessCommands


class StreamConsumerHelper(RedisProxy):
    __slots__ = ('instance', "_callbacks", "_instance_check", "_aio", "_cluster", "watch", "_topics",
                 "_auto_offset_reset", "_count", "_blocktime",
                 "_client_id", "_group_id", "_ack")

    def __init__(self, topics: str, *, url: Optional[str] = None, addresses: Optional[str] = None, aio: Optional[bool] = None,
                 auto_offset_reset: AutoOffsetReset = AutoOffsetReset.latest, count: Optional[int] = 1, blocktime: Optional[int] = 1000,
                 client_id: Optional[str] = None, group_id: Optional[str] = None, ack: Acks = Acks.after,
                 **conn_params: Any) -> None:
        """Stream结构的消费者代理.

        Args:
            topics (str): 监听的stream名,以","分隔
            url (Optional[str], optional): 适用于非集群redis的请求url. Defaults to None.
            addresses (Optional[str], optional): 适用于集群redis的以,分隔的地址序列. Defaults to None.
            aio (Optional[bool], optional): 是否异步接口. Defaults to None.
            auto_offset_reset (AutoOffsetReset, optional): 监听的开始位置. Defaults to AutoOffsetReset.latest.
            count (Optional[int], optional): 一次监听获取的最大消息个数. Defaults to 1.
            blocktime (Optional[int], optional): 一次监听的最大等待时间. Defaults to 1000.
            client_id (Optional[str], optional): 客户端id,如果要用group模式监听数据则必填. Defaults to None.
            group_id (Optional[str], optional): group id,如果要用group模式监听数据则必填. Defaults to None.
            ack (Acks, optional): group模式下确认消息已读取的策略. Defaults to Acks.after.
            conn_params (Any): 其他连接选项.
        """
        self._auto_offset_reset = auto_offset_reset
        self._count = count
        self._blocktime = blocktime
        self._client_id = client_id
        self._group_id = group_id
        self._ack = ack
        self._topics: Dict[str, Union[int, str]]
        if auto_offset_reset is AutoOffsetReset.earliest:
            self._topics = {topic: "0" for topic in topics.split(",")}
        else:
            if client_id and group_id:
                self._topics = {topic: ">" for topic in topics.split(",")}
            else:
                self._topics = {topic: "$" for topic in topics.split(",")}
        super().__init__()
        self.attach_callback(self.regist_methods)
        self.attach_instance_check(lambda x: isinstance(x, (Redis, RedisCluster, AioRedis)))
        if url:
            self.initialize_from_url(url, **conn_params)
        elif addresses:
            if aio is None:
                _aio = False
            else:
                _aio = aio
            self.initialize_from_addresses(addresses, aio=_aio, **conn_params)

    def regist_methods(self, instance: Any) -> None:
        if self._aio:
            self.watch = MethodType(_watch_async, self)
        else:
            self.watch = MethodType(_watch_sync, self)

    async def _watch_async(self) -> AsyncGenerator[ConsumerRecord, None]:
        c = cast(AsyncDataAccessCommands, self.instance)
        if self._group_id and self._client_id:
            if self._auto_offset_reset is AutoOffsetReset.latest:
                while True:
                    streams_message = await c.xreadgroup(self._group_id, self._client_id, streams=self._topics, count=self._count, block=self._blocktime, noack=False)
                    if not streams_message:
                        continue
                    for topic, messages in streams_message:
                        if not messages:
                            continue
                        for offset, message in messages:
                            ts = int(offset.split("-")[0])
                            value = {key if isinstance(key, str) else key.encode("utf-8"): m if isinstance(m, str) else m.encode("utf-8") for key, m in message.items()}
                            record = ConsumerRecord(topic=topic, value=value, offset=offset, timestamp=ts)
                            yield record
            else:
                while True:
                    streams_message = await c.xreadgroup(self._group_id, self._client_id, streams=self._topics, count=self._count, block=None, noack=True)
                    if not streams_message:
                        continue
                    for topicb, messages in streams_message:
                        if not messages:
                            continue
                        topic = topicb if isinstance(topicb, str) else topicb.encode("utf-8")
                        if self._ack is Acks.after_batch:
                            offsets = []
                            for offsetb, message in messages:
                                offset = offsetb if isinstance(offsetb, str) else offsetb.encode("utf-8")
                                offsets.append(offset)
                                ts = int(offset.split("-")[0])
                                value = {key if isinstance(key, str) else key.encode("utf-8"): m if isinstance(m, str) else m.encode("utf-8") for key, m in message.items()}
                                record = ConsumerRecord(topic=topic, value=value, offset=offset, timestamp=ts)
                                yield record
                            await c.xack(topic, self._group_id, *offsets)
                        else:
                            for offsetb, message in messages:
                                offset = offsetb if isinstance(offsetb, str) else offsetb.encode("utf-8")
                                if self._ack is Acks.before:
                                    await c.xack(topic, self._group_id, offset)
                                ts = int(offset.split("-")[0])
                                value = {key if isinstance(key, str) else key.encode("utf-8"): m if isinstance(m, str) else m.encode("utf-8") for key, m in message.items()}
                                record = ConsumerRecord(topic=topic, value=value, offset=offset, timestamp=ts)
                                yield record
                                if self._ack is Acks.after:
                                    await c.xack(topic, self._group_id, offset)
        else:
            while True:
                streams_message = await c.xread(streams=self._topics, count=self._count, block=self._blocktime)
                if not streams_message:
                    continue
                for topicb, messages in streams_message:
                    if not messages:
                        continue
                    topic = topicb if isinstance(topicb, str) else topicb.encode("utf-8")
                    latest_offset = ""
                    for offsetb, message in messages:
                        offset = offsetb if isinstance(offsetb, str) else offsetb.encode("utf-8")
                        latest_offset = offset
                        ts = int(offset.split("-")[0])
                        value = {key if isinstance(key, str) else key.encode("utf-8"): m if isinstance(m, str) else m.encode("utf-8") for key, m in message.items()}
                        record = ConsumerRecord(topic=topic, value=value, offset=offset, timestamp=ts)
                        yield record
                    self._topics.update({
                        topic: latest_offset
                    })

    def _watch_sync(self) -> Generator[ConsumerRecord, None, None]:
        c = cast(DataAccessCommands, self.instance)
        if self._group_id and self._client_id:
            if self._auto_offset_reset is AutoOffsetReset.latest:
                while True:
                    streams_message = c.xreadgroup(self._group_id, self._client_id, streams=self._topics, count=self._count, block=self._blocktime, noack=False)
                    if not streams_message:
                        continue
                    for topic, messages in streams_message:
                        if not messages:
                            continue
                        for offset, message in messages:
                            ts = int(offset.split("-")[0])
                            value = {key if isinstance(key, str) else key.encode("utf-8"): m if isinstance(m, str) else m.encode("utf-8") for key, m in message.items()}
                            record = ConsumerRecord(topic=topic, value=value, offset=offset, timestamp=ts)
                            yield record
            else:
                while True:
                    streams_message = c.xreadgroup(self._group_id, self._client_id, streams=self._topics, count=self._count, block=None, noack=True)
                    if not streams_message:
                        continue
                    for topicb, messages in streams_message:
                        if not messages:
                            continue
                        topic = topicb if isinstance(topicb, str) else topicb.encode("utf-8")
                        if self._ack is Acks.after_batch:
                            offsets = []
                            for offsetb, message in messages:
                                offset = offsetb if isinstance(offsetb, str) else offsetb.encode("utf-8")
                                offsets.append(offset)
                                ts = int(offset.split("-")[0])
                                value = {key if isinstance(key, str) else key.encode("utf-8"): m if isinstance(m, str) else m.encode("utf-8") for key, m in message.items()}
                                record = ConsumerRecord(topic=topic, value=value, offset=offset, timestamp=ts)
                                yield record
                            c.xack(topic, self._group_id, *offsets)
                        else:
                            for offsetb, message in messages:
                                offset = offsetb if isinstance(offsetb, str) else offsetb.encode("utf-8")
                                if self._ack is Acks.before:
                                    c.xack(topic, self._group_id, offset)
                                ts = int(offset.split("-")[0])
                                value = {key if isinstance(key, str) else key.encode("utf-8"): m if isinstance(m, str) else m.encode("utf-8") for key, m in message.items()}
                                record = ConsumerRecord(topic=topic, value=value, offset=offset, timestamp=ts)
                                yield record
                                if self._ack is Acks.after:
                                    c.xack(topic, self._group_id, offset)
        else:
            while True:
                streams_message = c.xread(streams=self._topics, count=self._count, block=self._blocktime)
                if not streams_message:
                    continue
                for topicb, messages in streams_message:
                    if not messages:
                        continue
                    topic = topicb if isinstance(topicb, str) else topicb.encode("utf-8")
                    latest_offset = ""
                    for offsetb, message in messages:
                        offset = offsetb if isinstance(offsetb, str) else offsetb.encode("utf-8")
                        latest_offset = offset
                        ts = int(offset.split("-")[0])
                        value = {key if isinstance(key, str) else key.encode("utf-8"): m if isinstance(m, str) else m.encode("utf-8") for key, m in message.items()}
                        record = ConsumerRecord(topic=topic, value=value, offset=offset, timestamp=ts)
                        yield record
                    self._topics.update({
                        topic: latest_offset
                    })

    @classmethod
    def from_proxy(clz, proxy: RedisProxy, topics: str, *,
                   auto_offset_reset: AutoOffsetReset = AutoOffsetReset.latest, count: Optional[int] = 20, blocktime: Optional[int] = 1000,
                   client_id: Optional[str] = None, group_id: Optional[str] = None, ack: Acks = Acks.after) -> "StreamConsumerHelper":
        """从RedisProxy实例创建代理.

        Args:
            proxy (RedisProxy): RedisProxy的实例
            topics (str): 待监听的频道名列表,以","分隔
             auto_offset_reset (AutoOffsetReset, optional): 监听的开始位置. Defaults to AutoOffsetReset.latest.
            count (Optional[int], optional): 一次监听获取的最大消息个数. Defaults to 1.
            blocktime (Optional[int], optional): 一次监听的最大等待时间. Defaults to 1000.
            client_id (Optional[str], optional): 客户端id,如果要用group模式监听数据则必填. Defaults to None.
            group_id (Optional[str], optional): group id,如果要用group模式监听数据则必填. Defaults to None.
            ack (Acks, optional): group模式下确认消息已读取的策略. Defaults to Acks.after.

        Returns:
            StreamConsumerProxy: 满足protocols.ConsumerProtocol或者protocols.AioConsumerProtocol协议的消费者代理对象
        """
        p = clz(topics, auto_offset_reset=auto_offset_reset, count=count, blocktime=blocktime, client_id=client_id, group_id=group_id, ack=ack)
        if proxy.instance is not None:
            p._aio = proxy.aio
            p._cluster = proxy.cluster
            p.initialize(proxy.instance)
        return p


@asynccontextmanager
async def _watch_async(self: StreamConsumerHelper) -> AsyncGenerator[AsyncIterable[ConsumerRecord], None]:
    if self.instance is None:
        raise NotImplemented
    try:
        yield self._watch_async()
    finally:
        await self.instance.close()


@contextmanager
def _watch_sync(self: StreamConsumerHelper) -> Generator[Iterable[ConsumerRecord], None, None]:
    if self.instance is None:
        raise NotImplemented
    try:
        yield self._watch_sync()
    finally:
        self.instance.close()
