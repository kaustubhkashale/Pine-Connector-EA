import random
import string
from datetime import datetime
from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel

app = FastAPI()

# MongoDB configuration
MONGO_URI = "mongodb+srv://adminkk:Simba580@kkfx.8rk6m.mongodb.net/?retryWrites=true&w=majority&appName=KKFX" 
DB_NAME = "webhook_db"
COLLECTION_NAME = "orders"

# Connect to MongoDB using Motor
client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]
collection = db[COLLECTION_NAME]

# Helper function to generate order ID
def generate_order_id(action: str) -> str:
    """Generate a unique 6-character alphanumeric order ID with a prefix."""
    prefix = "BUY" if action.lower() == "buy" else "SELL"
    unique_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"{prefix}-{unique_id}"

# Request model for validation (optional but recommended)
class WebhookData(BaseModel):
    account_id: str
    symbol: str
    action: str
    lot: float
    sl: float
    tp: float

@app.post("/webhook")
async def webhook(data: WebhookData):
    """Handle incoming webhook and save data to MongoDB."""
    print("Received data:", data.dict())

    # Generate order ID and timestamp
    order_id = generate_order_id(data.action)
    timestamp = datetime.utcnow()

    # Create the record
    record = {
        "accountid": data.account_id,
        "symbol": data.symbol,
        "action": data.action,
        "lot": data.lot,
        "sl": data.sl,
        "tp": data.tp,
        "order_id": order_id,
        "timestamp": timestamp,
    }

    # Insert into MongoDB
    await collection.insert_one(record)

    return {"status": 200, "message": "Order received", "order_id": order_id}

@app.get("/spiderhook/{account_id}")
async def get_latest_order(account_id: str):
    """Fetch the most recent record for a given account ID."""
    # Query the latest record
    record = await collection.find_one(
        {"accountid": account_id},
        sort=[("timestamp", -1)]  # Sort by timestamp in descending order
    )

    if not record:
        return {"status": 404, "message": "No recent orders found"}

    # Convert MongoDB ObjectId to string
    record["_id"] = str(record["_id"])
    return {"status": 200, "data": record}

@app.get("/")
async def root():
    return {"message": "Hello World"}

# Run the app with Uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
