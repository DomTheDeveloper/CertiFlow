from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable
from ..model import Fact, IRNode

class Adapter(ABC):
    @abstractmethod
    def nodes(self) -> Iterable[IRNode]: raise NotImplementedError
    def seed_facts(self) -> Iterable[Fact]: return ()
