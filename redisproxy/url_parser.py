from typing import Union, TypedDict, List
from redis.cluster import ClusterNode
from redis.asyncio.cluster import ClusterNode as AioClusterNode


def addresses2clusternode(addresses: str, *, aio: bool = False) -> Union[List[ClusterNode], List[AioClusterNode]]:
    """将节点地址转换成节点对象.

    Args:
        addresses (str): 以','分隔的host:port地址列表
        aio (bool): 是否为异步连接. Defaults to False.

    Returns:
        Union[List[ClusterNode], List[AioClusterNode]]: 同步或异步集群节点列表
    """
    if aio:
        return [AioClusterNode(*pairstr.split(":")) for pairstr in addresses.split(",")]
    else:
        result = []
        for pairstr in addresses.split(","):
            host, portstr = pairstr.split(":")
            node = ClusterNode(host, int(portstr))
            result.append(node)
        return result


class RedisUrlInfo(TypedDict):
    aio: bool
    cluster: bool
    redis_url: str


class RedisUrlError(Exception):
    pass


def redisurl_parser(url: str) -> RedisUrlInfo:
    """校验和规整url.

    url的schema可以为`redis/rediss`,`async`,`cluster`三个对象的组合,但必须包含`redis`或`rediss`

    Args:
        url (str): 原始的url

    Raises:
        RedisUrlError: url的校验错误

    Returns:
        RedisUrlInfo: url中获得的信息
    """
    aio: bool = False
    cluster: bool = False
    redis_url: str
    scheme, url_tail = url.split("://")
    scheme = scheme.lower()
    scheme_eles = scheme.split("+")
    print(scheme_eles)
    for ele in scheme_eles:
        if ele not in ("redis", "rediss", "async", "cluster"):
            raise RedisUrlError("scheme必须只含有redis,rediss,async,cluster")
    if "redis" not in scheme_eles and "rediss" not in scheme_eles:
        raise RedisUrlError("scheme必须含有redis或rediss")
    if "redis" in scheme_eles and "rediss" in scheme_eles:
        raise RedisUrlError("scheme必须只含有redis或rediss中的一个")
    if "async" in scheme_eles:
        aio = True
    if "cluster" in scheme_eles:
        cluster = True
    if "rediss" in scheme_eles:
        redis_url = "rediss://" + url_tail
    else:
        redis_url = "redis://" + url_tail

    return {"aio": aio, "cluster": cluster, "redis_url": redis_url}
