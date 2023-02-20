from .proxy import RedisProxy
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Optional, Generator, AsyncGenerator, Dict, cast
from redis import Redis
from redis.cluster import RedisCluster
from redis.asyncio import Redis as AioRedis
from redis.commands.core import DataAccessCommands, AsyncDataAccessCommands
from types import MethodType


class StreamProducerHelper(RedisProxy):
    __slots__ = ('instance', "_callbacks", "_instance_check", "_aio", "_cluster", "mount", "publish", "_maxlen", "_approximate", "_nomkstream")

    def __init__(self, *, url: Optional[str] = None, addresses: Optional[str] = None, aio: Optional[bool] = None,
                 maxlen: Optional[int] = None, approximate: bool = True, nomkstream: bool = False, ** conn_params: Any) -> None:
        """stream的生产者代理.

        Args:
            url (Optional[str], optional): 适用于非集群redis的请求url. Defaults to None.
            addresses (Optional[str], optional): 适用于集群redis的以,分隔的地址序列. Defaults to None.
            aio (Optional[bool], optional): 是否异步接口. Defaults to None.
            maxlen (Optional[int], optional): 流的最大长度 Defaults to None.
            approximate (bool, optional): 是否有余量的执行最大长度. Defaults to True.
            nomkstream (bool, optional): 流不存在时是否自动创建. Defaults to False.
            conn_params (Any): 其他连接选项.
        """
        self._maxlen = maxlen
        self._approximate = approximate
        self._nomkstream = nomkstream
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
            self.publish = MethodType(_publish_async, self)
            self.mount = MethodType(_mount_async, self)
        else:
            self.publish = MethodType(_publish_sync, self)
            self.mount = MethodType(_mount_sync, self)

    @classmethod
    def from_proxy(clz, proxy: RedisProxy, maxlen: Optional[int] = None, approximate: bool = True, nomkstream: bool = False) -> "StreamProducerHelper":
        """从RedisProxy实例创建代理.

        Args:
            proxy (RedisProxy): RedisProxy的实例
            maxlen (Optional[int], optional): 流的最大长度 Defaults to None.
            approximate (bool, optional): 是否有余量的执行最大长度. Defaults to True.
            nomkstream (bool, optional): 流不存在时是否自动创建. Defaults to False.

        Returns:
            StreamProducerProxy: 满足protocols.StreamProducerProtocol或者protocols.AioStreamProducerProtocol协议的消费者代理对象
        """
        p = clz(maxlen=maxlen, approximate=approximate, nomkstream=nomkstream)
        if proxy.instance is not None:
            p._aio = proxy.aio
            p._cluster = proxy.cluster
            p.initialize(proxy.instance)
        return p


async def _publish_async(self: StreamProducerHelper, topic: str, value: Dict[str, str]) -> None:
    p = cast(AsyncDataAccessCommands, self.instance)
    await p.xadd(topic, value, maxlen=self._maxlen, approximate=self._approximate, nomkstream=self._nomkstream)


def _publish_sync(self: StreamProducerHelper, topic: str, value: Dict[str, str]) -> None:
    p = cast(DataAccessCommands, self.instance)
    p.xadd(topic, value, maxlen=self._maxlen, approximate=self._approximate, nomkstream=self._nomkstream)


@contextmanager
def _mount_sync(self: StreamProducerHelper) -> Generator[StreamProducerHelper, None, None]:
    if self.instance is None:
        raise NotImplemented
    try:
        yield self
    finally:
        self.instance.close()


@asynccontextmanager
async def _mount_async(self: StreamProducerHelper) -> AsyncGenerator[StreamProducerHelper, None]:
    if self.instance is None:
        raise NotImplemented
    try:
        yield self
    finally:
        await self.instance.close()
