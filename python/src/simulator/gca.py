from abc import ABC, abstractmethod
from typing import TypeVar, Generic, NamedTuple, List

import numpy as np
import itertools
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


# def _deep_merge_pydantic(dct, merge_dct):
#     for k, v in merge_dct.items():
#         if k in dct and isinstance(dct[k], BaseModel):
#             dct[k] = dct[k].model_copy(update=v.model_dump())
#         elif k in dct and isinstance(dct[k], dict) and isinstance(v, dict):
#             _deep_merge_pydantic(dct[k], v)
#         else:
#             dct[k] = v
#     return dct


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
        in_edge: ES | None
        out_edge: ES | None

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

    @abstractmethod
    def transition_func(
        self, node: NS, node_index: int, neighbours: list[AdjacentState]
    ) -> tuple[NS, dict[(int, int), ES]]:
        """
        Transition rule for the node state update.
        """
        pass

    @abstractmethod
    def node_action_policy(self, node: NS) -> NS:
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

            def _get_state(x: dict | None):
                return x["state"] if x else None

            for node in graph.nodes:
                neighbours = [
                    self.AdjacentState(
                        node_index=n,
                        node_state=graph.nodes[n]["state"],
                        in_edge=_get_state(graph.in_edges.get((n, node))),
                        out_edge=_get_state(graph.out_edges.get((node, n))),
                    )
                    for n in itertools.chain(graph.predecessors(node), graph.successors(node))
                ]
                new_node_state, new_edge_states = self.transition_func(
                    graph.nodes[node]["state"], node, neighbours
                )

                next_node_states[node] = new_node_state

                # TODO: check where is the edge depth
                next_edge_states = next_edge_states | new_edge_states

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

    def transition_func(
        self,
        node: NS,
        node_index: int,
        neighbours: list[
            GraphCellularAutomata.AdjacentState[BasicNodeState, BasicEdgeState]
        ],
    ) -> tuple[NS, dict[(int, int), ES]]:
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

        new_edge_states = {(node_index, edge.node_index): edge.out_edge for edge in neighbours}
        return new_node_state, new_edge_states

    def node_action_policy(self, node: NS) -> NS:
        # The most basic policy: do nothing
        return node



class VesselNodeState(NodeState):
    balance: float
    phantom_balance: float
    phantom_excess: float
    is_open: bool = False

    @property
    def credit_limit(self):
        return max(self.phantom_excess - self.balance, 0)



class VesselEdgeState(EdgeState):
    capacity: float
    flow: float
    phantom_flow: float
    height: float
    is_open: bool = False


class VesselsGCA(GraphCellularAutomata):
    def initialize_graph(
        self,
        balance_distribution: dict[int, float],
        time_scale: float = 1.0, 
        fractional_banking_coeff: float = 1.0,
        **kwargs
    ):
        self.fractional_banking_coeff = fractional_banking_coeff
        self.time_scale = time_scale

        for node in self.graph.nodes:
            b = balance_distribution[node]
            self.graph.nodes[node]["state"] = VesselNodeState(
                balance=b, phantom_balance=b, phantom_excess=b,
            )

        for edge in self.graph.edges:
            e = self.graph.edges[edge]
            e["state"] = VesselEdgeState(capacity=e["capacity"], height=e["height"], flow=0, phantom_flow=0)

    def transition_func(
        self,
        node: NS,
        node_index: int,
        neighbours: list[
            GraphCellularAutomata.AdjacentState[VesselNodeState, VesselEdgeState]
        ],
    ) -> tuple[NS, dict[(int, int), ES]]:
        # Simple logic to increase trust by a constant factor for demonstration

        in_neighbours = [neighbour for neighbour in neighbours if neighbour.in_edge is not None]

        out_neighbours = [neighbour for neighbour in neighbours if neighbour.out_edge is not None]
        out_neighbours = sorted(out_neighbours, key=lambda x: (x.out_edge.height, x.out_edge.capacity))

        cur_balance = node.phantom_balance
        cur_excess = node.phantom_excess
        out_flows = {}

        for neighbour in out_neighbours:
            height_above_ours = max(cur_balance - neighbour.out_edge.height, 0)
            height_above_theirs = max(neighbour.node_state.phantom_balance - neighbour.out_edge.height, 0)
            h_diff = max(height_above_ours - height_above_theirs, 0)
            out_flows[neighbour.node_index] = self.time_scale * neighbour.out_edge.capacity * np.sqrt(2 * h_diff)
            cur_balance -= self.fractional_banking_coeff * out_flows[neighbour.node_index]

        incoming_flows = sum(neighbour.in_edge.phantom_flow for neighbour in in_neighbours)
        cur_balance += incoming_flows
        cur_excess += incoming_flows

        new_node_state = node.model_copy(update={"phantom_balance": cur_balance, "phantom_excess": cur_excess})
        new_edge_states = {
            (node_index, edge.node_index): edge.out_edge.model_copy(
                update={"phantom_flow": out_flows[edge.node_index]}
            )
            for edge in out_neighbours
        }
        return new_node_state, new_edge_states


    def node_action_policy(self, node: NS) -> NS:
        # The most basic policy: do nothing
        return node


class VesselsGCASingle(GraphCellularAutomata):
    def initialize_graph(
        self,
        balance_distribution: dict[int, float],
        time_scale: float = 1.0,
        fractional_banking_coeff: float = 1.0,
        debting_node: int = 0,
        **kwargs
    ):
        self.time_scale = time_scale
        self.fractional_banking_coeff = fractional_banking_coeff
        self.debting_node = debting_node

        for node in self.graph.nodes:
            b = balance_distribution[node]
            self.graph.nodes[node]["state"] = VesselNodeState(
                balance=b,
                phantom_balance=b,
                phantom_excess=b,
                is_open=(node == debting_node),
            )


        for edge in self.graph.edges:
            e = self.graph.edges[edge]
            e["state"] = VesselEdgeState(capacity=e["capacity"], height=e["height"], flow=0, phantom_flow=0)

    def transition_func(
        self,
        node: NS,
        node_index: int,
        neighbours: list[
            GraphCellularAutomata.AdjacentState[VesselNodeState, VesselEdgeState]
        ],
    ) -> tuple[NS, dict[(int, int), ES]]:
        # Simple logic to increase trust by a constant factor for demonstration

        in_neighbours = [neighbour for neighbour in neighbours if neighbour.in_edge is not None]
        out_neighbours = [neighbour for neighbour in neighbours if neighbour.out_edge is not None]
        out_neighbours = sorted(out_neighbours, key=lambda x: (x.out_edge.height, x.out_edge.capacity))

        cur_balance = node.balance
        is_open = node.is_open or any(neighbour.node_state.is_open for neighbour in out_neighbours)
        out_flows = {}

        for neighbour in out_neighbours:
            if neighbour.out_edge.is_open:
                height_above_ours = max(cur_balance - neighbour.out_edge.height, 0)
                height_above_theirs = max(neighbour.node_state.balance - neighbour.out_edge.height, 0)
                h_diff = max(height_above_ours - height_above_theirs, 0)
                out_flows[neighbour.node_index] = min(
                    self.time_scale * neighbour.out_edge.capacity * np.sqrt(2 * h_diff),
                    cur_balance
                )
                cur_balance -= out_flows[neighbour.node_index]
            else:
                out_flows[neighbour.node_index] = 0

        cur_balance += sum(neighbour.in_edge.flow for neighbour in in_neighbours)

        additional_edge_states = {}

        if is_open:
            # print(node_index, "is open")
            for neighbour in in_neighbours:
                if not neighbour.in_edge.is_open and neighbour.node_index != self.debting_node:
                    additional_edge_states[(neighbour.node_index, node_index)] = neighbour.in_edge.model_copy(
                        update={"is_open": True}
                    )

        new_node_state = node.model_copy(update={"balance": cur_balance, "is_open": is_open})
        new_edge_states = {
            (node_index, edge.node_index): edge.out_edge.model_copy(
                update={"flow": out_flows[edge.node_index]}
            )
            for edge in out_neighbours
        }
        new_edge_states = new_edge_states | additional_edge_states

        return new_node_state, new_edge_states


    def node_action_policy(self, node: NS) -> NS:
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
