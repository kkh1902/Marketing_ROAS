#!/usr/bin/env python3
"""
PyFlink - Kafka 연동 테스트
"""

import sys
import os

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

print("="*60, flush=True)
print("PyFlink Kafka Test Starting", flush=True)
print("="*60, flush=True)

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import MapFunction
from pyflink.datastream.connectors.kafka import FlinkKafkaConsumer
from pyflink.common.serialization import SimpleStringSchema
from pyflink.common.typeinfo import Types

from config import FlinkConfig

print("✅ All imports successful", flush=True)


class MessagePrinter(MapFunction):
    """Kafka 메시지 출력"""

    def map(self, value):
        print(f"✅ Received: {value}")
        return value


def main():
    """Kafka 연동 테스트"""

    # 설정 검증
    try:
        FlinkConfig.validate()
        print("✅ Configuration validated", flush=True)
    except Exception as e:
        print(f"❌ Configuration error: {e}", flush=True)
        return 1

    # StreamExecutionEnvironment 생성
    print("Creating Flink StreamExecutionEnvironment...", flush=True)
    env = StreamExecutionEnvironment.get_execution_environment()
    env.set_parallelism(FlinkConfig.PARALLELISM)

    print(f"✅ Flink Environment initialized", flush=True)
    print(f"   Bootstrap Servers: {FlinkConfig.BOOTSTRAP_SERVERS}", flush=True)
    print(f"   Topic: {FlinkConfig.TOPIC}", flush=True)
    print(f"   Group ID: {FlinkConfig.GROUP_ID}", flush=True)

    try:
        # Kafka Consumer 생성
        print("Creating Kafka Consumer...", flush=True)
        kafka_consumer = FlinkKafkaConsumer(
            FlinkConfig.TOPIC,
            SimpleStringSchema(),
            {
                'bootstrap.servers': FlinkConfig.BOOTSTRAP_SERVERS,
                'group.id': FlinkConfig.GROUP_ID,
                'auto.offset.reset': 'earliest',
            }
        )

        print("✅ Kafka Consumer created", flush=True)

        # 데이터 스트림 생성
        print("Adding Kafka source...", flush=True)
        data_stream = env.add_source(kafka_consumer)
        print("✅ Data stream created", flush=True)

        # 메시지 출력
        print("Adding map transformation...", flush=True)
        processed_stream = data_stream.map(MessagePrinter())
        print("✅ Processing pipeline configured", flush=True)

        # 실행
        print("=" * 60, flush=True)
        print("Starting Flink-Kafka connection test...", flush=True)
        print("=" * 60, flush=True)

        env.execute("Kafka-Flink Simple Test")
        print("✅ Job completed successfully!", flush=True)
        return 0

    except Exception as e:
        print(f"❌ Error: {e}", flush=True)
        import traceback
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
        return 1


if __name__ == "__main__":
    sys.exit(main())
