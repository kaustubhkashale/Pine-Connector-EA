import random
import string
from datetime import datetime, timedelta
from fastapi import FastAPI, Request, HTTPException
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

class WebhookMessage(BaseModel):
    message: str

@app.post("/webhook")
async def webhook(request: Request):
    """
    Handle incoming webhook, parse the TradingView message from raw content, and save data to MongoDB.
    """
    try:
        # Read raw body content
        body = await request.body()
        message = body.decode('utf-8').strip()  # Decode and clean the message

        # Split the message into components
        components = message.split(",")
        if len(components) != 6:
            raise ValueError("Invalid message format")

        # Extract values from the message
        account_id = components[0].strip()
        symbol = components[1].strip()
        action = components[2].strip().lower()

        # Extract lot, SL, and TP as key=value pairs
        lot = None
        sl = None
        tp = None

        for component in components[3:]:
            key, value = component.split("=")
            if key == "lot":
                lot = float(value)
            elif key == "sl":
                sl = float(value)
            elif key == "tp":
                tp = float(value)

        # Validate extracted data
        if not account_id or not symbol or not action or lot is None or sl is None or tp is None:
            raise ValueError("Missing or invalid data in message")

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
        await collection.insert_one(record)

        return {"status": 200, "message": "Order received", "order_id": order_id}

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail="An error occurred while processing the webhook")

@app.get("/spiderhook/{account_id}")
async def get_latest_order(account_id: str):
    """Fetch the most recent record for a given account ID."""
    # Query the latest record

    record = await collection.find_one(
        {"accountid": account_id},
        sort=[("timestamp", -1)]  # Sort by timestamp in descending order
    )
    current_time = datetime.utcnow()
    record_time = record["timestamp"]

    if not record:
        return {"status": 404, "message": "No recent orders found"}

    if not isinstance(record_time, datetime):
        raise HTTPException(status_code=500, detail="Invalid timestamp in database")

    if (current_time - record_time) > timedelta(seconds=10):
        return {"status": 404, "message": "No orders within the last 10 seconds"}
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
