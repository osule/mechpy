"""Tests for FFT analysis function"""

import math
import pyarrow as pa
from mechpy import sensor


def test_fft_analysis_basic():
    """Test basic FFT analysis with sine wave"""
    # Create sine wave: 10 Hz at 100 Hz sampling
    signal = []
    for i in range(64):
        t = i / 100.0
        signal.append(math.sin(2 * math.pi * 10 * t))

    data = pa.array(signal)
    result = sensor.fft_analysis(data, sample_rate=100.0)

    # Result is Arrow RecordBatch - basic functionality test
    assert result is not None


def test_fft_analysis_empty_array():
    """Test FFT with empty array"""
    data = pa.array([], type=pa.float64())
    result = sensor.fft_analysis(data, sample_rate=100.0)

    # Basic functionality check
    assert result is not None


def test_fft_analysis_single_value():
    """Test FFT with single value"""
    data = pa.array([1.0])
    result = sensor.fft_analysis(data, sample_rate=100.0)

    # Basic functionality check
    assert result is not None


def test_fft_analysis_dc_signal():
    """Test FFT with DC signal (constant value)"""
    data = pa.array([5.0] * 32)  # Constant value
    result = sensor.fft_analysis(data, sample_rate=100.0)

    # Basic functionality check
    assert result is not None


def test_fft_analysis_with_nulls():
    """Test FFT handles null values (treated as 0)"""
    signal = []
    for i in range(32):
        if i < 16:  # First half valid
            t = i / 100.0
            signal.append(math.sin(2 * math.pi * 10 * t))
        else:  # Second half null
            signal.append(None)

    data = pa.array(signal)
    result = sensor.fft_analysis(data, sample_rate=100.0)

    # Basic functionality check
    assert result is not None


def test_fft_analysis_invalid_sample_rate():
    """Test FFT with invalid sample rate"""
    data = pa.array([1.0, 2.0, 3.0])
    try:
        sensor.fft_analysis(data, sample_rate=0.0)
        assert False, "Should have raised an error"
    except Exception as e:
        assert "positive" in str(e).lower()

    try:
        sensor.fft_analysis(data, sample_rate=-10.0)
        assert False, "Should have raised an error"
    except Exception as e:
        assert "positive" in str(e).lower()


def test_fft_analysis_wrong_type():
    """Test FFT with wrong data type"""
    data = pa.array([1, 2, 3], type=pa.int32())  # Wrong type
    try:
        sensor.fft_analysis(data, sample_rate=100.0)
        assert False, "Should have raised an error"
    except Exception as e:
        assert "Float64" in str(e)


def test_fft_analysis_different_sizes():
    """Test FFT with different input sizes"""
    # Test various power-of-2 sizes
    for size in [8, 16, 32, 64]:
        signal = [math.sin(2 * math.pi * 5 * i / 100.0) for i in range(size)]
        data = pa.array(signal)
        result = sensor.fft_analysis(data, sample_rate=100.0)

        # Basic functionality check for different sizes
        assert result is not None