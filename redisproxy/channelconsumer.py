from .proxy import RedisProxy
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Optional, Generator, AsyncGenerator, AsyncIterable, Iterable
from types import MethodType
from redis import Redis
from redis.client import PubSub
from redis.cluster import RedisCluster
from redis.asyncio import Redis as AioRedis
from redis.asyncio.client import PubSub as AioPubSub
from .models import ConsumerRecord


class ChannelConsumerProxy(RedisProxy):
    __slots__ = ('instance', "_callbacks", "_instance_check", "_aio", "_cluster", "watch", "_topics")

    def __init__(self, topics: str, *, url: Optional[str] = None, addresses: Optional[str] = None, aio: Optional[bool] = None,
                 **conn_params: Any) -> None:
        """pubsub模式频道消费者代理.

        Args:
            topics (str): 待监听的频道名列表,以","分隔
            url (Optional[str], optional): 适用于非集群redis的请求url. Defaults to None.
            addresses (Optional[str], optional): 适用于集群redis的以,分隔的地址序列. Defaults to None.
            aio (Optional[bool], optional): 是否异步接口. Defaults to None.
            conn_params (Any): 其他连接选项.
        """
        self._topics = topics
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

    async def _watch_async(self, channel: AioPubSub, timeout: Optional[int] = None) -> AsyncGenerator[ConsumerRecord, None]:
        while True:
            if timeout is None:
                message = await channel.get_message(ignore_subscribe_messages=True)
            else:
                message = await channel.get_message(ignore_subscribe_messages=True, timeout=timeout)
            if message is None:
                continue
            topic = message.get("channel", "")
            value = message.get("data", "")
            record = ConsumerRecord(topic=topic, value=value)
            yield record

    def _watch_sync(self, channel: PubSub, timeout: int = 3) -> Generator[ConsumerRecord, None, None]:
        while True:
            if timeout is None:
                message = channel.get_message(ignore_subscribe_messages=True)
            else:
                message = channel.get_message(ignore_subscribe_messages=True, timeout=timeout)
            if message is None:
                continue
            topic = message.get("channel", "")
            value = message.get("data", "")
            record = ConsumerRecord(topic=topic, value=value)
            yield record

    @classmethod
    def from_proxy(clz, proxy: RedisProxy, topics: str) -> "ChannelConsumerProxy":
        """从RedisProxy实例创建代理.

        Args:
            proxy (RedisProxy): RedisProxy的实例
            topics (str): 待监听的频道名列表,以","分隔

        Returns:
            ChannelConsumerProxy: 满足protocols.ConsumerProtocol或者protocols.AioConsumerProtocol协议的消费者代理对象
        """
        p = clz(topics)
        if proxy.instance is not None:
            p._aio = proxy.aio
            p._cluster = proxy.cluster
            p.initialize(proxy.instance)
        return p


@asynccontextmanager
async def _watch_async(self: ChannelConsumerProxy) -> AsyncGenerator[AsyncIterable[ConsumerRecord], None]:
    if self.instance is None:
        raise NotImplemented
    try:
        async with self.instance.pubsub() as pubsub:
            if "*" in self._topics or "?" in self._topics or "!" in self._topics:
                await pubsub.psubscribe(self._topics)
            else:
                await pubsub.subscribe(*self._topics.split(","))
            yield self._watch_async(pubsub)
    finally:
        await self.instance.close()


@contextmanager
def _watch_sync(self: ChannelConsumerProxy) -> Generator[Iterable[ConsumerRecord], None, None]:
    if self.instance is None:
        raise NotImplemented
    try:
        with self.instance.pubsub() as pubsub:
            if "*" in self._topics or "?" in self._topics or "!" in self._topics:
                pubsub.psubscribe(self._topics)
            else:
                pubsub.subscribe(*self._topics.split(","))
            yield self._watch_sync(pubsub)
    finally:
        self.instance.close()
