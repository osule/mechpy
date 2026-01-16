use std::fmt;

/// Library-wide error types for MechPy
#[derive(Debug)]
pub enum MechPyError {
    /// Invalid input parameters (wrong types, out of range, etc.)
    InvalidInput(String),

    /// Data type conversion or validation errors
    DataTypeError(String),

    /// Array or data access errors
    DataAccessError(String),

    /// Numerical computation errors (NaN, overflow, etc.)
    ComputationError(String),

    /// I/O or external system errors
    IoError(String),

    // Module-specific errors can be added here as needed
    // SimulationError(SimulationError),  // Future modules
}

impl fmt::Display for MechPyError {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            MechPyError::InvalidInput(msg) => write!(f, "Invalid input: {}", msg),
            MechPyError::DataTypeError(msg) => write!(f, "Data type error: {}", msg),
            MechPyError::DataAccessError(msg) => write!(f, "Data access error: {}", msg),
            MechPyError::ComputationError(msg) => write!(f, "Computation error: {}", msg),
            MechPyError::IoError(msg) => write!(f, "I/O error: {}", msg),
        }
    }
}

impl std::error::Error for MechPyError {}

/// Convert MechPyError to PyErr for Python interop
impl From<MechPyError> for pyo3::PyErr {
    fn from(err: MechPyError) -> pyo3::PyErr {
        match err {
            MechPyError::InvalidInput(_) => pyo3::exceptions::PyValueError::new_err(err.to_string()),
            MechPyError::DataTypeError(_) => pyo3::exceptions::PyTypeError::new_err(err.to_string()),
            MechPyError::DataAccessError(_) => pyo3::exceptions::PyRuntimeError::new_err(err.to_string()),
            MechPyError::ComputationError(_) => pyo3::exceptions::PyRuntimeError::new_err(err.to_string()),
            MechPyError::IoError(_) => pyo3::exceptions::PyOSError::new_err(err.to_string()),
        }
    }
}