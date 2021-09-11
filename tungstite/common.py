from collections import OrderedDict
from typing      import MutableMapping, Optional, TypeVar

class EmailInfo:
    to:     Optional[str] = None
    # _from because from is a keyword :(
    _from:  Optional[str] = None
    status: Optional[str] = None
    reason: Optional[str] = None

    def __init__(self, ts: int):
        self.ts = ts

    def finalised(self) -> bool:
        return all([self.to, self._from, self.status, self.reason])

TKey   = TypeVar("TKey")
TValue = TypeVar("TValue")

class LimitedOrderedDict(
        OrderedDict,
        MutableMapping[TKey, TValue]
):
    def __init__(self, max: int):
        self._max = max

    def __setitem__(self,
            key:   TKey,
            value: TValue):

        super().__setitem__(key, value)
        super().move_to_end(key, last=False)
        if super().__len__() > self._max:
            super().popitem(last=True)

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
