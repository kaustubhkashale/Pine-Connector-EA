import random
import string
from datetime import datetime, timedelta
from fastapi import FastAPI, Request
from pymongo import MongoClient
from mangum import Mangum

app = FastAPI()

# MongoDB configuration
MONGO_URI = "mongodb+srv://adminkk:Simba580@kkfx.8rk6m.mongodb.net/?retryWrites=true&w=majority&appName=KKFX" 
DB_NAME = "webhook_db"
COLLECTION_NAME = "orders"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

def generate_order_id(action: str) -> str:
    """Generate a unique 6-character alphanumeric order ID with a prefix."""
    prefix = "BUY" if action.lower() == "buy" else "SELL"
    unique_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{unique_id}"

@app.post("/webhook")
async def webhook(request: Request):
    """Handle incoming webhook and save data to MongoDB."""
    data = await request.json()
    print("Received data:", data)

    # Extract required fields
    account_id = data.get("account_id")
    symbol = data.get("symbol")
    action = data.get("action")
    lot = data.get("lot")
    sl = data.get("sl")
    tp = data.get("tp")

    if not all([symbol, action, lot, sl, tp]):
        return {"status": 400, "message": "Missing required fields"}

    # Generate order ID and timestamp
    order_id = generate_order_id(action)
    timestamp = datetime.utcnow()

    # Create the record
    record = {
        "accountid": account_id,
        "symbol": symbol,
        "action": action,
        "lot": lot,
        "sl": sl,
        "tp": tp,
        "order_id": order_id,
        "timestamp": timestamp,
    }

    # Insert into MongoDB
    collection.insert_one(record)

    return {"status": 200, "message": "Order received", "order_id": order_id}

@app.get("/spiderhook/{account_id}")
async def get_latest_order(account_id: str):
    """Fetch the latest record for an account ID within the last 1 minute."""
    one_min_ago = datetime.utcnow() - timedelta(minutes=1)

    # Query the latest record
    record = collection.find_one(
        {"accountid": account_id, "timestamp": {"$gte": one_min_ago}},
        sort=[("timestamp", -1)]  # Sort by timestamp in descending order
    )

    if not record:
        return {"status": 404, "message": "No recent orders found"}

    # Convert MongoDB ObjectId to string
    record["_id"] = str(record["_id"])
    return {"status": 200, "data": record}

# AWS Lambda handler using Mangum
# handler = Mangum(app)
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="127.0.0.1", port=8000)