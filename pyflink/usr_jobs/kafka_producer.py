import json
import random
import time
from datetime import datetime, timezone
import uuid
from kafka import KafkaProducer

SLEEP_TIME = 1 

def generate_stock_data() -> dict:
    tickers = ['GOOGL', 'AAPL', 'MSFT', 'AMZN', 'TSLA']
    ticker = random.choice(tickers)
    price = round(random.uniform(100, 1500), 2)
    volume = random.randint(10000, 5000000)
    
    stock_data = {
        "trade_id": uuid.uuid4().hex,
        "ticker": ticker,
        "price": price,
        "volume": volume,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return stock_data

def main() -> None:
    producer = KafkaProducer(
        bootstrap_servers="localhost:9092",
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
    )

    while True:
        stock_data = generate_stock_data()
        producer.send("sensors", value=stock_data)
        print(f"Produced: {stock_data}")
        time.sleep(SLEEP_TIME)

if __name__ == "__main__":
    main()
