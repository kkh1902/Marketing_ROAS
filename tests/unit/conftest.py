"""
pytest 단위 테스트 conftest.py
단위 테스트에서 사용할 fixtures
"""

import pytest
import tempfile
import os
from pathlib import Path


@pytest.fixture
def temp_dir():
    """임시 디렉토리"""
    temp_path = tempfile.mkdtemp()
    yield temp_path
    # cleanup
    import shutil
    if os.path.exists(temp_path):
        shutil.rmtree(temp_path)


@pytest.fixture
def temp_file():
    """임시 파일"""
    fd, temp_path = tempfile.mkstemp()
    os.close(fd)
    yield temp_path
    if os.path.exists(temp_path):
        os.unlink(temp_path)
