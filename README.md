# Real-Time Stock Trade Analytics with Apache Flink, Kafka, and PostgreSQL

This project implements a real-time streaming data pipeline that simulates stock trade events, filters high-volume trades using Apache Flink, and stores raw trade data in PostgreSQL. The architecture is containerized using Docker Compose and is suitable for monitoring trading activity in a scalable and modular environment.

## Problem Statement

In high-frequency trading environments, it is critical to detect and respond to significant trade events in real time. For instance, identifying trades with unusually large volumes can provide valuable insights into market movements and institutional behavior.

This project addresses the challenge by:

* Ingesting simulated stock trade events into a Kafka topic.
* Using Apache Flink to detect trades with volume exceeding a predefined threshold.
* Forwarding alerts to a separate Kafka topic.
* Storing all raw trade data into a PostgreSQL database for long-term storage and analysis.

## Architecture Overview

```
Kafka Producer → Kafka Topic (sensors) → Flink Consumer
     ├── PostgreSQL (raw trade data)
     └── Kafka Topic (alerts)
```

* Kafka is used for decoupling and reliable messaging between components.
* Flink is used for real-time stream processing.
* PostgreSQL stores the raw trade data for querying and historical analysis.
* Python powers the producer and the Flink pipeline (via PyFlink).

## Technology Stack

* Apache Kafka
* Apache Flink (PyFlink)
* PostgreSQL
* Docker, Docker Compose
* Python 3.10

## Future Development

This project serves as a strong foundation for real-time stock trade analytics. Potential future enhancements include:

### Scaling for Higher Volume & Wider Schemas

* Implementing a producer that generates a significantly higher volume of data (e.g., millions of events per second) with a wider schema (e.g., 60+ columns) across multiple Kafka topics (e.g., 25+ topics).

### Advanced Flink Analytics

* Utilizing Event Time and Watermarks for accurate, time-based computations (e.g., 1-minute Volume-Weighted Average Price - VWAP).
* Implementing Windowing (e.g., Tumbling or Sliding windows) to calculate aggregates like total volume, average price, min/max over time.
* Leveraging Stateful Processing using Flink's managed state for complex continuous calculations such as running averages or pattern detection.

### Performance Monitoring & Optimization

* Using tools like cAdvisor for monitoring container resource utilization (CPU, memory, network I/O).
* Analyzing Flink UI metrics (records in/out per second, backpressure) and Kafka consumer lag.
* Optimizing Flink's parallelism (task slots) and sink configurations (batch size, interval) for maximum throughput.

### Real-Time Dashboard

* Connecting processed data (from PostgreSQL or a dedicated Kafka topic) to visualization tools like Grafana for live market metrics and alerts.

### Machine Learning Integration

* Feeding processed features into real-time ML models in Flink for use cases like fraud detection, price prediction, etc.

## Setup Instructions

Assumes you're in the root directory of the project where `docker-compose.yml` exists.

### Step 0: Stop and Remove Existing Containers

```bash
docker compose down -v
```

### Step 1: Launch Docker Containers

```bash
docker compose up -d --build
```

### Step 2: Drop and Recreate Kafka Topics

```bash
docker compose exec kafka kafka-topics --delete --topic sensors --bootstrap-server localhost:9092
docker compose exec kafka kafka-topics --delete --topic alerts --bootstrap-server localhost:9092

docker compose exec kafka kafka-topics --create --topic sensors --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
docker compose exec kafka kafka-topics --create --topic alerts --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

### Step 3: Connect to PostgreSQL and Create Table

```bash
docker compose exec postgres psql -h localhost -U flinkuser -d flinkdb
```

Password: `flinkpassword`

Inside psql:

```sql
DROP TABLE IF EXISTS stock_trades;

CREATE TABLE stock_trades (
    trade_id VARCHAR(255) PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    price NUMERIC(10, 4) NOT NULL,
    volume INT NOT NULL,
    trade_timestamp TIMESTAMPTZ NOT NULL
    -- Additional fields if needed:
    -- trade_type VARCHAR(10),
    -- exchange VARCHAR(10)
);

\d stock_trades
\q
```

### Step 4: Start Kafka Producer

```bash
pip install kafka-python
python pyflink/usr_jobs/kafka_producer.py
```

### Step 5: Run Flink Job to Store Data in PostgreSQL

```bash
docker compose exec flink-jobmanager flink run -py /opt/flink/usr_jobs/postgres_sink.py
```

Visit Flink Web UI at: [http://localhost:8081](http://localhost:8081)

### Step 6: Query Raw Trade Data

```bash
docker compose exec postgres psql -h localhost -U flinkuser -d flinkdb
```

Query:

```sql
SELECT trade_id, ticker, price, volume, trade_timestamp
FROM stock_trades
LIMIT 10;
```

### Step 7 (Optional): View High-Volume Alerts

```bash
docker compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic alerts --from-beginning
```

## Directory Structure

```
.
├── usr_jobs/
│   ├── kafka_producer.py
│   ├── kafka_consumer.py
│   └── postgres_sink.py
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .gitignore
└── README.md
```

## License

This project is a modified version of an open-source streaming pipeline. Please refer to the LICENSE file for more details or apply your own license if deploying publicly.

## Author

Developed and maintained by **Bikram Dutta**. For inquiries, suggestions, or collaboration, please open an issue or contact directly via GitHub.

```

