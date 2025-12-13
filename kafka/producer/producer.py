"""
Kafka Producer - CSV 데이터를 Kafka로 발행

실행:
    python -m kafka.producer.producer
    python -m kafka.producer.producer 100
    python kafka/producer/producer.py 100
"""

import sys
import csv
import argparse
from datetime import datetime
from typing import Optional, Dict, Any

from confluent_kafka import Producer
from confluent_kafka.error import KafkaError

from .config import ProducerConfig
from .data_transformer import AdEventTransformer
from utils.logger import setup_logging, get_logger

# 로깅 설정
setup_logging(log_level=ProducerConfig.LOG_LEVEL)
logger = get_logger(__name__)


class AdEventProducer:
    """CSV 데이터를 Kafka로 발행하는 Producer"""

    def __init__(self):
        """Producer 초기화"""
        self.config = ProducerConfig
        self.transformer = AdEventTransformer()
        self.producer = None

        # 통계
        self.stats = {
            'total': 0,
            'success': 0,
            'validation_failed': 0,
            'send_failed': 0,
        }

        self._create_producer()

    def _create_producer(self):
        """Kafka Producer 생성"""
        try:
            logger.info(f"Creating Kafka Producer: {self.config.BOOTSTRAP_SERVERS}")
            producer_config = self.config.get_producer_config()
            self.producer = Producer(producer_config)
            logger.info("✅ Kafka Producer created")
        except Exception as e:
            logger.error(f"Failed to create Kafka Producer: {e}")
            raise

    def _delivery_report(self, err: Optional[KafkaError], msg: Any):
        """Delivery report 콜백"""
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
            self.stats['send_failed'] += 1
        else:
            self.stats['success'] += 1

    def process_and_send(self, raw_data: Dict[str, Any], row_number: int) -> bool:
        """CSV 행을 처리하고 Kafka로 발행"""
        try:
            # 1. 데이터 변환
            transformed = self.transformer.transform(raw_data)
            if transformed is None:
                self.stats['validation_failed'] += 1
                return False

            # 2. 데이터 검증
            if not self.transformer.validate(transformed):
                self.stats['validation_failed'] += 1
                return False

            # 3. JSON 직렬화
            json_str = self.transformer.to_json(transformed)
            if json_str is None:
                self.stats['validation_failed'] += 1
                return False

            # 4. Kafka로 발행
            self.producer.produce(
                topic=self.config.TOPIC,
                key=str(transformed.get('id')),
                value=json_str,
                callback=self._delivery_report
            )

            self.producer.poll(0)

            if row_number % 100 == 0:
                logger.info(f"Processed {row_number} rows")

            return True

        except Exception as e:
            logger.error(f"Row {row_number}: Error: {e}")
            self.stats['validation_failed'] += 1
            return False

    def run(self, csv_file: str, num_records: Optional[int] = None):
        """CSV 파일을 읽고 Kafka로 발행"""
        logger.info("=" * 60)
        logger.info("Starting Kafka Producer")
        logger.info("=" * 60)
        logger.info(f"CSV File: {csv_file}")
        logger.info(f"Topic: {self.config.TOPIC}")
        logger.info(f"Records: {num_records or 'all'}")
        logger.info("=" * 60)

        start_time = datetime.now()

        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_number, raw_row in enumerate(reader, start=1):
                    if num_records and row_number > num_records:
                        break

                    self.stats['total'] += 1
                    self.process_and_send(raw_row, row_number)

        except FileNotFoundError:
            logger.error(f"CSV file not found: {csv_file}")
            raise
        except Exception as e:
            logger.error(f"Error reading CSV: {e}")
            raise
        finally:
            logger.info("Flushing producer...")
            remaining = self.producer.flush(timeout=30)
            if remaining > 0:
                logger.warning(f"{remaining} message(s) not delivered")

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        self._print_stats(duration)

    def _print_stats(self, duration: float):
        """통계 출력"""
        logger.info("=" * 60)
        logger.info("Producer Statistics")
        logger.info("=" * 60)
        logger.info(f"Total: {self.stats['total']}")
        logger.info(f"Success: {self.stats['success']}")
        logger.info(f"Validation failed: {self.stats['validation_failed']}")
        logger.info(f"Send failed: {self.stats['send_failed']}")
        logger.info(f"Duration: {duration:.2f}s")

        if self.stats['total'] > 0:
            success_rate = (self.stats['success'] / self.stats['total'] * 100)
            logger.info(f"Success rate: {success_rate:.2f}%")
            if duration > 0:
                logger.info(f"Throughput: {self.stats['success'] / duration:.2f} msgs/sec")

        logger.info("=" * 60)

    def close(self):
        """Producer 종료"""
        if self.producer:
            self.producer.flush()


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(
        description='Kafka Producer - CSV to Kafka'
    )
    parser.add_argument(
        'num_records',
        nargs='?',
        type=int,
        help='처리할 최대 행 수 (기본값: 전체)'
    )
    parser.add_argument(
        '--file',
        type=str,
        default=ProducerConfig.CSV_FILE_PATH,
        help='CSV 파일 경로'
    )

    args = parser.parse_args()

    # 설정 검증
    try:
        ProducerConfig.validate()
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        return 1

    producer = None
    try:
        producer = AdEventProducer()
        producer.run(args.file, args.num_records)
        return 0

    except KeyboardInterrupt:
        logger.info("Producer interrupted")
        return 130

    except Exception as e:
        logger.error(f"Producer error: {e}", exc_info=True)
        return 1

    finally:
        if producer:
            producer.close()


if __name__ == "__main__":
    sys.exit(main())
