from typing import Optional
from fastapi import FastAPI

from clique_sim.simple import VerySimple


app = FastAPI()
protocol = VerySimple()

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


@app.get("/{user_id}/locked")
async def locked(user_id: str):
    return protocol.locked_balance(user_id)


@app.get("/{user_id}/debt")
async def debt(user_id: str, recipient_id: Optional[str] = None):
    return protocol.debt(user_id, recipient_id)


@app.post("/{user_id}/deposit")
async def deposit(user_id: str, amount: int):
    protocol.deposit(user_id, amount)
    return {"message": "Deposited"}


@app.post("/{user_id}/withdraw")
async def withdraw(user_id: str, amount: int):
    protocol.withdraw(user_id, amount)
    return {"message": "Withdrawn"}


@app.post("{user_id}/transfer")
async def transfer(user_id: str, amount: int, recipient_id: str):
    protocol.transfer(user_id, amount, recipient_id)
    return {"message": "Transferred"}


@app.post("/{user_id}/trust")
async def trust(user_id: str, amount: int, recipient_id: str):
    protocol.set_trust(user_id, amount, recipient_id)
    return {"message": "Trust set"}


@app.post("/{user_id}/borrow")
async def borrow(user_id: str, amount: int):
    protocol.borrow(user_id, amount)
    return {"message": "Borrowed"}


@app.post("/{user_id}/repay")
async def repay(user_id: str, amount: int):
    protocol.repay(user_id, amount)
    return {"message": "Repaid"}


# Run the server
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8000)