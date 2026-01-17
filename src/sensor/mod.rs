use pyo3::prelude::*;
use pyo3::types::PyModule;

// Re-export functions from submodules
pub use rolling::{rolling_mean, rolling_rms};
pub use fft::fft_analysis;

pub mod rolling;
pub mod fft;

/// Register all sensor functions with the Python module
pub fn register_module(py: Python, parent: &Bound<PyModule>) -> PyResult<()> {
    let sensor_module = PyModule::new_bound(py, "sensor")?;

    // Register functions from submodules
    sensor_module.add_function(wrap_pyfunction!(rolling_mean, sensor_module.clone())?)?;
    sensor_module.add_function(wrap_pyfunction!(rolling_rms, sensor_module.clone())?)?;
    sensor_module.add_function(wrap_pyfunction!(fft_analysis, sensor_module.clone())?)?;

    parent.add_submodule(&sensor_module)?;

    py.import_bound("sys")?
        .getattr("modules")?
        .set_item("mechpy.sensor", sensor_module)?;

    Ok(())
}