extern crate cpython;

use cpython::{py_fn, py_module_initializer, PyResult, Python};

fn schedule(_py: Python) -> PyResult<Vec<Vec<u32>>> {
  let results = vec![vec![]; 3];
  Ok(results)
}

py_module_initializer!(libscheduler, initlibscheduler, PyInit_scheduler, |py, m| {
  m.add(py, "__doc__", "This module is implemented in Rust.")?;
  m.add(py, "schedule", py_fn!(py, schedule()))?;
  Ok(())
});
