"""
pytest 루트 conftest.py
모든 테스트에서 사용할 전역 설정 및 fixtures
프로젝트 루트에 위치해야 pytest.ini와 함께 작동
"""

import sys
import os
import pytest

# 프로젝트 루트 경로 설정 (현재 conftest.py 위치 = 프로젝트 루트)
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# sys.path에 프로젝트 루트를 최우선으로 추가
sys.path.insert(0, PROJECT_ROOT)


def pytest_configure(config):
    """pytest 설정 전 sys.path 초기화 (테스트 수집 전)"""
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)


@pytest.fixture(scope="session")
def project_root():
    """프로젝트 루트 경로"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def test_data_dir():
    """테스트 데이터 디렉토리"""
    test_data_path = os.path.join(PROJECT_ROOT, 'tests', 'fixtures', 'data')
    os.makedirs(test_data_path, exist_ok=True)
    return test_data_path


@pytest.fixture(autouse=True)
def reset_modules():
    """각 테스트 전후 모듈 상태 초기화"""
    yield
    # 테스트 후 cleanup (필요시)
    pass
