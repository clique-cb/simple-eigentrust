# Define the Trust Strategy Interface
from abc import ABC, abstractmethod
from typing import Dict

import networkx as nx


class TrustStrategy(ABC):
    @abstractmethod
    def generate_trust_deltas(self, user_id: str, graph: nx.DiGraph) -> Dict[str, int]:
        """
        Generate trust adjustments for a given user based on the graph.
        """
        pass


class ExampleTrustStrategy(TrustStrategy):
    def generate_trust_deltas(self, user_id: str, graph: nx.DiGraph) -> Dict[str, int]:
        # Simple logic to increase trust by a constant factor for demonstration
        return {v: 10 for v in graph.successors(user_id) if v != user_id}
