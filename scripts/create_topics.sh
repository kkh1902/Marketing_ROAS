#!/bin/bash

set -e  # 에러 발생 시 즉시 중단

# Topic 생성 함수
create_topic() {
    TOPIC_NAME=$1
    PARTITIONS=$2
    REPLICATION=$3

    echo "Creating topic: $TOPIC_NAME (partitions: $PARTITIONS, replication: $REPLICATION)"

    docker-compose exec broker kafka-topics \
        --create \
        --bootstrap-server broker:29092 \
        --topic $TOPIC_NAME \
        --partitions $PARTITIONS \
        --replication-factor $REPLICATION \
        --config retention.ms=86400000 \
        --config compression.type=snappy \
        --config min.insync.replicas=1 \
        --config cleanup.policy=delete \
        2>&1 || echo "⚠️  Topic $TOPIC_NAME already exists"
}

echo "================================"
echo "Creating Kafka Topics..."
echo "================================"

# ============================================================
# 운영용 토픽 (Production)
# ============================================================

# 1. 메인 토픽: 광고 이벤트 (실시간 처리)
create_topic "ad_events_raw" 3 1

# 2. DLQ: 처리 실패한 메시지
create_topic "ad_events_dlq" 1 1

# 3. 리트라이: 재처리 대기
create_topic "ad_events_retry" 1 1

# ============================================================
# 테스트용 토픽 (Testing)
# ============================================================

# 4. 테스트: 광고 이벤트 (단위/통합/E2E 테스트)
create_topic "test_ad_events_raw" 1 1

# 5. 테스트: DLQ (테스트용 실패 메시지)
create_topic "test_ad_events_dlq" 1 1

# 6. 테스트: 리트라이 (테스트용 재처리)
create_topic "test_ad_events_retry" 1 1

echo ""
echo "✅ Topic creation completed"


echo "================================"
echo "topic 추가 되었는지 확인"
echo "================================"
docker-compose exec broker kafka-topics \
    --list \
    --bootstrap-server broker:29092

# Topic 상세 정보
docker-compose exec broker kafka-topics \
    --describe \
    --bootstrap-server broker:29092 \
    --topic ad_events_raw
