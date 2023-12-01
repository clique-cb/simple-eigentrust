from simulator import basic_simulation

if __name__ == "__main__":
    for distribution_type in ["equal", "one_rich", "pareto"]:
        basic_simulation(
            num_users=10,
            initial_balance=1000,
            num_days=30,
            transactions_per_day=5,
            distribution_type=distribution_type,
        )
