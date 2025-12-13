"""
Kafka Retry Consumer - 실패한 메시지를 지수 백오프로 재시도하는 Consumer

실행:
    python -m kafka.consumers.retry_consumer.main
    python kafka/consumers/retry_consumer/main.py
"""

import sys
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any

from confluent_kafka import Consumer, Producer
from confluent_kafka.error import KafkaError

from .config import RetryConsumerConfig
from utils.logger import setup_logging, get_logger

# 로깅 설정
setup_logging(log_level=RetryConsumerConfig.LOG_LEVEL)
logger = get_logger(__name__)


class RetryConsumer:
    """실패한 메시지를 재시도하는 Consumer"""

    def __init__(self):
        """Consumer/Producer 초기화"""
        self.config = RetryConsumerConfig
        self.consumer = None
        self.producer = None

        # 통계
        self.stats = {
            'total': 0,
            'processed': 0,
            'retried': 0,
            'dlq_sent': 0,
            'errors': 0,
        }

        self._create_consumer()
        self._create_producer()

    def _create_consumer(self):
        """Kafka Consumer 생성"""
        try:
            logger.info(f"Creating Kafka Retry Consumer: {self.config.BOOTSTRAP_SERVERS}")
            consumer_config = self.config.get_consumer_config()
            self.consumer = Consumer(consumer_config)
            self.consumer.subscribe([self.config.TOPIC])
            logger.info(f"✅ Kafka Retry Consumer 생성 - {self.config.TOPIC} 구독 중")
        except Exception as e:
            logger.error(f"Failed to create Kafka Consumer: {e}")
            raise

    def _create_producer(self):
        """Kafka Producer 생성 (DLQ로 보내기 위함)"""
        try:
            logger.info("Creating Kafka Producer for DLQ")
            producer_config = {
                'bootstrap.servers': self.config.BOOTSTRAP_SERVERS,
                'client.id': 'retry_consumer_producer',
                'acks': 'all',
                'enable.idempotence': True,
            }
            self.producer = Producer(producer_config)
            logger.info("✅ Kafka Producer DLQ용 생성 완료")
        except Exception as e:
            logger.error(f"Failed to create Kafka Producer: {e}")
            raise

    def _delivery_report(self, err, msg):
        """Producer delivery report 콜백"""
        if err is not None:
            logger.error(f"DLQ message delivery failed: {err}")
            self.stats['errors'] += 1
        else:
            logger.info(f"Message sent to DLQ topic: {msg.topic()}")
            self.stats['dlq_sent'] += 1

    def _send_to_dlq(self, message: Dict[str, Any], reason: str):
        """메시지를 DLQ로 전송"""
        try:
            dlq_message = {
                'original_message': message,
                'sent_to_dlq_at': datetime.now().isoformat(),
                'reason': reason,
            }

            self.producer.produce(
                topic=self.config.DLQ_TOPIC,
                value=json.dumps(dlq_message),
                callback=self._delivery_report
            )
            self.producer.poll(0)

        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}")
            self.stats['errors'] += 1

    def _retry_message(self, message: Dict[str, Any], retry_count: int) -> bool:
        """메시지 재시도 (지수 백오프 적용)"""
        try:
            # 재시도 횟수 증가
            retry_count += 1

            if retry_count >= self.config.MAX_RETRIES:
                logger.warning(f"최대 재시도 횟수({self.config.MAX_RETRIES})를 초과했습니다. DLQ로 전송합니다.")
                self._send_to_dlq(message, f"Max retries exceeded ({retry_count})")
                self.stats['dlq_sent'] += 1
                return False

            # 지수 백오프 (exponential backoff)
            backoff_ms = min(
                self.config.RETRY_BACKOFF_MS * (2 ** (retry_count - 1)),
                self.config.RETRY_BACKOFF_MAX_MS
            )

            logger.info(f"메시지 재시도 (시도 {retry_count}/{self.config.MAX_RETRIES}), 대기: {backoff_ms}ms")
            time.sleep(backoff_ms / 1000)

            # 메시지 처리 시도
            if self._process_message(message, retry_count):
                self.stats['retried'] += 1
                return True
            else:
                # 재귀적으로 다시 시도
                return self._retry_message(message, retry_count)

        except Exception as e:
            logger.error(f"Retry failed: {e}")
            self._send_to_dlq(message, f"Retry error: {str(e)}")
            self.stats['errors'] += 1
            return False

    def _process_message(self, message: Dict[str, Any], retry_count: int = 0) -> bool:
        """메시지 처리"""
        try:
            # 여기서 실제 비즈니스 로직을 수행
            # 예: DB 저장, 외부 API 호출 등
            logger.info(f"메시지 처리 중: {message.get('id', 'unknown')}")

            # 시뮬레이션: 메시지 처리
            # 실제로는 여기에 비즈니스 로직이 들어감

            self.stats['processed'] += 1
            return True

        except Exception as e:
            logger.error(f"Message processing failed: {e}")
            if retry_count < self.config.MAX_RETRIES:
                # 재시도
                return self._retry_message(message, retry_count)
            else:
                # DLQ로 전송
                self._send_to_dlq(message, f"Processing error: {str(e)}")
                return False

    def run(self):
        """Consumer 실행"""
        logger.info("=" * 60)
        logger.info("Kafka Retry Consumer 시작")
        logger.info("=" * 60)
        logger.info(f"Topic: {self.config.TOPIC}")
        logger.info(f"Group ID: {self.config.GROUP_ID}")
        logger.info(f"최대 재시도 횟수: {self.config.MAX_RETRIES}")
        logger.info(f"DLQ Topic: {self.config.DLQ_TOPIC}")
        logger.info("=" * 60)

        try:
            while True:
                msg = self.consumer.poll(timeout=1.0)

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug("파티션 끝에 도달했습니다")
                    else:
                        logger.error(f"Consumer error: {msg.error()}")
                        self.stats['errors'] += 1
                    continue

                try:
                    # 메시지 역직렬화
                    message_value = json.loads(msg.value().decode('utf-8'))
                    self.stats['total'] += 1

                    logger.info(f"메시지 수신: {message_value.get('id', 'unknown')}")

                    # 메시지 처리
                    self._process_message(message_value)

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                    self.stats['errors'] += 1
                    self._send_to_dlq({'raw_value': msg.value().decode('utf-8', errors='ignore')}, f"JSON decode error: {str(e)}")

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    self.stats['errors'] += 1

        except KeyboardInterrupt:
            logger.info("Consumer 중단됨")
        except Exception as e:
            logger.error(f"Consumer error: {e}", exc_info=True)
        finally:
            self._print_stats()
            self.close()

    def _print_stats(self):
        """통계 출력"""
        logger.info("=" * 60)
        logger.info("Retry Consumer 통계")
        logger.info("=" * 60)
        logger.info(f"Total: {self.stats['total']}")
        logger.info(f"Processed: {self.stats['processed']}")
        logger.info(f"Retried: {self.stats['retried']}")
        logger.info(f"Sent to DLQ: {self.stats['dlq_sent']}")
        logger.info(f"Errors: {self.stats['errors']}")
        logger.info("=" * 60)

    def close(self):
        """Consumer/Producer 종료"""
        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.flush()


def main():
    """메인 함수"""
    # 설정 검증
    try:
        RetryConsumerConfig.validate()
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return 1

    consumer = None
    try:
        consumer = RetryConsumer()
        consumer.run()
        return 0

    except KeyboardInterrupt:
        logger.info("Consumer 중단됨")
        return 130

    except Exception as e:
        logger.error(f"Consumer error: {e}", exc_info=True)
        return 1

    finally:
        if consumer:
            consumer.close()


if __name__ == "__main__":
    sys.exit(main())
