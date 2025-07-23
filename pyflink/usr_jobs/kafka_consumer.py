import json
from pyflink.common import WatermarkStrategy
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors.kafka import KafkaOffsetsInitializer, KafkaSource

def parse_and_filter_stocks(value: str) -> str | None:
    print(f"[RECEIVED] Raw message: {value}")
    VOLUME_THRESHOLD = 1_000_000

    try:
        data = json.loads(value)

        trade_id = data["trade_id"]
        ticker = data["ticker"]
        volume = int(data["volume"])
        timestamp = data["timestamp"]

        if volume > VOLUME_THRESHOLD:
            alert_message = {
                "trade_id": trade_id,
                "ticker": ticker,
                "volume": volume,
                "alert": f"Large trade detected for {ticker}",
                "timestamp": timestamp
            }
            alert_json = json.dumps(alert_message)
            print(f"[ALERT] Generated alert: {alert_json}")
            return alert_json
        else:
            print(f"[SKIPPED] Trade volume {volume} is below threshold.")
    except Exception as e:
        print(f"[ERROR] Failed to parse message: {value}. Error: {e}")
    
    return None

def main() -> None:
    env = StreamExecutionEnvironment.get_execution_environment()

    current_dir_list = __file__.split("/")[:-1]
    current_dir = "/".join(current_dir_list)
    
    env.add_jars(
        f"file://{current_dir}/flink-sql-connector-kafka-3.1.0-1.18.jar"
    )

    properties = {
        "bootstrap.servers": "kafka:19092",
        "group.id": "stock-alerts-consumer",
    }
    
    offset = KafkaOffsetsInitializer.latest()

    kafka_source = (
        KafkaSource.builder()
        .set_topics("sensors")
        .set_properties(properties)
        .set_starting_offsets(offset)
        .set_value_only_deserializer(SimpleStringSchema())
        .build()
    )

    data_stream = env.from_source(
        kafka_source, WatermarkStrategy.no_watermarks(), "Kafka Stock Topic"
    )

    print("[INIT] Starting to read data from Kafka topic 'sensors'...")

    alerts = data_stream.map(parse_and_filter_stocks).filter(lambda x: x is not None)

    alerts.print()

    env.execute("Kafka Stock Alert Consumer")

if __name__ == "__main__":
    main()
