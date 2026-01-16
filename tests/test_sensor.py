"""Unit tests for sensor.rolling_mean function"""

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


# TODO: Add support for integer types
# def test_rolling_mean_integer_types():
#     """Test rolling mean with integer types"""
#     # Test with int32
#     data_int32 = pa.array([1, 2, 3, 4, 5], type=pa.int32())
#     result_int32 = sensor.rolling_mean(data_int32, window=3)
#     expected = [None, None, 2.0, 3.0, 4.0]
#     assert result_int32.to_pylist() == expected

#     # Test with int64
#     data_int64 = pa.array([10, 20, 30, 40, 50], type=pa.int64())
#     result_int64 = sensor.rolling_mean(data_int64, window=2)
#     expected = [None, 15.0, 25.0, 35.0, 45.0]
#     assert result_int64.to_pylist() == expected


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
