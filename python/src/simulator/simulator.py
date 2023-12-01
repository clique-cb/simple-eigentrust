import random

import networkx as nx
import numpy as np

from clique_sim.simple import VerySimple


def create_random_digraph(n, p):
    g = nx.fast_gnp_random_graph(n, p, directed=True)
    for u, v, d in g.edges(data=True):
        d["weight"] = np.random.uniform(0.0, 1.0)

    return g


def create_cycle(n):
    g = nx.DiGraph()
    for i in range(n):
        g.add_edge(i, (i + 1) % n, weight=1.0)

    return g


def to_absolute_capacities(g, max_money=1000):
    g_abs = nx.DiGraph()
    for u, v, d in g.edges(data=True):
        g_abs.add_edge(u, v, capacity=int(d["weight"] * max_money))
    return g_abs


def to_relative_weights(g, p):
    g_rel = nx.DiGraph()
    for u, v, d in g.edges(data=True):
        deposit = int(p[u])
        g_rel.add_edge(u, v, weight=d["weight"] / deposit)
    return g_rel


def create_random_digraph_absolute(n, p, max_money=1000):
    return to_absolute_capacities(create_random_digraph(n, p), max_money)


def setup_simulation(
    num_users, distribution_type, max_money=1000, p=0.3, pareto_shape=1.5
):
    protocol = VerySimple()

    # Create a list of user IDs
    user_ids = [f"user_{i}" for i in range(num_users)]

    # Initialize balances based on the distribution type
    if distribution_type == "equal":
        # Distribute max_money equally among all users
        equal_amount = max_money // num_users
        balances = [equal_amount for _ in user_ids]
    elif distribution_type == "one_rich":
        # All money to one user, others get nothing
        balances = [0 for _ in user_ids]
        balances[np.random.randint(num_users)] = max_money
    elif distribution_type == "pareto":
        balances = np.random.pareto(pareto_shape, num_users) * 100
        balances = balances.astype(int)
    else:
        raise ValueError("Invalid distribution type")

    # Add users and deposit initial balance
    for user_id, balance in zip(user_ids, balances):
        protocol.add_user(user_id)
        protocol.deposit(user_id, balance)

    # Create a random directed graph with absolute capacities
    g = create_random_digraph_absolute(num_users, p, max_money)

    # Establish trust relationships based on the graph
    for u, v, d in g.edges(data=True):
        protocol.set_trust(f"user_{u}", d["capacity"], f"user_{v}")

    return protocol, user_ids


def simulate_day_bank_run(transactions_per_day, protocol, user_ids):
    failed_transactions = 0
    for _ in range(transactions_per_day):
        ids = [x for x in user_ids if protocol.available_balance(x) >= 1]
        if not ids:
            break
        borrower = random.choice(ids)
        credit_limit = protocol.credit_limit(borrower)

        # Users attempt to withdraw a larger portion of their credit limit
        amount = random.randint(int(0.5 * credit_limit), credit_limit)

        try:
            protocol.borrow(borrower, amount)
        except ValueError as e:
            print(f"Transaction failed: {e}")
            failed_transactions += 1

    return failed_transactions


def simulate_day(transactions_per_day, protocol, user_ids):
    for _ in range(transactions_per_day):
        ids = [x for x in user_ids if protocol.available_balance(x) >= 1]
        if not ids:
            return
        borrower = random.choice(ids)
        credit_limit = protocol.credit_limit(borrower)
        amount = random.randint(1, credit_limit)  # Random loan amount

        try:
            protocol.borrow(borrower, amount)
        except ValueError as e:
            print(f"Transaction failed: {e}")


def simulate_bank_run(
    num_users, initial_balance, num_days, transactions_per_day, distribution_type
):
    protocol, user_ids = setup_simulation(num_users, distribution_type, initial_balance)

    total_failed_transactions = 0
    for day in range(num_days):
        failed_transactions = simulate_day_bank_run(
            transactions_per_day, protocol, user_ids
        )
        total_failed_transactions += failed_transactions

    print(f"Total failed transactions: {total_failed_transactions}")


def basic_simulation(
    num_users, initial_balance, num_days, transactions_per_day, distribution_type
):
    protocol, user_ids = setup_simulation(num_users, distribution_type, initial_balance)

    for day in range(num_days):
        simulate_day(transactions_per_day, protocol, user_ids)
