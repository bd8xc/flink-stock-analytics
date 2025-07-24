
# Real-Time Stock Trade Analytics with Apache Flink, Kafka, and PostgreSQL

This project implements a real-time streaming data pipeline that simulates stock trade events, filters high-volume trades using Apache Flink, and stores raw trade data in PostgreSQL. The architecture is containerized using Docker Compose and is suitable for monitoring trading activity in a scalable and modular environment.

---

## Problem Statement

In high-frequency trading environments, it is critical to detect and respond to significant trade events in real time. For instance, identifying trades with unusually large volumes can provide valuable insights into market movements and institutional behavior.

This project addresses the challenge by:

* Ingesting simulated stock trade events into a Kafka topic.
* Using Apache Flink to detect trades with volume exceeding a predefined threshold.
* Forwarding alerts to a separate Kafka topic.
* Storing all raw trade data into a PostgreSQL database for long-term storage and analysis.

---

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

---

## Technology Stack

* Apache Kafka
* Apache Flink (PyFlink)
* PostgreSQL
* Docker, Docker Compose
* Python 3.10

---

## Setup Instructions

These instructions assume you are in the root directory of the project (where `docker-compose.yml` is located).

### Step 0: Clean Up Existing Containers

Stop and remove any previously running Docker containers and associated volumes:

```bash
docker compose down -v
```

---

### Step 1: Launch Docker Containers

Build and start all services in detached mode:

```bash
docker compose up -d --build
```

---

### Step 2: Drop and Recreate Kafka Topics

Delete existing topics (ignore warnings if topics don't exist):

```bash
docker compose exec kafka kafka-topics --delete --topic sensors --bootstrap-server localhost:9092
docker compose exec kafka kafka-topics --delete --topic alerts --bootstrap-server localhost:9092
```

Recreate topics:

```bash
docker compose exec kafka kafka-topics --create --topic sensors --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
docker compose exec kafka kafka-topics --create --topic alerts --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

Verify:

```bash
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

---

### Step 3: Prepare PostgreSQL

Connect to the PostgreSQL instance:

```bash
docker compose exec postgres psql -h localhost -U flinkuser -d flinkdb
```

Password: `flinkpassword`

Drop the existing table (if it exists):

```sql
DROP TABLE IF EXISTS stock_trades;
```

Create the table:

```sql
CREATE TABLE stock_trades (
    trade_id VARCHAR(255) PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    price NUMERIC(10, 4) NOT NULL,
    volume INT NOT NULL,
    trade_timestamp TIMESTAMPTZ NOT NULL
);
```

Verify table creation:

```sql
\d stock_trades
```

Exit:

```sql
\q
```

---

### Step 4: Start Kafka Producer

Install the required dependency:

```bash
pip install kafka-python
```

Run the producer:

```bash
python pyflink/usr_jobs/kafka_producer.py
```

---

### Step 5: Run Flink Job to Store Data in PostgreSQL

Submit the Flink job:

```bash
docker compose exec flink-jobmanager flink run -py /opt/flink/usr_jobs/postgres_sink.py
```

Monitor via Flink Web UI at: [http://localhost:8081](http://localhost:8081)

---

### Step 6: Query Data in PostgreSQL

Reconnect to PostgreSQL:

```bash
docker compose exec postgres psql -h localhost -U flinkuser -d flinkdb
```

Run a sample query:

```sql
SELECT trade_id, ticker, price, volume, trade_timestamp
FROM stock_trades
LIMIT 10;
```

---

### Step 7 (Optional): Consume Alerts from Kafka

To view high-volume trade alerts:

```bash
docker compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic alerts --from-beginning
```

---

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

---

## License

This project is a modified version of an open-source streaming pipeline. Please refer to the LICENSE file for more details or apply your own license if deploying publicly.

---

## Author

Developed and maintained by **Bikram Dutta**. For inquiries, suggestions, or collaboration, please open an issue or contact directly via GitHub.


