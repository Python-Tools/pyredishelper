from .proxy import RedisProxy
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Optional, Generator, AsyncGenerator, AsyncIterable, Iterable
from types import MethodType
from .models import ConsumerRecord


class QueueConsumerHelper(RedisProxy):
    __slots__ = ('instance', "_callbacks", "_instance_check", "_aio", "_cluster", "watch", "_l2r", "_topics")

    def __init__(self, topics: str, *, url: Optional[str] = None, addresses: Optional[str] = None, aio: Optional[bool] = None,
                 l2r: bool = False,
                 **conn_params: Any) -> None:
        """使用List结构构造的queue的消费者代理.

        Args:
            topics (str): 监听的list列表键名,以","分隔
            url (Optional[str], optional): 适用于非集群redis的请求url. Defaults to None.
            addresses (Optional[str], optional): 适用于集群redis的以,分隔的地址序列. Defaults to None.
            aio (Optional[bool], optional): 是否异步接口. Defaults to None.
            l2r (bool, optional): 是否从左侧插入数据右侧读取数据. Defaults to False.
            conn_params (Any): 其他连接选项.
        """
        self._l2r = l2r
        self._topics = topics.split(",")
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
            self.watch = MethodType(_watch_async, self)
        else:
            self.watch = MethodType(_watch_sync, self)

    @property
    def l2r(self) -> bool:
        """描述插入和弹出消息的方向."""
        return self._l2r

    async def _watch_async(self, timeout: int = 3) -> AsyncGenerator[ConsumerRecord, None]:
        if self.l2r:
            while True:
                data = await self.instance.brpop(self._topics, timeout=timeout)  # 右侧取值
                if data is None:
                    continue
                topic, value = data
                record = ConsumerRecord(topic=topic, value=value,)
                yield record
        else:
            while True:
                data = await self.instance.blpop(self._topics, timeout=timeout)  # 左侧取值
                if data is None:
                    continue
                topic, value = data
                record = ConsumerRecord(topic=topic, value=value,)
                yield record

    def _watch_sync(self, timeout: int = 3) -> Generator[ConsumerRecord, None, None]:
        if self.l2r:
            while True:
                data = self.instance.brpop(self._topics, timeout=timeout)  # 右侧取值
                if data is None:
                    continue
                topic, value = data
                record = ConsumerRecord(topic=topic, value=value,)
                yield record
        else:
            while True:
                data = self.instance.blpop(self._topics, timeout=timeout)  # 左侧取值
                if data is None:
                    continue
                topic, value = data
                record = ConsumerRecord(topic=topic, value=value,)
                yield record

    @classmethod
    def from_proxy(clz, proxy: RedisProxy, topics: str, *,
                   l2r: bool = False) -> "QueueConsumerHelper":
        """从RedisProxy实例创建代理.

        Args:
            proxy (RedisProxy): RedisProxy的实例
            topics (str): 待监听的频道名列表,以","分隔
            l2r (bool, optional): 是否从左侧插入数据右侧读取数据. Defaults to False.

        Returns:
            QueueConsumerHelper: 满足protocols.ConsumerProtocol或者protocols.AioConsumerProtocol协议的消费者代理对象
        """
        p = clz(topics, strl2r=l2r)
        if proxy.instance is not None:
            p._aio = proxy.aio
            p._cluster = proxy.cluster
            p.initialize(proxy.instance)
        return p


@asynccontextmanager
async def _watch_async(self: QueueConsumerHelper) -> AsyncGenerator[AsyncIterable[ConsumerRecord], None]:
    if self.instance is None:
        raise NotImplemented
    try:
        yield self._watch_async()
    finally:
        await self.instance.close()


@contextmanager
def _watch_sync(self: QueueConsumerHelper) -> Generator[Iterable[ConsumerRecord], None, None]:
    if self.instance is None:
        raise NotImplemented
    try:
        yield self._watch_sync()
    finally:
        self.instance.close()
