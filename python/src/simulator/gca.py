from abc import ABC, abstractmethod
from typing import TypeVar, Generic, NamedTuple, List

import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from pydantic import BaseModel

from cadCAD.configuration import Configuration, Experiment
from cadCAD.configuration.utils import config_sim
from cadCAD.engine import ExecutionMode, ExecutionContext, Executor


class NodeState(BaseModel):
    pass


class EdgeState(BaseModel):
    pass


NS = TypeVar("NS", bound=NodeState)
ES = TypeVar("ES", bound=EdgeState)


class GraphCellularAutomata(ABC, Generic[NS, ES]):
    """
    GraphCellularAutomata is a class that defines a graph-based cellular automata simulation.
    One should define:
     - Data structure for the node state
     - Data structure for the edge state
     - Transition rule for the node and edges state update, which takes the neighbourhood of node as input
    """

    class AdjacentState(NamedTuple):
        node_index: int
        node_state: NS
        in_edge: ES
        out_edge: ES

    def __init__(self, graph: nx.DiGraph, **kwargs):
        self.graph = graph
        self.initialize_graph(**kwargs)

    @abstractmethod
    def initialize_graph(self, **kwargs):
        """
        Initialize the graph with the initial state. For example:
        - set the available balances for each node accordingly to a given initial funds distribution
        - set all credit limits to zero
        """
        pass

    @classmethod
    @abstractmethod
    def transition_func(
        cls, node: NS, neighbours: list[AdjacentState]
    ) -> tuple[NS, dict[int, ES]]:
        """
        Transition rule for the node state update.
        """
        pass

    @classmethod
    @abstractmethod
    def node_action_policy(cls, node: NS) -> NS:
        """
        Node action policy: how a node can change its own state "at will". For example,
        deposit or withdraw funds.
        """
        pass

    def run_simulation(self, n_steps: int):
        """
        Run the simulation for n_steps.
        """
        initial_state = {"graph": self.graph}
        sim_params = {
            "N": 1,  # Number of Monte Carlo runs
            "T": range(n_steps),  # Number of time steps
            # "M": {},  # Model parameters, empty in this case since no sweeping is used
        }

        def _policies_apply(params, substep, state_history, previous_state):
            graph = previous_state["graph"]
            result = {}
            for node in graph.nodes:
                result[node] = self.node_action_policy(graph.nodes[node]["state"])
            return result

        def _states_apply(params, substep, state_history, previous_state, policy_input):
            graph = previous_state["graph"]
            for node in policy_input:
                graph.nodes[node]["state"] = policy_input[node]

            # save state updates to be applied at the end (avoid interference at each time step)
            next_node_states = {}
            next_edge_states = {}

            def dfs_collect_nodes_optimized(start_node, graph, memo):
                if start_node in memo:
                    return memo[start_node]

                visited = set()
                stack = [(start_node, 0)]  # Stack stores tuples of (node, depth)
                reachable_nodes = []

                while stack:
                    node, depth = stack.pop()
                    if node not in visited:
                        visited.add(node)
                        reachable_nodes.append((node, depth))
                        stack.extend(
                            (n, depth + 1)
                            for n in graph.neighbors(node)
                            if n not in visited
                        )

                # Sort the reachable_nodes list by depth
                reachable_nodes.sort(key=lambda x: x[1])

                # Extract only the nodes from the sorted list
                sorted_nodes = [node for node, depth in reachable_nodes]

                # Memoize the result
                memo[start_node] = sorted_nodes
                return sorted_nodes

            # Initialize the memoization dictionary
            memo = {}

            # Compute the connected nodes using optimized DFS with memoization
            connected_nodes = {
                node: dfs_collect_nodes_optimized(node, graph, memo)
                for node in graph.nodes
            }

            for node in graph.nodes:
                neighbours = [
                    self.AdjacentState(
                        node_index=n,
                        node_state=graph.nodes[n]["state"],
                        in_edge=graph.edges[n, node]["state"],
                        out_edge=graph.edges[node, n]["state"],
                    )
                    for n in graph.neighbors(node)
                ]
                new_node_state, new_edge_states = self.transition_func(
                    graph.nodes[node]["state"], neighbours
                )

                next_node_states[node] = new_node_state

                # TODO: check where is the edge depth
                for other in graph.neighbors(node):
                    next_edge_states[(node, other)] = new_edge_states[other]

            for connected_node in connected_nodes:
                for node in connected_nodes[connected_node]:
                    if node == connected_node:
                        continue
                    next_node_states[connected_node].credit_limit.append(
                        next_node_states[node].credit_limit[0]
                    )

            for node in next_node_states:
                graph.nodes[node]["state"] = next_node_states[node]

            for edge in next_edge_states:
                graph.edges[edge]["state"] = next_edge_states[edge]

            return "graph", graph

        partial_state_update_block = [
            {
                "policies": {"user_actions": _policies_apply},
                "variables": {"graph": _states_apply},
            }
        ]

        # Configuring and running the simulation
        experiment = Experiment()
        experiment.append_configs(
            initial_state=initial_state,
            partial_state_update_blocks=partial_state_update_block,
            sim_configs=config_sim(sim_params),  # Ensure this is a dictionary
        )

        exec_mode = ExecutionMode()
        exec_context = ExecutionContext(exec_mode.single_proc)
        executor = Executor(exec_context, experiment.configs)
        records = executor.execute()

        return records


class BasicNodeState(NodeState):
    balance: int
    credit_limit: List[int]


class BasicEdgeState(EdgeState):
    capacity: int
    flow: int


class Maxflow2GCA(GraphCellularAutomata[BasicNodeState, BasicEdgeState]):

    def initialize_graph(self, balance_distribution: dict[int, int], **kwargs):
        for node in self.graph.nodes:
            self.graph.nodes[node]["state"] = BasicNodeState(
                balance=balance_distribution[node], credit_limit=[]
            )

        for edge in self.graph.edges:
            e = self.graph.edges[edge]
            e["state"] = BasicEdgeState(capacity=e["capacity"], flow=0)

    @classmethod
    def transition_func(
        cls,
        node: NS,
        neighbours: list[
            GraphCellularAutomata.AdjacentState[BasicNodeState, BasicEdgeState]
        ],
    ) -> tuple[NS, list[ES]]:
        # Simple logic to increase trust by a constant factor for demonstration
        edge_credit_limits = [
            min(
                neighbour.in_edge.capacity - neighbour.in_edge.flow,
                neighbour.node_state.balance,
            )
            for neighbour in neighbours
        ]

        new_credit_limit = sum(edge_credit_limits)
        locked_balance = sum(neighbour.out_edge.flow for neighbour in neighbours)
        debt = sum(neighbour.in_edge.flow for neighbour in neighbours)
        new_balance = node.balance + debt - locked_balance

        new_node_state = BasicNodeState(
            balance=new_balance, credit_limit=[new_credit_limit]
        )
        new_edge_states = {edge.node_index: edge.out_edge for edge in neighbours}
        return new_node_state, new_edge_states

    @classmethod
    def node_action_policy(cls, node: NS) -> NS:
        # The most basic policy: do nothing
        return node


if __name__ == "__main__":
    graph = nx.barabasi_albert_graph(1000, 2, seed=42)
    num_edges = graph.number_of_edges()
    capacities = list(np.random.randint(1, 10000, num_edges))
    balances = {node: np.random.randint(1, 100000) for node in graph.nodes}

    for edge in graph.edges:
        graph.edges[edge]["capacity"] = capacities.pop()

    gca = Maxflow2GCA(graph, balance_distribution=balances)
    records = gca.run_simulation(10)
