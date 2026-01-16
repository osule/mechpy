use pyo3::prelude::*;

pub mod error;
pub mod sensor;

#[pymodule]
fn mechpy(py: Python, m: &Bound<PyModule>) -> PyResult<()> {
    sensor::register_module(py, m)?;
    Ok(())
}
