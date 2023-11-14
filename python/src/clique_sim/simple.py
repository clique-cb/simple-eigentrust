import networkx as nx

from .protocol import Protocol


class Simple(Protocol):
    def __init__(self):
        self._graph = nx.DiGraph()
        self._balances = {}

    def add_user(self, user_id: str):
        self._graph.add_node(user_id)

    def deposit(self, user_id: str, amount: int):
        self._balances[user_id] = self._balances.get(user_id, 0) + amount

    def withdraw(self, user_id: str, amount: int):
        if amount <= self.available_balance(user_id):
            self._balances[user_id] = self._balances.get(user_id, 0) - amount
        else:
            raise ValueError("Insufficient balance")

    def transfer(self, user_id: str, amount: int, recipient_id: str):
        raise NotImplementedError
    
    def set_trust(self, user_id: str, amount: int, recipient_id: str):
        pass