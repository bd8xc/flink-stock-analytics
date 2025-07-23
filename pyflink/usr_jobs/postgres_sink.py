import json
import logging
from datetime import datetime

from pyflink.common import Row, Types, WatermarkStrategy
from pyflink.common.serialization import SimpleStringSchema
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.connectors import JdbcSink
from pyflink.datastream.connectors.jdbc import (
    JdbcConnectionOptions,
    JdbcExecutionOptions,
)
from pyflink.datastream.connectors.kafka import (
    DeliveryGuarantee,
    KafkaOffsetsInitializer,
    KafkaRecordSerializationSchema,
    KafkaSink,
    KafkaSource,
)

KAFKA_HOST = "kafka:19092"
POSTGRES_HOST = "postgres:5432"

def parse_data(data: str) -> Row:
    data = json.loads(data)
    trade_id = data["trade_id"]
    ticker = data["ticker"]
    price = float(data["price"])
    volume = int(data["volume"])
    timestamp = datetime.strptime(data["timestamp"], "%Y-%m-%dT%H:%M:%S.%f+00:00")
    return Row(trade_id, ticker, price, volume, timestamp)

def filter_large_trades(value: str) -> str | None:
    VOLUME_THRESHOLD = 1_000_000
    data = json.loads(value)
    volume = int(data["volume"])
    if volume > VOLUME_THRESHOLD:
        alert_message = {
            "trade_id": data["trade_id"],
            "ticker": data["ticker"],
            "volume": volume,
            "alert": f"Large trade detected for {data['ticker']}",
            "timestamp": data["timestamp"],
        }
        return json.dumps(alert_message)
    return None

def initialize_env() -> StreamExecutionEnvironment:
    env = StreamExecutionEnvironment.get_execution_environment()
    root_dir_list = __file__.split("/")[:-2]
    root_dir = "/".join(root_dir_list)
    env.add_jars(
        f"file://{root_dir}/lib/flink-connector-jdbc-3.1.2-1.18.jar",
        f"file://{root_dir}/lib/postgresql-42.7.3.jar",
        f"file://{root_dir}/lib/flink-sql-connector-kafka-3.1.0-1.18.jar",
    )
    return env

def configure_source(server: str, earliest: bool = False) -> KafkaSource:
    properties = {"bootstrap.servers": server, "group.id": "stock-traders"}
    offset = KafkaOffsetsInitializer.earliest() if earliest else KafkaOffsetsInitializer.latest()
    return (
        KafkaSource.builder()
        .set_topics("sensors")
        .set_properties(properties)
        .set_starting_offsets(offset)
        .set_value_only_deserializer(SimpleStringSchema())
        .build()
    )

def configure_postgre_sink(sql_dml: str, type_info: Types) -> JdbcSink:
    return JdbcSink.sink(
        sql_dml,
        type_info,
        JdbcConnectionOptions.JdbcConnectionOptionsBuilder()
        .with_url(f"jdbc:postgresql://{POSTGRES_HOST}/flinkdb")
        .with_driver_name("org.postgresql.Driver")
        .with_user_name("flinkuser")
        .with_password("flinkpassword")
        .build(),
        JdbcExecutionOptions.builder()
        .with_batch_interval_ms(1000)
        .with_batch_size(200)
        .with_max_retries(5)
        .build(),
    )

def configure_kafka_sink(server: str, topic_name: str) -> KafkaSink:
    return (
        KafkaSink.builder()
        .set_bootstrap_servers(server)
        .set_record_serializer(
            KafkaRecordSerializationSchema.builder()
            .set_topic(topic_name)
            .set_value_serialization_schema(SimpleStringSchema())
            .build()
        )
        .set_delivery_guarantee(DeliveryGuarantee.AT_LEAST_ONCE)
        .build()
    )

def main() -> None:
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

    logger.info("Initializing environment")
    env = initialize_env()

    logger.info("Configuring source and sinks")
    kafka_source = configure_source(KAFKA_HOST)

    sql_dml = (
        "INSERT INTO stock_trades (trade_id, ticker, price, volume, timestamp) "
        "VALUES (?, ?, ?, ?, ?)"
    )

    TYPE_INFO = Types.ROW(
        [
            Types.STRING(),
            Types.STRING(),
            Types.FLOAT(),
            Types.LONG(),
            Types.SQL_TIMESTAMP(),
        ]
    )

    jdbc_sink = configure_postgre_sink(sql_dml, TYPE_INFO)
    kafka_sink = configure_kafka_sink(KAFKA_HOST, "alerts")

    logger.info("Source and sinks initialized")

    data_stream = env.from_source(
        kafka_source, WatermarkStrategy.no_watermarks(), "Kafka Stock Topic"
    )

    transformed_data = data_stream.map(parse_data, output_type=TYPE_INFO)

    alarms_data = data_stream.map(
        filter_large_trades, output_type=Types.STRING()
    ).filter(lambda x: x is not None)

    logger.info("Defined transformations to data stream")

    logger.info("Ready to sink data")
    alarms_data.print()
    alarms_data.sink_to(kafka_sink)
    transformed_data.add_sink(jdbc_sink)

    env.execute("Flink Stock Processing Job")

if __name__ == "__main__":
    main()
