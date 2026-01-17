"""Benchmark tests for rolling window functions (rolling_mean, rolling_rms)"""

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


def rolling_rms_python(data, window):
    """Pure Python RMS implementation for comparison"""
    import math
    values = data.to_pylist()
    result = []

    for i in range(len(values)):
        if i + 1 < window:
            result.append(None)
        else:
            window_vals = [v for v in values[i + 1 - window:i + 1] if v is not None]
            if window_vals:
                sum_squares = sum(v * v for v in window_vals)
                rms = math.sqrt(sum_squares / len(window_vals))
                result.append(rms)
            else:
                result.append(None)

    return pa.array(result)


@pytest.fixture
def small_data():
    return pa.array([float(i) for i in range(100)])


@pytest.fixture
def large_data():
    return pa.array([float(i) for i in range(10000)])


# Rolling Mean Benchmarks
def test_bench_rolling_mean_rust_small(benchmark, small_data):
    """Benchmark Rust rolling_mean with small dataset"""
    benchmark(sensor.rolling_mean, small_data, 10)


def test_bench_rolling_mean_python_small(benchmark, small_data):
    """Benchmark Python rolling_mean with small dataset"""
    benchmark(rolling_mean_python, small_data, 10)


def test_bench_rolling_mean_rust_large(benchmark, large_data):
    """Benchmark Rust rolling_mean with large dataset"""
    benchmark(sensor.rolling_mean, large_data, 50)


def test_bench_rolling_mean_python_large(benchmark, large_data):
    """Benchmark Python rolling_mean with large dataset"""
    benchmark(rolling_mean_python, large_data, 50)


# Rolling RMS Benchmarks
def test_bench_rolling_rms_rust_small(benchmark, small_data):
    """Benchmark Rust rolling_rms with small dataset"""
    benchmark(sensor.rolling_rms, small_data, 10)


def test_bench_rolling_rms_python_small(benchmark, small_data):
    """Benchmark Python rolling_rms with small dataset"""
    benchmark(rolling_rms_python, small_data, 10)


def test_bench_rolling_rms_rust_large(benchmark, large_data):
    """Benchmark Rust rolling_rms with large dataset"""
    benchmark(sensor.rolling_rms, large_data, 50)


def test_bench_rolling_rms_python_large(benchmark, large_data):
    """Benchmark Python rolling_rms with large dataset"""
    benchmark(rolling_rms_python, large_data, 50)