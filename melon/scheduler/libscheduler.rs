extern crate cpython;
use rand::Rng;

use cpython::{py_fn, py_module_initializer, PyResult, Python};

const INITIAL_TEMPERATURE: f64 = 0.2;
const DAY_LENGTH: f32 = 14.0;

struct Task {
  uid: String,
  duration: f32, // in hours
  priority: u32,
  location: u32,
  due: f32, // in hours
}

struct TimeSlot {
  timestamp: f32, // in hours
  duration: f32,  // in hours
}

fn permute_state(state: &mut Vec<usize>) {
  let mut rng = rand::thread_rng();
  let index_a = rng.gen_range(0..state.len());
  let index_b = rng.gen_range(0..state.len());
  let value_at_a = state[index_a];
  state[index_a] = state[index_b];
  state[index_b] = value_at_a;
}

fn generate_next_working_slot(previous: TimeSlot) -> TimeSlot {
  return TimeSlot {
    timestamp: previous.timestamp + 24.0,
    duration: DAY_LENGTH,
  };
}

fn spread_tasks(tasks: &Vec<Task>, state: &Vec<usize>) -> Vec<(String, TimeSlot)> {
  let mut slot = TimeSlot {
    timestamp: 0.0,
    duration: DAY_LENGTH,
  };
  let mut stamp = slot.timestamp;
  let mut spread: Vec<(String, TimeSlot)> = vec![];
  for index in state {
    let task = &tasks[*index];
    if task.duration > slot.duration {
      panic!("Cannot schedule a task longer than the slot!");
    }
    if stamp + task.duration > slot.timestamp + slot.duration {
      slot = generate_next_working_slot(slot);
      stamp = slot.timestamp;
    }
    spread.push((
      task.uid.clone(),
      TimeSlot {
        timestamp: stamp,
        duration: task.duration,
      },
    ));
    stamp += task.duration;
  }
  return spread;
}

fn compute_energy(tasks: &Vec<Task>, state: &Vec<usize>) -> f64 {
  let spread = spread_tasks(&tasks, &state);
  let first = spread.first().expect("Cannot get energy of an empty state");
  let last = spread.last().expect("Cannot get energy of an empty state");
  let time_penalty = (last.1.timestamp + last.1.duration - first.1.timestamp) as f64;
  let priority_penalty: u32 = (0..state.len())
    .map(|i| (i as u32) * tasks[state[i] as usize].priority)
    .sum();
  let mut commute_penalty: f64 = 0.0;
  let mut on_time_penalty: f64 = 0.0;
  for index in 1..state.len() {
    let previous_task = &tasks[state[index - 1]];
    let this_task = &tasks[state[index]];
    if this_task.due != 0.0 && this_task.due < spread[index].1.timestamp + spread[index].1.duration {
      on_time_penalty += 100.0;
    }
    if previous_task.location == 0 || this_task.location == 0 {
      continue;
    }
    if previous_task.location != this_task.location {
      commute_penalty += 30.0;
    }
  }
  // println!(
  //   "Penalties {}, {}, {}, {}",
  //   time_penalty, priority_penalty, commute_penalty, on_time_penalty
  // );
  return time_penalty + priority_penalty as f64 + commute_penalty + on_time_penalty;
}

fn mcmc_sweep(tasks: &Vec<Task>, initial_state: Vec<usize>, temperature: f64) -> Vec<usize> {
  let n = tasks.len();
  let mut state = initial_state;
  let mut energy = compute_energy(&tasks, &state);
  for _i in 0..n * n {
    let mut new_state = state.clone();
    permute_state(&mut new_state);
    let delta = compute_energy(&tasks, &new_state) - energy;
    let acceptance_probability = (-delta / (energy * temperature)).exp();
    if rand::random::<f64>() < acceptance_probability {
      state = new_state;
      energy += delta;
    }
  }
  return state;
}

fn schedule(tasks: &Vec<Task>) -> Vec<(String, TimeSlot)> {
  let n = tasks.len();
  let mut state = (0..n).collect();
  for k in 1..11 {
    state = mcmc_sweep(&tasks, state, INITIAL_TEMPERATURE * (k as f64).powf(-1.0));
  }
  return spread_tasks(&tasks, &state);
}

fn py_schedule(_py: Python, tasks: Vec<(String, f32, u32, u32, f32)>) -> PyResult<Vec<(String, f32, f32)>> {
  let my_tasks: Vec<Task> = tasks
    .iter()
    .map(|x| Task {
      uid: x.0.clone(),
      duration: x.1,
      priority: x.2,
      location: x.3,
      due: x.4,
    })
    .collect();
  let calendar = schedule(&my_tasks);
  let results = calendar
    .iter()
    .map(|x| (x.0.clone(), x.1.timestamp, x.1.duration))
    .collect();
  Ok(results)
}

py_module_initializer!(libscheduler, initlibscheduler, PyInit_scheduler, |py, m| {
  m.add(py, "__doc__", "This module is implemented in Rust.")?;
  m.add(
    py,
    "schedule",
    py_fn!(py, py_schedule(tasks: Vec<(String, f32, u32, u32, f32)>)),
  )?;
  Ok(())
});
