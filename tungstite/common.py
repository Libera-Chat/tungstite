from collections import deque, OrderedDict
from typing      import OrderedDict as TOrderedDict
from typing      import Deque, Generic, Iterator, List, Optional, TypeVar

class EmailInfo:
    to:     Optional[str] = None
    # _from because from is a keyword :(
    _from:  Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None

    def __init__(self, id: str, ts: int):
        self.id = id
        self.ts = ts

    def finalised(self) -> bool:
        return all([self.to, self._from, self.status, self.reason])

TKey   = TypeVar("TKey")
TValue = TypeVar("TValue")

class LimitedOrderedDict(Generic[TKey, TValue]):
    def __init__(self, max: int):
        self._max = max
        self._dict: TOrderedDict[TKey, TValue] = OrderedDict()

    def __contains__(self, key: TKey) -> bool:
        return key in self._dict

    def __getitem__(self, key: TKey) -> TValue:
        return self._dict[key]

    def __setitem__(self,
            key:   TKey,
            value: TValue):

        self._dict[key] = value
        self._dict.move_to_end(key, last=False)
        if len(self._dict) > self._max:
            self._dict.popitem(last=True)

    def __delitem__(self, key: TKey):
        del self._dict[key]

class LimitedList(Generic[TKey]):
    def __init__(self, max: int):
        self._max = max
        self._items: Deque[TKey] = deque()

    def __iter__(self) -> Iterator[TKey]:
        return self._items.__iter__()

    def add(self, item: TKey):
        self._items.appendleft(item)
        if len(self._items) > self._max:
            self._items.pop()

SECONDS_MINUTES = 60
SECONDS_HOURS   = SECONDS_MINUTES*60
SECONDS_DAYS    = SECONDS_HOURS*24
SECONDS_WEEKS   = SECONDS_DAYS*7

def human_duration(total: int, max_units: int=2) -> str:
    counts: List[int] = []
    counts[0:2] = divmod(total,      SECONDS_WEEKS)
    counts[1:3] = divmod(counts[-1], SECONDS_DAYS)
    counts[2:4] = divmod(counts[-1], SECONDS_HOURS)
    counts[3:5] = divmod(counts[-1], SECONDS_MINUTES)

    outs: List[str] = []
    for unit, i in zip("wdhms", counts):
        if i > 0 and len(outs) < max_units:
            outs.append(f"{i}{unit}")

    return "".join(outs)
