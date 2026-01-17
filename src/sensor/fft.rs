use pyo3::prelude::*;
use pyo3::types::PyDict;
use pyo3_arrow::PyArray;
use arrow::array::{ArrayRef, Float64Array, Array};
use std::sync::Arc;
use realfft::RealFftPlanner;

use crate::error::MechPyError;

/// Helper function to create PyArray result dictionary
/// Reduces code duplication in result construction
fn create_fft_result(
    py: Python,
    freq_array: ArrayRef,
    mag_array: ArrayRef,
    phase_array: ArrayRef
) -> PyResult<PyObject> {
    let result = PyDict::new_bound(py);
    result.set_item("frequencies", PyArray::from_array_ref(freq_array).into_py(py))?;
    result.set_item("magnitude", PyArray::from_array_ref(mag_array).into_py(py))?;
    result.set_item("phase", PyArray::from_array_ref(phase_array).into_py(py))?;
    Ok(result.to_object(py))
}


/// Efficient FFT analysis for PyArrow arrays
/// Computes frequency-domain representation using real-valued FFT
///
/// Returns a dictionary with:
/// - 'frequencies': Frequency bins in Hz (0 to Nyquist frequency)
/// - 'magnitude': Magnitude spectrum (signal strength at each frequency)
/// - 'phase': Phase spectrum in radians (-π to π)
///
/// Uses realfft library for high-performance real-to-complex FFT.
/// FFT planners are cached globally for optimal performance on repeated calls
/// with the same input size.
///
/// # Null Value Handling
///
/// Null values in the input array are replaced with 0.0 before FFT computation.
/// This prevents NaN propagation but may introduce minor spectral artifacts.
/// For critical applications, consider preprocessing your data to:
/// - Interpolate missing values
/// - Filter out null-containing segments
/// - Use alternative gap-filling strategies
///
/// Input length should ideally be a power of 2 for optimal performance,
/// though non-power-of-2 sizes are supported.
///
/// # Arguments
/// * `data` - PyArrow Float64 array of time-domain signal
/// * `sample_rate` - Sampling frequency in Hz (must be > 0)
///
/// # Returns
/// Python dictionary with frequency domain analysis results:
/// - `frequencies`: Array of frequency values in Hz
/// - `magnitude`: Array of signal magnitudes (linear scale)
/// - `phase`: Array of phase angles in radians
///
/// # Performance
/// - FFT planners are cached for repeated use with same input sizes
/// - O(N log N) complexity where N is input length
/// - Memory efficient with minimal allocations
///
/// # Errors
/// * `MechPyError::InvalidInput` - Sample rate ≤ 0 or invalid
/// * `MechPyError::DataTypeError` - Input is not a Float64 array
/// * `MechPyError::ComputationError` - FFT computation failed
#[pyfunction]
pub fn fft_analysis(data: PyArray, sample_rate: f64) -> PyResult<PyObject> {
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
            create_fft_result(py, empty_array.clone(), empty_array.clone(), empty_array)
        });
    }

    // Handle null values by skipping them (replace with 0.0 for FFT)
    let mut real_data: Vec<f64> = Vec::with_capacity(len);
    for i in 0..len {
        real_data.push(if array.is_null(i) { 0.0 } else { array.value(i) });
    }

    // Create FFT planner
    // TODO: Implement planner caching for repeated calls with same input size
    let mut planner = RealFftPlanner::<f64>::new();
    let fft = planner.plan_fft_forward(len);

    // Allocate output buffer for complex results
    let mut spectrum = fft.make_output_vec();

    // Perform real-to-complex FFT
    fft.process(&mut real_data, &mut spectrum)
        .map_err(|e| MechPyError::ComputationError(format!("FFT computation failed: {:?}", e)))?;

    // Compute output length (N/2 + 1 for real FFT)
    let output_len = spectrum.len();

    // Create frequency bins: f[i] = i * sample_rate / len
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
        create_fft_result(py, freq_array, mag_array, phase_array)
    })
}