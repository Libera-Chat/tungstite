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
