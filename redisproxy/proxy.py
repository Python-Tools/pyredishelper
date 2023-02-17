"""基础的redis代理对象."""
from pyproxypattern import Proxy
from typing import Optional, Union, List, Any, cast
from redis import Redis
from redis.cluster import RedisCluster
from redis.asyncio import Redis as AioRedis
from redis.asyncio.cluster import RedisCluster as AioRedisCluster
from redis.cluster import ClusterNode
from redis.asyncio.cluster import ClusterNode as AioClusterNode
from .url_parser import addresses2clusternode, redisurl_parser


class RedisProxy(Proxy):
    """redis的代理类."""
    __slots__ = ('instance', "_callbacks", "_instance_check", "_aio", "_cluster")

    def __init__(self, *, url: Optional[str] = None, addresses: Optional[str] = None, aio: Optional[bool] = None, **conn_params: Any) -> None:
        """redis-py的代理对象.

        Args:
            url (Optional[str], optional): 适用于非集群redis的请求url. Defaults to None.
            addresses (Optional[str], optional): 适用于集群redis的以,分隔的地址序列. Defaults to None.
            aio (Optional[bool], optional): 是否异步接口. Defaults to None.
            conn_params (Any): 其他连接选项.
        """
        self._aio: Optional[bool] = None
        self._cluster: Optional[bool] = None
        if url:
            info = redisurl_parser(url)
            if aio is not None:
                _aio = aio
            else:
                _aio = info["aio"]
            instance = self.new_instance_from_url(info["redis_url"], aio=_aio, cluster=info["cluster"], **conn_params)
            super().__init__(instance)
        elif addresses:
            if aio is None:
                _aio = False
            else:
                _aio = aio
            instance = self.new_instance_from_address(addresses, aio=_aio, **conn_params)
            super().__init__(instance)
        else:
            super().__init__()

    @property
    def aio(self) -> bool:
        if self.instance is None:
            raise NotImplemented
        if self._aio is not None:
            return self._aio
        else:
            aio = isinstance(self.instance, (AioRedisCluster, AioRedis))
            self._aio = aio
            return aio

    @property
    def cluster(self) -> bool:
        if self.instance is None:
            raise NotImplemented
        if self._cluster is not None:
            return self._cluster
        else:
            cluster = isinstance(self.instance, (AioRedisCluster, RedisCluster))
            self._cluster = cluster
            return cluster

    def new_instance_from_addresses(self, addresses: str, *, aio: bool = False, **conn_params: Any) -> Union[RedisCluster, AioRedisCluster]:
        self._cluster = True
        if aio:
            self._aio = True
            startup_nodes = addresses2clusternode(addresses, aio=aio)
            startup_nodes = cast(List[AioClusterNode], startup_nodes)
            return AioRedisCluster(startup_nodes=startup_nodes, **conn_params)
        else:
            self._aio = False
            startup_nodes = addresses2clusternode(addresses, aio=aio)
            startup_nodes = cast(List[ClusterNode], startup_nodes)
            return RedisCluster(startup_nodes=startup_nodes, **conn_params)

    def initialize_from_addresses(self, addresses: str, *, aio: bool = False, **conn_params: Any) -> None:
        """使用集群起始节点地址初始化redis连接实例

        Args:
            addresses (str): 以','分隔的host:port地址列表
            aio (bool, optional): 是否构造异步客户端. Defaults to False.
            conn_params (Any): 其他连接选项.
        """
        instance = self.new_instance_from_addresses(addresses, aio=aio, **conn_params)
        self.initialize(instance)

    def new_instance_from_url(self, url: str, *, aio: bool = False, cluster: bool = False, **conn_params: Any) -> Union[Redis, AioRedis, RedisCluster, AioRedisCluster]:
        if aio:
            self._aio = True
            if cluster:
                self._cluster = True
                return AioRedisCluster.from_url(url, **conn_params)
            else:
                self._cluster = False
                return AioRedis.from_url(url, **conn_params)
        else:
            self._aio = False
            if cluster:
                self._cluster = True
                return RedisCluster.from_url(url, **conn_params)
            else:
                self._cluster = False
                return Redis.from_url(url, **conn_params)

    def initialize_from_url(self, url: str, **conn_params: Any) -> None:
        """使用url初始化代理对象

        Args:
            url (str): 适用于非集群redis的请求url.
            conn_params (Any): 其他连接选项.
        """
        info = redisurl_parser(url)
        instance = self.new_instance_from_url(info["redis_url"], aio=info["aio"], cluster=info["cluster"], **conn_params)
        self.initialize(instance)
