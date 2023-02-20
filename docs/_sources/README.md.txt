# pyredishelper

提供redis客户端的代理对象功能.本项目代理的对象是[redis-py](https://github.com/redis/redis-py)中的四种客户端

+ `redis.Redis`
+ `redis.cluster.RedisCluster`
+ `redis.asyncio.Redis`
+ `redis.asyncio.cluster.RedisCluster`

## 特性

+ 提供了统一的代理对象`RedisProxy`用于代理`redis.Redis`,`redis.cluster.RedisCluster`,`redis.asyncio.Redis`或`redis.asyncio.cluster.RedisCluster`
+ 针对生产者消费者模式提供了专用代理对象`ChannelConsumerHelper`,`ChannelProducerHelper`,`QueueConsumerHelper`,`QueueProducerHelper`,`StreamConsumerPHelper`,`StreamProducerHelper`
+ 生产者消费者提供了进一步的封装,可以通过上下文管理连接

## 使用

### RedisProxy的使用

我们可以使用`RedisProxy`延后初始化要代理的对象,从而避免客户端对象在各个函数之间传来传去.

```python

rediscli = RedisProxy()

...

rediscli.initialize_from_url("redis://localhost:6379/0?decode_responses=true")
```

我们可以在运行时通过代理对象的property`aio`和property`cluster`来确认是哪种客户端.

当我们编程时我们应该先确定将使用哪种客户端,然后使用`typing.cast`方法在调用前声明类型.多数时候我们并不需要标明实际的类型,可以只区分同步和异步和具体使用:

> 同步:

```python
r = cast(redis.commands.core.DataAccessCommands,rediscli)
r.get("x")
```

> 异步:

```python
r = cast(redis.commands.core.AsyncDataAccessCommands,rediscli)
await r.get(x)
```

这样我们在写程序是也可以有接口提示.只有用到`pubsub`,`execute_command`或者`pipeline`的少数场景时需要指定具体类型.

### 生产者消费者模式

生产者消费者模式提供了基本统一的接口设计

+ `ConsumerProtocol` 通用的同步消费者接口
+ `ProducerProtocol` 除了stream外通用的同步生产者接口
+ `AioConsumerProtocol` 通用的异步消费者接口
+ `AioProducerProtocol` 除了stream外通用的异步生产者接口
+ `StreamProducerProtocol`stream的同步生产者接口
+ `AioStreamProducerProtocol` stream的异步生产者接口

当我们编程时我们应该先确定将使用哪种客户端,然后使用`typing.cast`方法在调用前声明对应代理的接口类型.

> 同步生产者

```python
qp = cast(StreamProducerProtocol, StreamProducerHelper.from_proxy(rediscli, maxlen=20))
with qp.mount() as producer:
    for i in range(10):
        producer.publish(topic,value)
```

> 异步生产者

```python
qp = cast(AioStreamProducerProtocol, StreamProducerHelper.from_proxy(rediscli, maxlen=20))
async with qp.mount() as producer:
    for i in range(10):
        await producer.publish(topic,value)
```

> 同步消费者

```python
qc = cast(ConsumerProtocol, QueueConsumerHelper.from_proxy(rediscli, topics))

with qc.watch() as records:
    for record in records:
        print(f"get msg {record.value} from topic {record.topic}")
```

> 异步消费者

```python
qc = cast(AioConsumerProtocol, QueueConsumerHelper.from_proxy(rediscli, topics))

async with qc.watch() as records:
    async for record in records:
        print(f"get msg {record.value} from topic {record.topic}")
```

## 安装

```bash
pip install pyredishelper
```
