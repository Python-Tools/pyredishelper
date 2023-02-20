from .proxy import RedisProxy
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Optional, Union, Generator, AsyncGenerator
from types import MethodType


class QueueProducerHelper(RedisProxy):
    __slots__ = ('instance', "_callbacks", "_instance_check", "_aio", "_cluster", "publish", "mount", "_l2r")

    def __init__(self, *, url: Optional[str] = None, addresses: Optional[str] = None, aio: Optional[bool] = None,
                 l2r: bool = False,
                 **conn_params: Any) -> None:
        """使用List结构构造的queue的生产者代理.

        Args:
            url (Optional[str], optional): 适用于非集群redis的请求url. Defaults to None.
            addresses (Optional[str], optional): 适用于集群redis的以,分隔的地址序列. Defaults to None.
            aio (Optional[bool], optional): 是否异步接口. Defaults to None.
            l2r (bool, optional): 是否从左侧插入数据右侧读取数据. Defaults to False.
            conn_params (Any): 其他连接选项.
        """
        self._l2r = l2r
        super().__init__()
        self.attach_callback(self.regist_methods)
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

    @property
    def l2r(self) -> bool:
        """描述插入和弹出消息的方向."""
        return self._l2r

    @classmethod
    def from_proxy(clz, proxy: RedisProxy, *,
                   l2r: bool = False) -> "QueueProducerHelper":
        """从RedisProxy实例创建代理.

        Args:
            proxy (RedisProxy): RedisProxy的实例
            l2r (bool, optional): 是否从左侧插入数据右侧读取数据. Defaults to False.

        Returns:
            QueueProducerHelper: 满足protocols.ProducerProtocol或者protocols.AioProducerProtocol协议的消费者代理对象
        """
        p = clz(l2r=l2r)
        if proxy.instance is not None:
            p._aio = proxy.aio
            p._cluster = proxy.cluster
            p.initialize(proxy.instance)
        return p


async def _publish_async(self: QueueProducerHelper, topic: str, value: Union[str, bytes]) -> None:
    if self._l2r:
        await self.instance.lpush(topic, value)
    else:
        await self.instance.rpush(topic, value)


def _publish_sync(self: QueueProducerHelper, topic: str, value: Union[str, bytes]) -> None:
    if self._l2r:
        self.instance.lpush(topic, value)
    else:
        self.instance.rpush(topic, value)


@contextmanager
def _mount_sync(self: QueueProducerHelper) -> Generator[QueueProducerHelper, None, None]:
    if self.instance is None:
        raise NotImplemented
    try:
        yield self
    finally:
        self.instance.close()


@asynccontextmanager
async def _mount_async(self: QueueProducerHelper) -> AsyncGenerator[QueueProducerHelper, None]:
    if self.instance is None:
        raise NotImplemented
    try:
        yield self
    finally:
        await self.instance.close()
