Real-Time Stock Trade Analytics with Apache Flink, Kafka, and PostgreSQL
This project implements a real-time streaming data pipeline that simulates stock trade events, filters high-volume trades using Apache Flink, and stores raw trade data in PostgreSQL. The architecture is containerized using Docker Compose and is suitable for monitoring trading activity in a scalable and modular environment.
Problem Statement
In high-frequency trading environments, it is critical to detect and respond to significant trade events in real time. For instance, identifying trades with unusually large volumes can provide valuable insights into market movements and institutional behavior.

This project addresses the challenge by:

Ingesting simulated stock trade events into a Kafka topic.

Using Apache Flink to detect trades with volume exceeding a predefined threshold.

Forwarding alerts to a separate Kafka topic.

Storing all raw trade data into a PostgreSQL database for long-term storage and analysis.

Architecture Overview
Kafka Producer → Kafka Topic (sensors) → Flink Consumer
     ├── PostgreSQL (raw trade data)
     └── Kafka Topic (alerts)

Kafka is used for decoupling and reliable messaging between components.

Flink is used for real-time stream processing.

PostgreSQL stores the raw trade data for querying and historical analysis.

Python powers the producer and the Flink pipeline (via PyFlink).

Technology Stack
Apache Kafka

Apache Flink (PyFlink)

PostgreSQL

Docker, Docker Compose

Python 3.10

Setup Instructions
These instructions assume you are in the root directory of the flink-stock-analytics project (where docker-compose.yml is located).

Step 0: Stop and Remove Existing Docker Containers (Clean Up)
First, stop and remove any previously running Docker containers and their associated volumes to ensure a completely clean slate.

docker compose down -v

This command stops and removes all services defined in your docker-compose.yml and also removes anonymous volumes, ensuring no lingering data.

Step 1: Launch Docker Containers (with Build)
Start all the services defined in your docker-compose.yml file (Zookeeper, Kafka, Flink JobManager, Flink TaskManager, PostgreSQL). The --build flag ensures that Flink images are rebuilt with the latest code changes.

docker compose up -d --build

The -d flag runs the containers in detached mode (in the background). You can watch the logs if you omit -d.

Step 2: Drop and Recreate Kafka Topics
Even after stopping containers, Kafka topic metadata can sometimes persist. Let's explicitly drop and recreate them to be sure.

Connect to the Kafka container and delete the existing topics:

docker compose exec kafka kafka-topics --delete --topic sensors --bootstrap-server localhost:9092
docker compose exec kafka kafka-topics --delete --topic alerts --bootstrap-server localhost:9092

You might see warnings like "Topic sensors does not exist" if they weren't created before, which is fine.

Now, recreate the necessary topics:

docker compose exec kafka kafka-topics --create --topic sensors --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
docker compose exec kafka kafka-topics --create --topic alerts --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1

Verify topic creation:

docker compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list

Step 3: Connect to PostgreSQL and Drop/Create Table
Connect to the PostgreSQL instance:

docker compose exec postgres psql -h localhost -U flinkuser -d flinkdb

When prompted for the password, enter: flinkpassword

Once connected to the flinkdb prompt, first drop the stock_trades table if it exists. This cleans up any old schema or data:

DROP TABLE IF EXISTS stock_trades;

(You might see a notice "NOTICE: table "stock_trades" does not exist, skipping" if it wasn't there, which is harmless.)

Now, create the stock_trades table with the correct schema for stock trade data, ensuring ticker and trade_timestamp column names match the Flink job:

CREATE TABLE stock_trades (
    trade_id VARCHAR(255) PRIMARY KEY,
    ticker VARCHAR(10) NOT NULL,
    price NUMERIC(10, 4) NOT NULL,
    volume INT NOT NULL,
    trade_timestamp TIMESTAMPTZ NOT NULL
    -- Add other fields if your simulated trade events contain more data
    -- For example:
    -- trade_type VARCHAR(10), -- e.g., 'BUY', 'SELL'
    -- exchange VARCHAR(10)
);

Verify the table creation and schema:

\d stock_trades

You should see the newly defined columns.

Type \q and press Enter to exit the PostgreSQL command line.

Step 4: Start Kafka Producer
Install the required Python dependency (if not already installed in your local environment):

pip install kafka-python

Run the producer script in a new terminal window. This will start generating and sending simulated stock trade events to the sensors topic:

python pyflink/usr_jobs/kafka_producer.py

You should see output indicating that stock data is being produced. Keep this terminal window open.

Step 5: Run Flink Consumer (to Store Data in PostgreSQL)
In a separate new terminal window, submit the Flink job that processes the stock trade stream and stores it into PostgreSQL:

docker compose exec flink-jobmanager flink run -py /opt/flink/usr_jobs/postgres_sink.py

This command runs the postgres_sink.py job, which is configured to send data to your PostgreSQL stock_trades table.

Monitor Flink jobs at the Web UI: http://localhost:8081

Step 6: Query Raw Trade Data in PostgreSQL
In yet another new terminal window, connect to PostgreSQL again:

docker compose exec postgres psql -h localhost -U flinkuser -d flinkdb

Password: flinkpassword

Now, query the stock_trades table. Since the Flink job writes data in batches, it might take a few seconds for the first records to appear.

SELECT
    trade_id, ticker, price, volume, trade_timestamp
FROM stock_trades
LIMIT 10;

You should now see the first 10 rows of stock trade data in your table. If you continue running the producer and the Flink job, more data will accumulate.

(Optional) Step 7: Consume Alerts from Kafka
In a fourth terminal window, you can read the filtered alerts (trades with volume > 1,000,000) that Flink also sends to the alerts Kafka topic:

docker compose exec kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic alerts --from-beginning

You should see JSON messages for trades that exceeded the volume threshold.

Directory Structure
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

License
This project is a modified version of an open-source streaming pipeline. Please refer to the LICENSE file for more details or apply your own license if deploying publicly.

Author
Developed and maintained by Bikram Dutta. For inquiries, suggestions, or collaboration, please open an issue or contact directly via GitHub.
