from .proxy import RedisProxy
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Optional, Generator, AsyncGenerator
from redis import Redis
from redis.cluster import RedisCluster
from redis.asyncio import Redis as AioRedis
from types import MethodType


class ChannelProducerHelper(RedisProxy):
    __slots__ = ('instance', "_callbacks", "_instance_check", "_aio", "_cluster", "mount")

    def __init__(self, *, url: Optional[str] = None, addresses: Optional[str] = None, aio: Optional[bool] = None, **conn_params: Any) -> None:
        """pubsub模式频道生产者者代理.

        Args:
            url (Optional[str], optional): 适用于非集群redis的请求url. Defaults to None.
            addresses (Optional[str], optional): 适用于集群redis的以,分隔的地址序列. Defaults to None.
            aio (Optional[bool], optional): 是否异步接口. Defaults to None.
            conn_params (Any): 其他连接选项.
        """
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
            self.mount = MethodType(_mount_async, self)
        else:
            self.mount = MethodType(_mount_sync, self)

    @classmethod
    def from_proxy(clz, proxy: RedisProxy) -> "ChannelProducerHelper":
        """从RedisProxy实例创建代理.

        Args:
            proxy (RedisProxy): RedisProxy的实例

        Returns:
            ChannelProducerHelper:  满足protocols.ProducerProtocol或者protocols.AioProducerProtocol协议的消费者代理对象
        """
        p = clz()
        if proxy.instance is not None:
            p._aio = proxy.aio
            p._cluster = proxy.cluster
            p.initialize(proxy.instance)
        return p


@contextmanager
def _mount_sync(self: ChannelProducerHelper) -> Generator[ChannelProducerHelper, None, None]:
    if self.instance is None:
        raise NotImplemented
    try:
        yield self
    finally:
        self.instance.close()


@asynccontextmanager
async def _mount_async(self: ChannelProducerHelper) -> AsyncGenerator[ChannelProducerHelper, None]:
    if self.instance is None:
        raise NotImplemented
    try:
        yield self
    finally:
        await self.instance.close()
