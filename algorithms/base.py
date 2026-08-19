from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Hashable, Iterator, Optional

import networkx as nx

Node = Hashable
Edge = tuple[Node, Node]


class NodeState(str, Enum):
    UNVISITED = "unvisited"
    CURRENT = "current"
    FRONTIER = "frontier"
    VISITED = "visited"
    IN_RESULT = "in_result"
    REJECTED = "rejected"


class EdgeState(str, Enum):
    UNVISITED = "unvisited"
    CONSIDERING = "considering"
    IN_RESULT = "in_result"
    REJECTED = "rejected"
    SATURATED = "saturated"


@dataclass
class AlgorithmStep:
    """One unit of algorithm progress, in a shape visualization.py can render generically."""

    index: int
    description: str
    node_states: dict[Node, NodeState] = field(default_factory=dict)
    edge_states: dict[Edge, EdgeState] = field(default_factory=dict)
    node_labels: dict[Node, Any] = field(default_factory=dict)
    edge_labels: dict[Edge, Any] = field(default_factory=dict)
    is_final: bool = False
    result: Optional[Any] = None


class GraphAlgorithm(ABC):
    """Base contract every algorithm module implements.

    `run` yields one AlgorithmStep at a time so the UI can animate/scrub through
    progress instead of jumping straight to the end result. The last yielded step
    must have is_final=True and carry the algorithm's result.
    """

    def __init__(self, graph: nx.Graph, **params: Any) -> None:
        self.graph = graph
        self.params = params

    @abstractmethod
    def run(self) -> Iterator[AlgorithmStep]:
        raise NotImplementedError
