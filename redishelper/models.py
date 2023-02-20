from enum import Enum, auto
from dataclasses import dataclass
from typing import Optional, Union, Dict


class AutoOffsetReset(Enum):
    earliest = auto()
    latest = auto()


class Acks(Enum):
    """ack的策略"""
    before = auto()  # 单条消息处理前确认
    after = auto()  # 单条消息处理后确认
    after_batch = auto()  # 一批消息处理后确认


@dataclass
class ConsumerRecord:
    topic: str
    "The topic this record is received from"

    value: Union[bytes, str, Dict[str, str]]
    "The value"

    offset: Optional[str] = None
    "The position id of this record in redis stream."

    timestamp: Optional[int] = None
    "The milliseconds timestamp of this record"
