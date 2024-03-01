from typing import Optional, Dict
from fastapi import FastAPI

from clique_sim.protocol import Protocol
from clique_sim.simple import VerySimple


app = FastAPI()
protocol: Protocol = VerySimple()

# Global methods

@app.get("/tvl")
async def total_value_locked():
    return protocol.total_value_locked()


@app.get("/debt")
async def total_debt():
    return protocol.total_debt()


# User methods

@app.post("/register")
async def register(user_id: str):
    protocol.add_user(user_id)
    return {"message": "User registered"}


@app.get("/{user_id}/balance")
async def balance(user_id: str):
    return protocol.available_balance(user_id)


@app.get("/{user_id}/credit_limit")
async def credit_limit(user_id: str):
    return protocol.credit_limit(user_id)


@app.get("/{user_id}/trusted")
async def trusted(user_id: str) -> Dict[str, int]:
    return protocol.trusted(user_id)

@app.get("/{user_id}/locked")
async def locked(user_id: str) -> Dict[str, int]:
    return protocol.locked(user_id)


@app.get("/{user_id}/debt")
async def debt(user_id: str) -> Dict[str, int]:
    return protocol.debt(user_id)


@app.post("/{user_id}/deposit")
async def deposit(user_id: str, amount: int):
    protocol.deposit(user_id, amount)
    return {"message": "Deposited"}


@app.post("/{user_id}/withdraw")
async def withdraw(user_id: str, amount: int):
    protocol.withdraw(user_id, amount)
    return {"message": "Withdrawn"}


@app.post("/{user_id}/transfer")
async def transfer(user_id: str, amount: int, recipient_id: str):
    protocol.transfer(user_id, amount, recipient_id)
    return {"message": "Transferred"}


@app.post("/{user_id}/trust")
async def trust(user_id: str, trust_deltas: Dict[str, int]):
    protocol.set_trust(user_id, trust_deltas)
    return {"message": "Trust set"}


@app.post("/{user_id}/borrow")
async def borrow(user_id: str, debt_deltas: Dict[str, int]):
    protocol.borrow(user_id, debt_deltas)
    return {"message": "Borrowed"}


@app.post("/{user_id}/repay")
async def repay(user_id: str, debt_deltas: Dict[str, int]):
    protocol.repay(user_id, debt_deltas)
    return {"message": "Repaid"}


# Run the server

def main():
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="Run the simulation server")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    args = parser.parse_args()

    uvicorn.run(app, port=args.port, host=args.host)

if __name__ == "__main__":
    main()