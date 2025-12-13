"""
Kafka DLQ (Dead Letter Queue) Consumer - 실패한 메시지를 저장하고 모니터링하는 Consumer

실행:
    python -m kafka.consumers.dlq_consumer.main
    python kafka/consumers/dlq_consumer/main.py
"""

import sys
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from confluent_kafka import Consumer
from confluent_kafka.error import KafkaError

from .config import DLQConsumerConfig
from utils.logger import setup_logging, get_logger

# 로깅 설정
setup_logging(log_level=DLQConsumerConfig.LOG_LEVEL)
logger = get_logger(__name__)


class DLQConsumer:
    """실패한 메시지를 저장하고 모니터링하는 Consumer"""

    def __init__(self):
        """Consumer 초기화"""
        self.config = DLQConsumerConfig
        self.consumer = None
        self.db_connection = None

        # 통계
        self.stats = {
            'total': 0,
            'stored': 0,
            'errors': 0,
        }

        self._create_consumer()
        self._init_database()

    def _create_consumer(self):
        """Kafka Consumer 생성"""
        try:
            logger.info(f"Creating Kafka DLQ Consumer: {self.config.BOOTSTRAP_SERVERS}")
            consumer_config = self.config.get_consumer_config()
            self.consumer = Consumer(consumer_config)
            self.consumer.subscribe([self.config.TOPIC])
            logger.info(f"✅ Kafka DLQ Consumer 생성 - {self.config.TOPIC} 구독 중")
        except Exception as e:
            logger.error(f"Failed to create Kafka Consumer: {e}")
            raise

    def _init_database(self):
        """SQLite 데이터베이스 초기화"""
        try:
            # 디렉토리 생성
            db_dir = Path(self.config.DLQ_DB_PATH).parent
            db_dir.mkdir(parents=True, exist_ok=True)

            # 데이터베이스 연결
            self.db_connection = sqlite3.connect(self.config.DLQ_DB_PATH)
            cursor = self.db_connection.cursor()

            # 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS dlq_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message_id TEXT,
                    topic TEXT,
                    partition INTEGER,
                    offset INTEGER,
                    message_content TEXT,
                    error_reason TEXT,
                    received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed_at TIMESTAMP
                )
            ''')

            # 인덱스 생성
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_message_id ON dlq_messages(message_id)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_received_at ON dlq_messages(received_at)
            ''')

            self.db_connection.commit()
            logger.info(f"✅ 데이터베이스 초기화 완료: {self.config.DLQ_DB_PATH}")

        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise

    def _store_message(self, msg: Any, message_content: Dict[str, Any], error_reason: str = ""):
        """메시지를 데이터베이스에 저장"""
        try:
            cursor = self.db_connection.cursor()

            message_id = message_content.get('original_message', {}).get('id', 'unknown')

            cursor.execute('''
                INSERT INTO dlq_messages
                (message_id, topic, partition, offset, message_content, error_reason, processed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                message_id,
                msg.topic(),
                msg.partition(),
                msg.offset(),
                json.dumps(message_content),
                error_reason or message_content.get('reason', ''),
                datetime.now().isoformat()
            ))

            self.db_connection.commit()
            self.stats['stored'] += 1

            logger.info(f"✅ DLQ 데이터베이스에 메시지 저장 - ID: {message_id}")

            # 로그 파일도 함께 저장
            self._write_log_file(message_id, message_content, error_reason)

        except Exception as e:
            logger.error(f"Failed to store message in database: {e}")
            self.stats['errors'] += 1

    def _write_log_file(self, message_id: str, message_content: Dict[str, Any], error_reason: str):
        """DLQ 메시지를 로그 파일에 저장"""
        try:
            log_dir = Path(self.config.DLQ_LOG_DIR)
            log_dir.mkdir(parents=True, exist_ok=True)

            # 날짜별 로그 파일
            log_file = log_dir / f"dlq_{datetime.now().strftime('%Y%m%d')}.jsonl"

            log_entry = {
                'message_id': message_id,
                'timestamp': datetime.now().isoformat(),
                'content': message_content,
                'error_reason': error_reason or message_content.get('reason', ''),
            }

            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry) + '\n')

            logger.debug(f"로그 파일 작성: {log_file}")

        except Exception as e:
            logger.error(f"Failed to write log file: {e}")

    def _process_message(self, msg: Any) -> bool:
        """DLQ 메시지 처리"""
        try:
            # 메시지 역직렬화
            message_value = json.loads(msg.value().decode('utf-8'))
            self.stats['total'] += 1

            message_id = message_value.get('original_message', {}).get('id', 'unknown')
            reason = message_value.get('reason', 'Unknown reason')
            timestamp = message_value.get('sent_to_dlq_at', datetime.now().isoformat())

            logger.warning(f"DLQ 메시지 수신 - ID: {message_id}, 이유: {reason}")

            # 데이터베이스에 저장
            self._store_message(msg, message_value)

            # 알림 전송
            self._send_alert(message_id, reason, timestamp)

            return True

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode DLQ message: {e}")
            self.stats['errors'] += 1
            return False

        except Exception as e:
            logger.error(f"Error processing DLQ message: {e}")
            self.stats['errors'] += 1
            return False

    def _send_alert(self, message_id: str, reason: str, timestamp: str):
        """알림 전송 (이메일, Slack 등으로 확장 가능)"""
        try:
            # 알림 로그
            logger.critical(f"경고: DLQ 메시지 - ID: {message_id}, 이유: {reason}, 시간: {timestamp}")

            # 운영 환경에서 구현할 사항:
            # - 이메일 알림
            # - Slack 메시지 전송
            # - 모니터링 시스템 이벤트 기록
            # - PagerDuty/Opsgenie 인시던트 생성

        except Exception as e:
            logger.error(f"Failed to send alert: {e}")

    def run(self):
        """Consumer 실행"""
        logger.info("=" * 60)
        logger.info("Kafka DLQ Consumer 시작")
        logger.info("=" * 60)
        logger.info(f"Topic: {self.config.TOPIC}")
        logger.info(f"Group ID: {self.config.GROUP_ID}")
        logger.info(f"Database: {self.config.DLQ_DB_PATH}")
        logger.info(f"Log Directory: {self.config.DLQ_LOG_DIR}")
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

                # DLQ 메시지 처리
                self._process_message(msg)

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
        logger.info("DLQ Consumer 통계")
        logger.info("=" * 60)
        logger.info(f"수신 총합: {self.stats['total']}")
        logger.info(f"DB에 저장: {self.stats['stored']}")
        logger.info(f"오류: {self.stats['errors']}")
        logger.info("=" * 60)

    def close(self):
        """Consumer와 Database 종료"""
        if self.consumer:
            self.consumer.close()
        if self.db_connection:
            self.db_connection.close()
            logger.info("데이터베이스 연결 종료됨")


def main():
    """메인 함수"""
    # 설정 검증
    try:
        DLQConsumerConfig.validate()
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return 1

    consumer = None
    try:
        consumer = DLQConsumer()
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
