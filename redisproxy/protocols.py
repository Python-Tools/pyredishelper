"""kafka代理的协议模块."""
from typing import Dict, Union, Protocol, ContextManager, Iterable, AsyncContextManager, AsyncIterable
from .models import ConsumerRecord


class ProducerProtocol(Protocol):
    """同步生产者协议"""

    def publish(self, topic: str, value: Union[str, bytes]) -> None:
        """同步发布接口.

        Args:
            topic (str): 发布去的主题
            value (Union[str, bytes, ]): 发布的值,
        """

    def mount(self) -> ContextManager["ProducerProtocol"]:
        """同步挂载接口.

        提供一个管理回收连接资源的上下文管理器.

        Example:
            p = cast(ProducerProtocol, kafkap)
            with p.mount() as cli:
                cli.publish("topic1", f"send {i}")
                print("send ok")

        Yields:
            ProducerProtocol: 返回一个同步发布协议对象
        """


class AioProducerProtocol(Protocol):
    """异步生产者协议"""
    async def publish(self, topic: str, value: Union[str, bytes]) -> None:
        """异步发布接口.

        Args:
            topic (str): 发布去的主题
            value (Union[str, bytes]): 发布的值
        """

    def mount(self) -> AsyncContextManager["AioProducerProtocol"]:
        """同步挂载接口.

        提供一个管理回收连接资源的上下文管理器.

        Example:
            p = cast(AioProducerProtocol, kafkap)
            async with p.mount() as cli:
                await cli.publish("topic1", f"send {i}")
                print("send ok")

        Yields:
            AioProducerProtocol: 返回一个异步发布协议对象
        """


class StreamProducerProtocol(Protocol):
    """同步流对象的生产者协议"""

    def publish(self, topic: str, value: Dict[str, str]) -> None:
        """同步发布接口.

        Args:
            topic (str): 发布去的主题
            value (Dict[str, str]): 发布的值
        """

    def mount(self) -> ContextManager["StreamProducerProtocol"]:
        """同步挂载接口.

        提供一个管理回收连接资源的上下文管理器.

        Example:
            p = cast(ProducerProtocol, kafkap)
            with p.mount() as cli:
                cli.publish("topic1", {"key": "a key", "value": f"{i}y"})
                print("send ok")

        Yields:
            ProducerProtocol: 返回一个同步发布协议对象
        """


class AioStreamProducerProtocol(Protocol):
    """异步流对象的生产者协议"""
    async def publish(self, topic: str, value: Dict[str, str]) -> None:
        """异步发布接口.

        Args:
            topic (str): 发布去的主题
            value (Dict[str, str]): 发布的值
        """

    def mount(self) -> AsyncContextManager["AioStreamProducerProtocol"]:
        """同步挂载接口.

        提供一个管理回收连接资源的上下文管理器.

        Example:
            p = cast(AioProducerProtocol, kafkap)
            async with p.mount() as cli:
                await cli.publish("topic1", {"key": "a key", "value": f"{i}y"})
                print("send ok")

        Yields:
            AioProducerProtocol: 返回一个异步发布协议对象
        """


class ConsumerProtocol(Protocol):
    """同步消费者的协议."""

    def watch(self) -> ContextManager[Iterable[ConsumerRecord]]:
        """同步监听接口.

        调用后获得一个管理启动关闭连接并且返回一个可迭代对象的上下文管理器.监听获取消息可以直接使用`for`实现.

        Example:
            c = cast(ConsumerProtocol, kafkac)
            with c.watch() as g:
                for record in g:
                    print(record.value)

        Yields:
            Iterable[ConsumerRecord]: 返回一个消息的可迭代对象
        """


class AioConsumerProtocol(Protocol):
    """异步消费者的协议."""

    def watch(self) -> AsyncContextManager[AsyncIterable[ConsumerRecord]]:
        """异步监听接口.

        调用后获得一个管理启动关闭连接并且返回一个异步可迭代对象的上下文管理器.监听获取消息可以直接使用`async for`实现.

        Example:
            c = cast(AioConsumerProtocol, kafkac)
            async with c.watch() as g:
                async for record in g:
                    print(record.value)

        Yields:
            AsyncIterable[ConsumerRecord]: 返回一个消息的异步可迭代对象
        """
