#!/usr/bin/env python3
"""
Flink 기본 기능 테스트 (JAR 의존성 없음)
간단한 로컬 스트림 처리만 진행
"""

from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.functions import MapFunction
from pyflink.common.typeinfo import Types

print("=" * 60)
print("✅ PyFlink 테스트 시작")
print("=" * 60)

# 환경 생성
env = StreamExecutionEnvironment.get_execution_environment()
env.set_parallelism(1)

print("✅ Flink StreamExecutionEnvironment 생성 성공")

# 간단한 MapFunction
class PrintMapper(MapFunction):
    def map(self, value):
        print(f"Processing: {value}")
        return value

# 간단한 데이터 소스
data = [1, 2, 3, 4, 5]
ds = env.from_collection(data, Types.INT())

print("✅ 데이터소스 생성 성공")

# Map 변환
result = ds.map(PrintMapper(), Types.INT())

print("✅ Map 변환 생성 성공")

# 실행
print("\n" + "=" * 60)
print("Flink Job 실행 중...")
print("=" * 60 + "\n")

try:
    env.execute("Basic Flink Test")
    print("\n" + "=" * 60)
    print("✅ Flink Job 실행 완료!")
    print("=" * 60)
except Exception as e:
    print(f"❌ 에러 발생: {e}")
    import traceback
    traceback.print_exc()
