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


def test_fft_analysis_basic():
    """Test basic FFT analysis with sine wave"""
    import math
    # Create sine wave: 10 Hz at 100 Hz sampling
    signal = []
    for i in range(64):
        t = i / 100.0
        signal.append(math.sin(2 * math.pi * 10 * t))

    data = pa.array(signal)
    result = sensor.fft_analysis(data, sample_rate=100.0)

    # Check result structure
    assert 'frequencies' in result
    assert 'magnitude' in result
    assert 'phase' in result

    # Check output dimensions (N/2 + 1 for real FFT)
    assert len(result['frequencies']) == 33  # 64/2 + 1
    assert len(result['magnitude']) == 33
    assert len(result['phase']) == 33

    # Check frequency range (0 to Nyquist frequency)
    freqs = result['frequencies'].to_pylist()
    assert freqs[0] == 0.0  # DC component
    assert abs(freqs[-1] - 50.0) < 1e-10  # Nyquist frequency (100/2)

    # Check that peak is near 10 Hz
    mags = result['magnitude'].to_pylist()
    max_idx = mags.index(max(mags))
    peak_freq = freqs[max_idx]
    assert abs(peak_freq - 10.0) < 2.0  # Allow some tolerance due to discretization


def test_fft_analysis_empty_array():
    """Test FFT with empty array"""
    data = pa.array([], type=pa.float64())
    result = sensor.fft_analysis(data, sample_rate=100.0)

    assert len(result['frequencies']) == 0
    assert len(result['magnitude']) == 0
    assert len(result['phase']) == 0


def test_fft_analysis_single_value():
    """Test FFT with single value"""
    data = pa.array([1.0])
    result = sensor.fft_analysis(data, sample_rate=100.0)

    # Single value FFT should have 1 frequency bin
    assert len(result['frequencies']) == 1
    assert len(result['magnitude']) == 1
    assert len(result['phase']) == 1

    # DC component should be the value itself
    assert abs(result['magnitude'].to_pylist()[0] - 1.0) < 1e-10


def test_fft_analysis_dc_signal():
    """Test FFT with DC signal (constant value)"""
    data = pa.array([5.0] * 32)  # Constant value
    result = sensor.fft_analysis(data, sample_rate=100.0)

    mags = result['magnitude'].to_pylist()

    # DC component should be large, others should be near zero
    assert mags[0] > 10.0  # DC component
    # Other components should be much smaller
    for mag in mags[1:]:
        assert mag < 1.0


def test_fft_analysis_with_nulls():
    """Test FFT handles null values (treated as 0)"""
    import math
    signal = []
    for i in range(32):
        if i < 16:  # First half valid
            t = i / 100.0
            signal.append(math.sin(2 * math.pi * 10 * t))
        else:  # Second half null
            signal.append(None)

    data = pa.array(signal)
    result = sensor.fft_analysis(data, sample_rate=100.0)

    # Should still work (nulls treated as 0)
    assert len(result['frequencies']) == 17  # 32/2 + 1
    assert len(result['magnitude']) == 17
    assert len(result['phase']) == 17


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
    import math

    # Test various power-of-2 sizes
    for size in [8, 16, 32, 64]:
        signal = [math.sin(2 * math.pi * 5 * i / 100.0) for i in range(size)]
        data = pa.array(signal)
        result = sensor.fft_analysis(data, sample_rate=100.0)

        expected_length = size // 2 + 1
        assert len(result['frequencies']) == expected_length
        assert len(result['magnitude']) == expected_length
        assert len(result['phase']) == expected_length


def test_rolling_rms_basic():
    """Test basic rolling RMS calculation"""
    data = pa.array([1.0, 2.0, 3.0, 4.0, 5.0])
    result = sensor.rolling_rms(data, window=3)

    # RMS = sqrt(sum(x^2)/n) for each window
    # Window [1,2,3]: sqrt((1+4+9)/3) = sqrt(14/3) ≈ 2.160
    # Window [2,3,4]: sqrt((4+9+16)/3) = sqrt(29/3) ≈ 3.109
    # Window [3,4,5]: sqrt((9+16+25)/3) = sqrt(50/3) ≈ 4.083
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
