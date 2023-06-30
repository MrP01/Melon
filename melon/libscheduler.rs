extern crate cpython;
extern crate rand;

use std::borrow::Cow;

use cpython::{py_fn, py_module_initializer, PyDict, PyObject, PyResult, PyTuple, Python};

const INITIAL_TEMPERATURE: f64 = 0.2;

struct Task {
  uid: Cow<'static, str>,
  duration: f32, // in hours
  priority: u32,
  location: u32,
}

struct TimeSlot {
  timestamp: f32, // in hours
  duration: f32,  // in hours
}

fn permute_state(state: Vec<i32>) -> Vec<i32> {
  return state;
}

fn spread_tasks(tasks: &Vec<Task>, state: &Vec<i32>) -> Vec<(Cow<'static, str>, TimeSlot)> {
  return vec![];
}

fn compute_energy(tasks: &Vec<Task>, state: &Vec<i32>) -> f64 {
  let spread = spread_tasks(&tasks, &state);
  return 0.0;
}

fn mcmc_sweep(tasks: &Vec<Task>, initial_state: Vec<i32>, temperature: f64) -> Vec<i32> {
  let N = tasks.len() as i32;
  let mut state = initial_state;
  let mut energy = compute_energy(&tasks, &state);
  for i in 0..N * N {
    let new_state = permute_state(state.clone());
    let delta = compute_energy(&tasks, &new_state) - energy;
    let acceptance_probability = (-delta / (energy * temperature)).exp();
    if rand::random::<f64>() < acceptance_probability {
      state = new_state;
      energy += delta;
    }
  }
  return vec![];
}

fn schedule(tasks: &Vec<Task>) -> Vec<(Cow<'static, str>, TimeSlot)> {
  let N = tasks.len() as i32;
  let mut state = (0..N).collect();
  for k in 1..11 {
    state = mcmc_sweep(&tasks, state, INITIAL_TEMPERATURE * (k as f64).powf(-1.0));
  }
  return spread_tasks(&tasks, &state);
}

fn py_task_to_task(object: &PyTuple) -> Task {
  return Task {
    uid: Cow::Borrowed("hi"),
    duration: 1.0,
    priority: 9,
    location: 0,
  };
}

fn py_schedule(_py: Python, tasks: Vec<PyTuple>) -> PyResult<Vec<PyTuple>> {
  let my_tasks: Vec<Task> = tasks.iter().map(py_task_to_task).collect();
  let calendar = schedule(&my_tasks);
  let elements = vec![];
  let tuple = PyTuple::new(_py, &elements);
  let results = vec![tuple];
  Ok(results)
}

py_module_initializer!(libscheduler, initlibscheduler, PyInit_scheduler, |py, m| {
  m.add(py, "__doc__", "This module is implemented in Rust.")?;
  m.add(py, "schedule", py_fn!(py, py_schedule(tasks: Vec<PyTuple>)))?;
  Ok(())
});
