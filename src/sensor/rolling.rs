use pyo3::prelude::*;
use pyo3_arrow::PyArray;
use arrow::array::{ArrayRef, Float64Array, Array};
use std::sync::Arc;

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
pub fn rolling_mean(data: PyArray, window: usize) -> PyResult<PyArray> {
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
pub fn rolling_rms(data: PyArray, window: usize) -> PyResult<PyArray> {
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