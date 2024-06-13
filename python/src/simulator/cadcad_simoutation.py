import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd
from cadCAD.configuration import Configuration, Experiment
from cadCAD.configuration.utils import config_sim
from cadCAD.engine import ExecutionMode, ExecutionContext, Executor

from clique_sim.simple_with_stratagy import SimpleWithParameters
from clique_sim.stratagy.basic import ExampleTrustStrategy


def policy_function(params, step, sL, s):
    protocol = s["protocol"]
    user_id = "user1"  # Example: Applying trust strategy for user1
    protocol.apply_trust_strategy(user_id)
    return {}


def update_function(params, step, sL, s, _input):
    return ("protocol", s["protocol"])


def run_cadcad_simulation():
    # Initial strategy and protocol setup
    initial_strategy = ExampleTrustStrategy()
    protocol = SimpleWithParameters(initial_strategy)

    # Add some users to the protocol
    user_ids = ["user1", "user2", "user3"]
    for user_id in user_ids:
        protocol.register(user_id)

    # Define initial state and simulation parameters
    initial_state = {"protocol": protocol}
    sim_params = {
        "N": 1,  # Number of Monte Carlo runs
        "T": range(10),  # Number of time steps
        # "M": {},  # Model parameters, empty in this case since no sweeping is used
    }

    # Define policy and state update functions
    partial_state_update_block = [
        {
            "policies": {"apply_trust_policy": policy_function},
            "variables": {"protocol": update_function},
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

    # print(records)
    # # Output results
    # df = pd.DataFrame(records)
    # print(df[["simulation", "timestep", "run", "protocol"]])
    #
    # # Visualize the final network state, if needed
    # final_protocol = df.iloc[-1]["protocol"]
    # final_graph = final_protocol._graph
    # nx.draw(final_graph, with_labels=True, node_color="lightblue")
    # plt.show()
