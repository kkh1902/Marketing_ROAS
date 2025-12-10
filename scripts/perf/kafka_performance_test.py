#!/usr/bin/env python3

import json
import time
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import statistics

print("=" * 70)
print("KAFKA 성능 테스트")
print("=" * 70)

# 테스트 메시지 생성
test_messages = []
for i in range(10000):
    test_messages.append({
        'id': f'test_{i:06d}',
        'click': i % 100 < 16,  # 16% CTR
        'hour': 140102,
        'device_type': i % 10,
        'timestamp': int(time.time() * 1000)
    })

# 1️⃣  Producer 성능 테스트
print("\n1️⃣  Producer 성능 테스트 (10,000 messages)...")

producer = KafkaProducer(
    bootstrap_servers=['localhost:9092'],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    acks='all',
    retries=3,
    batch_size=16384,
    linger_ms=10
)

latencies = []
start_time = time.time()

for i, msg in enumerate(test_messages):
    try:
        future = producer.send('ad_events_raw', value=msg)
        record_metadata = future.get(timeout=10)

        latency = (time.time() - start_time) * 1000 / (i + 1)
        latencies.append(latency)

        if (i + 1) % 1000 == 0:
            print(f"   📤 {i + 1:,} messages sent")
    except KafkaError as e:
        print(f"   ❌ Error: {e}")

producer.flush()
producer.close()

elapsed = time.time() - start_time
throughput = len(test_messages) / elapsed

print(f"\n   결과:")
print(f"   - 총 메시지: {len(test_messages):,}")
print(f"   - 소요 시간: {elapsed:.2f}초")
print(f"   - 처리량: {throughput:.0f} msg/sec")
print(f"   - 평균 레이턴시: {statistics.mean(latencies):.2f}ms")
print(f"   - 최대 레이턴시: {max(latencies):.2f}ms")
print(f"   - P99 레이턴시: {sorted(latencies)[int(len(latencies)*0.99)]:.2f}ms")

# 2️⃣  Consumer 성능 테스트
print("\n2️⃣  Consumer 성능 테스트...")

consumer = KafkaConsumer(
    'ad_events_raw',
    bootstrap_servers=['localhost:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    auto_offset_reset='earliest',
    consumer_timeout_ms=30000,
    fetch_max_bytes=52428800,
    max_poll_records=500
)

messages_received = 0
start_time = time.time()

for message in consumer:
    messages_received += 1
    if messages_received % 1000 == 0:
        print(f"   📥 {messages_received:,} messages received")

elapsed_consume = time.time() - start_time
throughput_consume = messages_received / elapsed_consume

print(f"\n   결과:")
print(f"   - 수신 메시지: {messages_received:,}")
print(f"   - 소요 시간: {elapsed_consume:.2f}초")
print(f"   - 처리량: {throughput_consume:.0f} msg/sec")

consumer.close()

# 3️⃣  최종 결과
print("\n" + "=" * 70)
print("성능 요약")
print("=" * 70)
print(f"Producer 처리량:  {throughput:>10.0f} msg/sec")
print(f"Consumer 처리량:  {throughput_consume:>10.0f} msg/sec")
print(f"P99 레이턴시:     {sorted(latencies)[int(len(latencies)*0.99)]:>10.2f} ms")
print(f"목표 달성:        {'✅' if throughput > 50000 else '⚠️'}")
print("=" * 70)