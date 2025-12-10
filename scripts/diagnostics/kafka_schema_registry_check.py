"""
Kafka + Schema Registry 통합 테스트 (간단 버전)

테스트 항목:
1. Schema Registry 연결 테스트
2. Kafka 연결 테스트
3. 테스트 메시지 발행
4. 메시지 수신 확인
"""

import requests
import json
from kafka import KafkaProducer, KafkaConsumer
import time

print("=" * 60)
print("KAFKA + SCHEMA REGISTRY 통합 테스트")
print("=" * 60)

# 1. Schema Registry 연결 테스트
print("\n1️⃣  Schema Registry 연결 테스트...")
try:
    response = requests.get('http://localhost:8081/subjects')
    subjects = response.json()
    print(f"   ✅ Schema Registry 정상 (subjects: {subjects})")
except Exception as e:
    print(f"   ❌ Schema Registry 연결 실패: {e}")


# 2. Kafka 연결 테스트
print("\n2️⃣  Kafka 연결 테스트...")
try:
    producer = KafkaProducer(bootstrap_servers=['localhost:9092'])
    producer.close()
    print(f"   ✅ Kafka Producer 연결 성공")
except Exception as e:
    print(f"   ❌ Kafka 연결 실패: {e}")


# 3. 테스트 메시지 발행
print("\n3️⃣  테스트 메시지 발행...")
try:
    producer = KafkaProducer(
        bootstrap_servers=['localhost:9092'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    test_event = {
        'id': 'test_001',
        'click': 1,
        'hour': 140102,
        'C1': 1005,
        'device_type': 1,
        'timestamp': int(time.time() * 1000)
    }

    future = producer.send('ad_events_raw', value=test_event)
    record_metadata = future.get(timeout=10)

    print(f"   ✅ 메시지 발행 성공")
    print(f"      Topic: {record_metadata.topic}")
    print(f"      Partition: {record_metadata.partition}")
    print(f"      Offset: {record_metadata.offset}")

    producer.close()
except Exception as e:
    print(f"   ❌ 메시지 발행 실패: {e}")


# 4. 메시지 수신 확인
print("\n4️⃣  메시지 수신 확인...")
try:
    consumer = KafkaConsumer(
        'ad_events_raw',
        bootstrap_servers=['localhost:9092'],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        auto_offset_reset='earliest',
        consumer_timeout_ms=5000
    )

    messages_received = 0
    for message in consumer:
        print(f"   ✅ 메시지 수신: {message.value}")
        messages_received += 1
        if messages_received >= 1:
            break

    consumer.close()
except Exception as e:
    print(f"   ❌ 메시지 수신 실패: {e}")

print("\n" + "=" * 60)
print("✅ 모든 테스트 완료!")
print("=" * 60)
