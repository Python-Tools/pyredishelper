# redisproxy

提供redis客户端的代理对象功能.本项目代理的对象是[redis-py](https://github.com/redis/redis-py)中的四种客户端

+ `redis.Redis`
+ `redis.cluster.RedisCluster`
+ `redis.asyncio.Redis`
+ `redis.asyncio.cluster.RedisCluster`

## 使用

我们可以在运行时通过代理对象的property`aio`和property`cluster`来确认是哪种客户端.

当我们编程时我们应该先确定将使用哪种客户端,然后使用`typing.cast`方法在调用前声明类型.多数时候我们并不需要标明实际的类型,可以只区分同步和异步和具体使用:

+ 数据读写
    + 同步:`r = cast(redis.commands.core.DataAccessCommands,proxy)`
    + 异步:`r = cast(redis.commands.core.AsyncDataAccessCommands,proxy)`
+ pubsub:
    + 同步:`r = cast(redis.commands.core.PubSubCommands,proxy)`
    + 异步:`r = cast(redis.commands.core.AsyncPubSubCommands,proxy)`

这样我们在写程序是也可以有接口提示.只有用到`execute_command`或者`pipeline`时需要指定具体类型.

## 安装

```bash
pip install redisproxy
```
