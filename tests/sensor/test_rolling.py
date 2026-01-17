"""Tests for rolling window functions (rolling_mean, rolling_rms)"""

import pyarrow as pa
from mechpy import sensor


def test_rolling_mean_basic():
    """Test basic rolling mean calculation"""
    data = pa.array([1.0, 2.0, 3.0, 4.0, 5.0])
    result = sensor.rolling_mean(data, window=3)
    expected = [None, None, 2.0, 3.0, 4.0]
    assert result.to_pylist() == expected


def test_rolling_mean_window_size_one():
    """Window size 1 should return original data"""
    data = pa.array([1.0, 2.0, 3.0])
    result = sensor.rolling_mean(data, window=1)
    assert result.to_pylist() == [1.0, 2.0, 3.0]


def test_rolling_mean_window_larger_than_data():
    """Window larger than data should return all None"""
    data = pa.array([1.0, 2.0, 3.0])
    result = sensor.rolling_mean(data, window=5)
    assert result.to_pylist() == [None, None, None]


def test_rolling_mean_empty_array():
    """Empty array should return empty array"""
    data = pa.array([], type=pa.float64())
    result = sensor.rolling_mean(data, window=3)
    assert len(result) == 0


def test_rolling_mean_with_nulls():
    """Handle null values in input by skipping them"""
    data = pa.array([1.0, None, 3.0, 4.0, 5.0])
    result = sensor.rolling_mean(data, window=3)
    expected = [None, None, 2.0, 3.5, 4.0]  # Skip nulls in calculation
    assert result.to_pylist() == expected


def test_rolling_mean_all_nulls():
    """All null values should return all nulls"""
    data = pa.array([None, None, None, None], type=pa.float64())
    result = sensor.rolling_mean(data, window=2)
    assert all(v is None for v in result.to_pylist())


def test_rolling_mean_large_window():
    """Test with realistic sensor data size"""
    data = pa.array([float(i) for i in range(100)])
    result = sensor.rolling_mean(data, window=10)

    # Check length
    assert len(result) == 100

    # Check first values are None
    assert all(v is None for v in result.to_pylist()[:9])

    # Check 10th value (index 9) is mean of first 10 values
    assert result.to_pylist()[9] == 4.5  # mean(0..9)

    # Check last value
    assert result.to_pylist()[99] == 94.5  # mean(90..99)


def test_rolling_rms_basic():
    """Test basic rolling RMS calculation"""
    data = pa.array([1.0, 2.0, 3.0, 4.0, 5.0])
    result = sensor.rolling_rms(data, window=3)

    # RMS = sqrt(sum(x^2)/n) for each window
    # Window [1,2,3]: sqrt((1+4+9)/3) ≈ 2.160
    # Window [2,3,4]: sqrt((4+9+16)/3) ≈ 3.109
    # Window [3,4,5]: sqrt((9+16+25)/3) ≈ 4.083
    expected = [None, None, 2.160246899469287, 3.109126351029605, 4.08248290463863]
    actual = result.to_pylist()

    # Use approximate comparison due to floating point precision
    for i, (exp, act) in enumerate(zip(expected, actual)):
        if exp is None:
            assert act is None, f"Expected None at position {i}, got {act}"
        else:
            assert abs(exp - act) < 1e-10, f"Expected {exp} at position {i}, got {act}"


def test_rolling_rms_window_size_one():
    """Window size 1 should return absolute values (RMS of single value)"""
    data = pa.array([1.0, 2.0, 3.0])
    result = sensor.rolling_rms(data, window=1)
    assert result.to_pylist() == [1.0, 2.0, 3.0]


def test_rolling_rms_window_larger_than_data():
    """Window larger than data should return all None"""
    data = pa.array([1.0, 2.0, 3.0])
    result = sensor.rolling_rms(data, window=5)
    assert result.to_pylist() == [None, None, None]


def test_rolling_rms_empty_array():
    """Empty array should return empty array"""
    data = pa.array([], type=pa.float64())
    result = sensor.rolling_rms(data, window=3)
    assert len(result) == 0


def test_rolling_rms_with_nulls():
    """Handle null values in input by skipping them"""
    data = pa.array([1.0, None, 3.0, 4.0, 5.0])
    result = sensor.rolling_rms(data, window=3)

    # Window [1,None,3]: only [1,3] valid, sum_squares=1+9=10, RMS=sqrt(10/2)≈2.236
    # Window [None,3,4]: only [3,4] valid, sum_squares=9+16=25, RMS=sqrt(25/2)≈3.536
    # Window [3,4,5]: all valid, sum_squares=9+16+25=50, RMS=sqrt(50/3)≈4.083
    expected = [None, None, 2.236067977, 3.535533906, 4.082482905]
    actual = result.to_pylist()

    for i, (exp, act) in enumerate(zip(expected, actual)):
        if exp is None:
            assert act is None, f"Expected None at position {i}, got {act}"
        else:
            assert abs(exp - act) < 1e-6, f"Expected {exp} at position {i}, got {act}"


def test_rolling_rms_all_nulls():
    """All null values should return all nulls"""
    data = pa.array([None, None, None, None], type=pa.float64())
    result = sensor.rolling_rms(data, window=2)
    assert all(v is None for v in result.to_pylist())


def test_rolling_rms_constant_values():
    """Test RMS with constant values"""
    data = pa.array([2.0, 2.0, 2.0, 2.0])
    result = sensor.rolling_rms(data, window=2)

    # RMS of [2,2] = sqrt((4+4)/2) = sqrt(4) = 2.0
    expected = [None, 2.0, 2.0, 2.0]
    actual = result.to_pylist()

    for exp, act in zip(expected, actual):
        if exp is None:
            assert act is None
        else:
            assert abs(exp - act) < 1e-10


def test_rolling_rms_large_window():
    """Test with realistic sensor data size"""
    import math
    data = pa.array([float(i) for i in range(10)])  # [0,1,2,3,4,5,6,7,8,9]
    result = sensor.rolling_rms(data, window=5)

    # Check length
    assert len(result) == 10

    # Check first values are None
    assert all(v is None for v in result.to_pylist()[:4])

    # Check 5th value (index 4) is RMS of first 5 values [0,1,2,3,4]
    # sum_squares = 0+1+4+9+16=30, RMS=sqrt(30/5)=sqrt(6)≈2.449
    expected_rms = math.sqrt(30.0 / 5.0)
    assert abs(result.to_pylist()[4] - expected_rms) < 1e-10

    # Check last value (index 9) is RMS of last 5 values [5,6,7,8,9]
    # sum_squares = 25+36+49+64+81=255, RMS=sqrt(255/5)=sqrt(51)≈7.141
    expected_last = math.sqrt(255.0 / 5.0)
    assert abs(result.to_pylist()[9] - expected_last) < 1e-10