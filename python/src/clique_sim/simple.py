from typing import Dict
from collections import defaultdict

import networkx as nx

from .protocol import Protocol
from .utils import split_proportionally


class VerySimple(Protocol):
    """
    The simplest protocol. Debt only happens between direct neighbors. However, it can be
    re-credited further (a user with a locked balance can borrow further and withdraw)
    """

    def __init__(self):
        self._graph = nx.DiGraph()
        self._balances = defaultdict(int)
        # self._self_locks = defaultdict(int)

    # Attributes

    def _capacity(self, user_id: str, recipient_id: str) -> int:
        return self._graph[user_id][recipient_id]["capacity"] if self._graph.has_edge(user_id, recipient_id) else 0

    def _flow(self, user_id: str, recipient_id: str) -> int:
        return self._graph[user_id][recipient_id]["flow"] if self._graph.has_edge(user_id, recipient_id) else 0
    
    edge_debt = _flow

    def remaining_capacity(self, user_id: str, recipient_id: str) -> int:
        return self._capacity(user_id, recipient_id) - self._flow(user_id, recipient_id)

    def trusted(self, user_id: str) -> Dict[str, int]:
        return {v: self._capacity(user_id, v) for v in self._graph.successors(user_id)}

    def locked(self, user_id: str) -> Dict[str, int]:
        return {v: self._flow(v, user_id) for v in self._graph.successors(user_id)}

    def debt(self, user_id: str) -> Dict[str, int]:
        return {v: self._flow(v, user_id) for v in self._graph.predecessors(user_id)}

    def available_balance(self, user_id: str) -> int:
        return self._balances[user_id] - self.locked_balance(user_id) + self.debt(user_id)

    def edge_credit_limit(self, creditor_id: str, debtor_id: str) -> int:
        return min(self.remaining_capacity(creditor_id, debtor_id), self.available_balance(creditor_id))

    def credit_limit(self, user_id: str):
        return sum(self.edge_credit_limit(v, user_id) for v in self._graph.predecessors(user_id))
    
    # Methods

    def register(self, user_id: str):
        self._graph.add_node(user_id)

    def deposit(self, user_id: str, amount: int):
        self._balances[user_id] = self._balances[user_id] + amount

    def withdraw(self, user_id: str, amount: int):
        if amount <= self.available_balance(user_id):
            self._balances[user_id] = self._balances[user_id] - amount
        else:
            raise ValueError("Insufficient balance")

    def transfer(self, user_id: str, amount: int, recipient_id: str):
        self.withdraw(user_id, amount)
        self.deposit(recipient_id, amount)

    def set_trust(self, user_id: str, trust_deltas: Dict[str, int]):
        for recipient_id, amount in trust_deltas.items():
            if self.remaining_capacity(user_id, recipient_id) + amount < 0:
                raise ValueError(f"Cannot decrease the trust from {user_id} to {recipient_id} by {amount}")

        for recipient_id, amount in trust_deltas.items():
            if not self._graph.has_edge(user_id, recipient_id):
                self._graph.add_edge(user_id, recipient_id, capacity=amount, flow=0)
            else:
                self._graph[user_id][recipient_id]["capacity"] += amount
    
    def borrow_or_repay(self, user_id: str, flow_deltas: Dict[str, int]):
        for creditor_id, amount in flow_deltas.items():
            new_flow = self._flow(creditor_id, user_id) + amount
            if new_flow < 0:
                raise ValueError(f"{user_id} cannot repay {-amount} to {creditor_id}: not enough debt")
            if new_flow > self._capacity(creditor_id, user_id):
                raise ValueError(f"{user_id} cannot borrow {amount} from {creditor_id}: not enough capacity")
        
        for creditor_id, amount in flow_deltas.items():
            if amount > 0:
                self._graph[creditor_id][user_id]["flow"] += amount

    borrow = borrow_or_repay

    def repay(self, user_id: str, flow_deltas: Dict[str, int]):
        self.borrow_or_repay(user_id, {k: -v for k, v in flow_deltas.items()})

    def total_value_locked(self) -> int:
        return sum(self._balances.values())
    
    def total_debt(self) -> int:
        return sum(self.debt(v) for v in self._graph.nodes)