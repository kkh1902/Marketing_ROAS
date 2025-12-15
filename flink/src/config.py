# -*- coding: utf-8 -*-
"""
Flink Configuration
"""

class FlinkConfig:
    """Flink Configuration"""

    # Kafka Configuration
    BOOTSTRAP_SERVERS = 'broker:29092'
    TOPIC = 'ad_events_raw'
    GROUP_ID = 'flink-consumer-group'

    # Flink Settings
    PARALLELISM = 1
    CHECKPOINT_INTERVAL = 60000  # 60 seconds

    @staticmethod
    def validate():
        """Validate all required configurations"""
        required_configs = [
            FlinkConfig.BOOTSTRAP_SERVERS,
            FlinkConfig.TOPIC,
            FlinkConfig.GROUP_ID,
        ]

        for config in required_configs:
            if not config:
                raise ValueError(f"Missing required configuration")

        return True
