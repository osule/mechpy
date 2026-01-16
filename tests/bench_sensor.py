"""Benchmark tests comparing Rust vs Python implementations"""

import pyarrow as pa
import pytest
from mechpy import sensor


def rolling_mean_python(data, window):
    """Pure Python implementation for comparison"""
    values = data.to_pylist()
    result = []
    
    for i in range(len(values)):
        if i + 1 < window:
            result.append(None)
        else:
            window_vals = [v for v in values[i + 1 - window:i + 1] if v is not None]
            result.append(sum(window_vals) / len(window_vals) if window_vals else None)
    
    return pa.array(result)


@pytest.fixture
def small_data():
    return pa.array([float(i) for i in range(100)])


@pytest.fixture
def large_data():
    return pa.array([float(i) for i in range(10000)])


def test_bench_rust_small(benchmark, small_data):
    """Benchmark Rust implementation with small dataset"""
    benchmark(sensor.rolling_mean, small_data, 10)


def test_bench_python_small(benchmark, small_data):
    """Benchmark Python implementation with small dataset"""
    benchmark(rolling_mean_python, small_data, 10)


def test_bench_rust_large(benchmark, large_data):
    """Benchmark Rust implementation with large dataset"""
    benchmark(sensor.rolling_mean, large_data, 50)


def test_bench_python_large(benchmark, large_data):
    """Benchmark Python implementation with large dataset"""
    benchmark(rolling_mean_python, large_data, 50)
