from collections import defaultdict

import networkx as nx

from .protocol import Protocol
from .utils import split_proportionally


class VerySimple(Protocol):
    """
    The simplest protocol. The debt _cannot_ be re-credited. It's like Union protocol.
    """
    def __init__(self):
        self._graph = nx.DiGraph()
        self._balances = defaultdict(int)
        self._self_locks = defaultdict(int)

    def _edge_trust(self, user_id: str, recipient_id: str) -> int:
        return self._graph[user_id][recipient_id]["capacity"]

    def _locked_edge_trust(self, user_id: str, recipient_id: str) -> int:
        return self._graph[user_id][recipient_id]["locked"]
    
    def _remaining_edge_trust(self, user_id: str, recipient_id: str) -> int:
        return self._edge_trust(user_id, recipient_id) - self._locked_edge_trust(user_id, recipient_id)

    def add_user(self, user_id: str):
        self._graph.add_node(user_id)

    def deposit(self, user_id: str, amount: int):
        self._balances[user_id] = self._balances[user_id] + amount

    def withdraw(self, user_id: str, amount: int):
        if amount <= self.available_balance(user_id):
            self._balances[user_id] = self._balances[user_id] - amount
        else:
            raise ValueError("Insufficient balance")
 
    def available_balance(self, user_id: str) -> int:
        return self._balances[user_id] - self.locked_balance(user_id)
    
    def locked_balance(self, user_id: str) -> int:
        return sum([
            self._locked_edge_trust(user_id, recipient_id)
            for recipient_id in self._graph.neighbors(user_id)
        ]) + self._self_locks[user_id]
    
    def transfer(self, user_id: str, amount: int, recipient_id: str):
        raise NotImplementedError
    
    def set_trust(self, user_id: str, amount: int, recipient_id: str):
        if self._graph.has_edge(user_id, recipient_id):
            edge_data = self._graph[user_id][recipient_id]
            if amount < edge_data["locked"]:
                raise ValueError("Cannot drop the locked trust")

            self._graph[user_id][recipient_id]["capacity"] = amount
        else:
            self._graph.add_edge(user_id, recipient_id, capacity=amount, locked=0)

    def credit_limit(self, user_id: str) -> int:
        own_money = self.available_balance(user_id)

        # Everything that can flow from friends and not yet locked.
        return own_money + sum([
            min(self._remaining_edge_trust(v, user_id), self.available_balance(v))
            for v in self._graph.predecessors(user_id)
        ])
    
    def _lock_trust(self, recipient_id: str, voucher_id: str, amount: int):
        remaining = self._remaining_edge_trust(voucher_id, recipient_id)
        if amount > remaining:
            raise ValueError("Insufficient trust")
        
        self._graph[voucher_id][recipient_id]["locked"] = self._graph[voucher_id][recipient_id]["locked"] + amount

    def borrow(self, user_id: str, amount: int):
        if amount > self.credit_limit(user_id):
            raise ValueError("Insufficient credit limit")

        # First, lock your own money
        self_locked = min(self.available_balance(user_id), amount)
        self._self_locks[user_id] = self._self_locks[user_id] + self_locked
        amount = amount - self_locked

        if amount > 0:
            # Then, lock money from friends, proportionally
            neighbors_limits = [
                (v, min(self._remaining_edge_trust(v, user_id), self.available_balance(v)))
                for v in self._graph.predecessors(user_id)
            ]
            
            split = split_proportionally(amount, [limit for _, limit in neighbors_limits])
            for (v, _), x in zip(neighbors_limits, split):
                self._lock_trust(user_id, v, x)

            amount -= sum(split)
        
        if amount > 0:
            raise ValueError("Wow what happened?")



