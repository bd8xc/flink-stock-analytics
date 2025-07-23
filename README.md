---
# Real-Time Stock Trade Analytics with Apache Flink, Kafka, and PostgreSQL

This project implements a real-time streaming data pipeline that simulates stock trade events, filters high-volume trades using Apache Flink, and stores raw trade data in PostgreSQL. The architecture is containerized using Docker Compose and is suitable for monitoring trading activity in a scalable and modular environment.
---

## Problem Statement

In high-frequency trading environments, it is critical to detect and respond to significant trade events in real time. For instance, identifying trades with unusually large volumes can provide valuable insights into market movements and institutional behavior.

This project addresses the challenge by:

- Ingesting simulated stock trade events into a Kafka topic.
- Using Apache Flink to detect trades with volume exceeding a predefined threshold.
- Forwarding alerts to a separate Kafka topic.
- Storing all raw trade data into a PostgreSQL database for long-term storage and analysis.

---

## Architecture Overview

```
Kafka Producer → Kafka Topic (sensors) → Flink Consumer
     ├── PostgreSQL (raw trade data)
     └── Kafka Topic (alerts)
```

- Kafka is used for decoupling and reliable messaging between components.
- Flink is used for real-time stream processing.
- PostgreSQL stores the raw trade data for querying and historical analysis.
- Python powers the producer and the Flink pipeline (via PyFlink).

---

## Technology Stack

- Apache Kafka
- Apache Flink (PyFlink)
- PostgreSQL
- Docker, Docker Compose
- Python 3.10

---

## Setup Instructions

### Step 1: Launch Docker Containers

Start the multi-container application:

```
docker compose up
```

Watch the logs to ensure all services start correctly.

---

### Step 2: Create Kafka Topics

Run the following commands to create the necessary topics:

```
docker compose exec kafka kafka-topics --create --topic sensors --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
docker compose exec kafka kafka-topics --create --topic alerts --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

Verify topic creation:

```
docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

---

### Step 3: Create PostgreSQL Table

Connect to the PostgreSQL instance:

```
psql -h localhost -U flinkuser -d flinkdb
```

Password: `flinkpassword`

Create the table:

```sql
CREATE TABLE raw_sensors_data (
    message_id VARCHAR(255) PRIMARY KEY,
    sensor_id INT NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL
);
```

Verify:

```sql
\d raw_sensors_data
```

---

### Step 4: Start Kafka Producer

Install the required dependency:

```
pip install kafka-python
```

Run the producer script:

```
python pyflink/usr_jobs/kafka_producer.py
```

This will start generating and sending simulated stock trade events to the `sensors` topic.

---

### Step 5: Run Flink Consumer

Submit the Flink job that processes the stock trade stream:

```
docker compose exec flink-jobmanager flink run -py /opt/flink/usr_jobs/kafka_consumer.py
```

Alternatively, to store into PostgreSQL:

```
docker compose exec flink-jobmanager flink run -py /opt/flink/usr_jobs/postgres_sink.py
```

Monitor Flink jobs at: [http://localhost:8081](http://localhost:8081)

---

### Step 6: Consume Alerts from Kafka

To read filtered alerts:

```
docker compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic alerts --from-beginning
```

---

### Step 7: Query Raw Trade Data in PostgreSQL

```sql
SELECT
    *,
    (message::json->>'volume')::numeric AS volume
FROM raw_sensors_data
LIMIT 10;
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

This project is a modified version of an open-source streaming pipeline. Please refer to the `LICENSE` file for more details or apply your own license if deploying publicly.

---

## Author

Developed and maintained by Bikram Dutta. For inquiries, suggestions, or collaboration, please open an issue or contact directly via GitHub.
