from abc import ABC, abstractmethod
from typing import TypeVar, Generic, NamedTuple

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
        node: NS
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
    def transition_func(cls, node: NS, neighbours: list[AdjacentState]) -> tuple[NS, list[ES]]:
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
                result[node] = self.node_action_policy(graph.nodes[node])
            return result

        def _states_apply(params, substep, state_history, previous_state, policy_input):               
            graph = previous_state["graph"]
            for node in policy_input:
                graph.nodes[node] = policy_input[node] 

            for node in graph.nodes:
                neighbours = [
                    self.AdjacentState(
                        node=graph.nodes[n],
                        in_edge=graph.edges[n, node],
                        out_edge=graph.edges[node, n]
                    )
                    for n in graph.neighbors(node)
                ]
                new_node_state, new_edge_states = self.transition_func(graph.nodes[node], neighbours)
                graph.nodes[node] = new_node_state
                for n, edge in graph.edges(node, data=True):
                    edge["state"] = new_edge_states[n]

            return "graph", graph
        
        partial_state_update_block = [
            {
                "policies": {"user_actions": _policies_apply},
                "variables": {"protocol": _states_apply},
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





    

