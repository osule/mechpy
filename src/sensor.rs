use pyo3::prelude::*;
use pyo3::types::{PyModule, PyDict};
use pyo3_arrow::PyArray;
use arrow::array::{ArrayRef, Float64Array, Array};
use std::sync::Arc;
use realfft::RealFftPlanner;

use crate::error::MechPyError;

/// Efficient rolling mean for PyArrow arrays
/// Computes moving average over a sliding window with O(n) complexity
///
/// Currently supports Float64 arrays. Support for other numeric types (int32, int64, float32, etc.) coming soon.
///
/// Uses a two-phase algorithm:
/// 1. Fill initial window and compute first mean
/// 2. Slide window: remove old value, add new value, compute mean
///
/// # Arguments
/// * `data` - PyArrow Float64 array
/// * `window` - Window size for rolling mean (must be > 0)
///
/// # Returns
/// PyArrow float64 array with rolling mean values. First (window-1) values are None.
///
/// # Errors
/// * `MechPyError::InvalidInput` - Window size is 0 or invalid
/// * `MechPyError::DataTypeError` - Input is not a Float64 array
/// * `MechPyError::ComputationError` - Numerical computation failed
#[pyfunction]
fn rolling_mean(data: PyArray, window: usize) -> PyResult<PyArray> {
    // Validate window size
    if window == 0 {
        return Err(MechPyError::InvalidInput("Window size must be greater than 0".to_string()).into());
    }

    // Cast to Float64Array - for now only supports Float64, but extensible
    let array = data.array()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| MechPyError::DataTypeError("Array must be Float64 type (other numeric types coming soon)".to_string()))?;

    let len = array.len();
    let window_size = window;

    // Early return for edge cases
    if len == 0 {
        let empty_array: ArrayRef = Arc::new(Float64Array::new_null(0));
        return Ok(PyArray::from_array_ref(empty_array));
    }

    // Prepare result builder with capacity
    let mut builder = arrow::array::Float64Builder::with_capacity(len);

    // Running sum and count for sliding window (O(n) algorithm)
    let mut sum = 0.0;
    let mut count = 0;

    // Phase 1: Append nulls for positions 0 to window_size-2 (not enough data for full window)
    for _ in 0..(window_size - 1).min(len) {
        builder.append_null();
    }

    // Phase 2: Fill initial window
    for i in 0..window_size.min(len) {
        if !array.is_null(i) {
            sum += array.value(i);
            count += 1;
        }
    }

    // Compute mean for the first complete window (position window_size - 1)
    if window_size <= len {
        if count > 0 {
            let mean = sum / count as f64;
            if !mean.is_finite() {
                return Err(MechPyError::ComputationError(
                    format!("Non-finite mean computed at position {}: {}", window_size - 1, mean)
                ).into());
            }
            builder.append_value(mean);
        } else {
            builder.append_null();
        }
    }

    // Phase 3: Slide the window and compute rolling means
    for i in window_size..len {
        // Remove old value leaving the window
        let old_idx = i - window_size;
        if !array.is_null(old_idx) {
            sum -= array.value(old_idx);
            count -= 1;
        }

        // Add new value entering the window
        if !array.is_null(i) {
            sum += array.value(i);
            count += 1;
        }

        // Compute and store mean for current window
        if count > 0 {
            let mean = sum / count as f64;
            if !mean.is_finite() {
                return Err(MechPyError::ComputationError(
                    format!("Non-finite mean computed at position {}: {}", i, mean)
                ).into());
            }
            builder.append_value(mean);
        } else {
            builder.append_null();
        }
    }

    let result_array: ArrayRef = Arc::new(builder.finish());
    Ok(PyArray::from_array_ref(result_array))
}

/// Efficient rolling RMS for PyArrow arrays
/// Computes root mean square over a sliding window with O(n) complexity
///
/// RMS = sqrt(sum(x^2) / n) for each window
///
/// Currently supports Float64 arrays. Support for other numeric types (int32, int64, float32, etc.) coming soon.
///
/// Uses a two-phase algorithm:
/// 1. Fill initial window and compute first RMS
/// 2. Slide window: remove old value, add new value, compute RMS
///
/// # Arguments
/// * `data` - PyArrow Float64 array
/// * `window` - Window size for rolling RMS (must be > 0)
///
/// # Returns
/// PyArrow float64 array with rolling RMS values. First (window-1) values are None.
///
/// # Errors
/// * `MechPyError::InvalidInput` - Window size is 0 or invalid
/// * `MechPyError::DataTypeError` - Input is not a Float64 array
/// * `MechPyError::ComputationError` - Numerical computation failed
#[pyfunction]
fn rolling_rms(data: PyArray, window: usize) -> PyResult<PyArray> {
    // Validate window size
    if window == 0 {
        return Err(MechPyError::InvalidInput("Window size must be greater than 0".to_string()).into());
    }

    // Cast to Float64Array - for now only supports Float64, but extensible
    let array = data.array()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| MechPyError::DataTypeError("Array must be Float64 type (other numeric types coming soon)".to_string()))?;

    let len = array.len();
    let window_size = window;

    // Early return for edge cases
    if len == 0 {
        let empty_array: ArrayRef = Arc::new(Float64Array::new_null(0));
        return Ok(PyArray::from_array_ref(empty_array));
    }

    // Prepare result builder with capacity
    let mut builder = arrow::array::Float64Builder::with_capacity(len);

    // Running sum of squares and count for sliding window (O(n) algorithm)
    let mut sum_squares = 0.0;
    let mut count = 0;

    // Phase 1: Append nulls for positions 0 to window_size-2 (not enough data for full window)
    for _ in 0..(window_size - 1).min(len) {
        builder.append_null();
    }

    // Phase 2: Fill initial window
    for i in 0..window_size.min(len) {
        if !array.is_null(i) {
            let val = array.value(i);
            sum_squares += val * val;
            count += 1;
        }
    }

    // Compute RMS for the first complete window (position window_size - 1)
    if window_size <= len {
        if count > 0 {
            let rms = (sum_squares / count as f64).sqrt();
            if !rms.is_finite() {
                return Err(MechPyError::ComputationError(
                    format!("Non-finite RMS computed at position {}: {}", window_size - 1, rms)
                ).into());
            }
            builder.append_value(rms);
        } else {
            builder.append_null();
        }
    }

    // Phase 3: Slide the window and compute rolling RMS
    for i in window_size..len {
        // Remove old value leaving the window
        let old_idx = i - window_size;
        if !array.is_null(old_idx) {
            let old_val = array.value(old_idx);
            sum_squares -= old_val * old_val;
            count -= 1;
        }

        // Add new value entering the window
        if !array.is_null(i) {
            let new_val = array.value(i);
            sum_squares += new_val * new_val;
            count += 1;
        }

        // Compute and store RMS for current window
        if count > 0 {
            let rms = (sum_squares / count as f64).sqrt();
            if !rms.is_finite() {
                return Err(MechPyError::ComputationError(
                    format!("Non-finite RMS computed at position {}: {}", i, rms)
                ).into());
            }
            builder.append_value(rms);
        } else {
            builder.append_null();
        }
    }

    let result_array: ArrayRef = Arc::new(builder.finish());
    Ok(PyArray::from_array_ref(result_array))
}

/// Efficient FFT analysis for PyArrow arrays
/// Computes frequency-domain representation using real-valued FFT
///
/// Returns a dictionary with:
/// - 'frequencies': Frequency bins in Hz
/// - 'magnitude': Magnitude spectrum
/// - 'phase': Phase spectrum in radians
///
/// Uses realfft library for high-performance real-to-complex FFT.
/// Input length should be a power of 2 for optimal performance.
///
/// # Arguments
/// * `data` - PyArrow Float64 array of time-domain signal
/// * `sample_rate` - Sampling frequency in Hz
///
/// # Returns
/// Python dictionary with frequency domain analysis results
///
/// # Errors
/// * `MechPyError::InvalidInput` - Sample rate is 0 or invalid
/// * `MechPyError::DataTypeError` - Input is not a Float64 array
/// * `MechPyError::ComputationError` - FFT computation failed
#[pyfunction]
fn fft_analysis(data: PyArray, sample_rate: f64) -> PyResult<PyObject> {
    // Validate sample rate
    if sample_rate <= 0.0 {
        return Err(MechPyError::InvalidInput("Sample rate must be positive".to_string()).into());
    }

    // Cast to Float64Array
    let array = data.array()
        .as_any()
        .downcast_ref::<Float64Array>()
        .ok_or_else(|| MechPyError::DataTypeError("Array must be Float64 type".to_string()))?;

    let len = array.len();

    // Early return for edge cases
    if len == 0 {
        return Python::with_gil(|py| {
            let empty_array: ArrayRef = Arc::new(Float64Array::new_null(0));
            let result = PyDict::new_bound(py);
            result.set_item("frequencies", PyArray::from_array_ref(empty_array.clone()).into_py(py))?;
            result.set_item("magnitude", PyArray::from_array_ref(empty_array.clone()).into_py(py))?;
            result.set_item("phase", PyArray::from_array_ref(empty_array).into_py(py))?;
            Ok(result.to_object(py))
        });
    }

    // Handle null values by skipping them (replace with 0.0 for FFT)
    let mut real_data: Vec<f64> = Vec::with_capacity(len);
    for i in 0..len {
        real_data.push(if array.is_null(i) { 0.0 } else { array.value(i) });
    }

    // Create FFT planner and compute FFT
    let mut planner = RealFftPlanner::<f64>::new();
    let fft = planner.plan_fft_forward(len);

    // Allocate output buffer for complex results
    let mut spectrum = fft.make_output_vec();

    // Perform real-to-complex FFT
    fft.process(&mut real_data, &mut spectrum)
        .map_err(|e| MechPyError::ComputationError(format!("FFT computation failed: {:?}", e)))?;

    // Compute output length (N/2 + 1 for real FFT)
    let output_len = spectrum.len();

    // Create frequency bins for real FFT: f[i] = i * fs / N
    // This gives frequencies from 0 to fs/2
    let mut frequencies = Vec::with_capacity(output_len);
    for i in 0..output_len {
        frequencies.push((i as f64) * sample_rate / (len as f64));
    }

    // Extract magnitude and phase
    let mut magnitudes = Vec::with_capacity(output_len);
    let mut phases = Vec::with_capacity(output_len);

    for complex_val in &spectrum {
        magnitudes.push(complex_val.norm());  // Magnitude = sqrt(re^2 + im^2)
        phases.push(complex_val.arg());       // Phase = atan2(im, re)
    }

    // Convert to Arrow arrays
    let freq_array: ArrayRef = Arc::new(Float64Array::from(frequencies));
    let mag_array: ArrayRef = Arc::new(Float64Array::from(magnitudes));
    let phase_array: ArrayRef = Arc::new(Float64Array::from(phases));

    // Create Python dictionary result
    Python::with_gil(|py| {
        let result = PyDict::new_bound(py);
        result.set_item("frequencies", PyArray::from_array_ref(freq_array).into_py(py))?;
        result.set_item("magnitude", PyArray::from_array_ref(mag_array).into_py(py))?;
        result.set_item("phase", PyArray::from_array_ref(phase_array).into_py(py))?;
        Ok(result.to_object(py))
    })
}

pub fn register_module(py: Python, parent: &Bound<PyModule>) -> PyResult<()> {
    let sensor_module = PyModule::new_bound(py, "sensor")?;
    sensor_module.add_function(wrap_pyfunction!(rolling_mean, sensor_module.clone())?)?;
    sensor_module.add_function(wrap_pyfunction!(rolling_rms, sensor_module.clone())?)?;
    sensor_module.add_function(wrap_pyfunction!(fft_analysis, sensor_module.clone())?)?;
    parent.add_submodule(&sensor_module)?;

    py.import_bound("sys")?
        .getattr("modules")?
        .set_item("mechpy.sensor", sensor_module)?;

    Ok(())
}
