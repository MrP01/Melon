#include <iostream>
#include <math.h>
#include <pybind11/pybind11.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static const double INITIAL_TEMPERATURE = 0.4;
static const double SWEEP_EXPONENT = -2.0;
static const size_t DAY_LENGTH = 14;

namespace py = pybind11;
typedef std::vector<size_t> State;

struct Task {
  std::string uid;
  float duration;
  int priority;
  int location;
  float due;
};

struct SpreadResult {
  std::string uid;
  float start;
  float duration;
};

class MCMCScheduler {
 public:
  double temperature;
  State state;
  std::vector<Task> tasks;

 public:
  MCMCScheduler() = default;

  void initState() {
    temperature = INITIAL_TEMPERATURE;
    for (size_t i = 0; i < tasks.size(); i++)
      state.push_back(i);
  }

  std::vector<SpreadResult> spreadTasks(State order) {
    float slot_start = 0.0;
    float slot_duration = DAY_LENGTH;
    float stamp = slot_start;
    std::vector<SpreadResult> schedule;
    for (size_t i = 0; i < order.size(); i++) {
      auto task = tasks[order[i]];
      if (task.duration > DAY_LENGTH)
        throw std::exception();
      if (stamp + task.duration > slot_start + slot_duration) {
        slot_start += 24;
        stamp = slot_start;
      }
      schedule.push_back(SpreadResult{task.uid, stamp, task.duration});
      stamp += task.duration;
    }
    return schedule;
  }

  double computeEnergy(State order) {
    auto spread = spreadTasks(order);
    auto last = spread[spread.size() - 1];
    auto first = spread[0];
    double timePenalty = last.start + last.duration - first.start;
    double priorityPenalty = 0;
    double commutePenalty = 0;
    double onTimePenalty = 0;
    for (size_t index = 1; index < order.size(); index++) {
      auto thisTask = tasks[order[index]];
      auto thisSlot = spread[index];
      priorityPenalty += index * thisTask.priority;
      if (thisTask.due != 0.0 && thisTask.due < thisSlot.start + thisSlot.duration)
        onTimePenalty += 100.0;
      auto previousTask = tasks[order[index - 1]];
      if (thisTask.location == 0 || previousTask.location == 0)
        continue;
      if (thisTask.location != previousTask.location)
        commutePenalty += 30.0;
    }
    // std::cout << timePenalty << ", " << priorityPenalty << ", " << commutePenalty << ", " << onTimePenalty <<
    // std::endl;
    return timePenalty + priorityPenalty + commutePenalty + onTimePenalty;
  }

  State permuteState() {
    State proposal = state; // copy current state
    size_t cityA_ = rand() % tasks.size();
    size_t cityB_ = rand() % tasks.size();
    proposal[cityA_] = state[cityB_];
    proposal[cityB_] = state[cityA_];
    return proposal;
  }

  void mcmcSweep(size_t steps, bool print_raw = true) {
    double energy = computeEnergy(state);
    double E_sum = 0, E_squared_sum = 0;
    for (size_t i = 0; i < steps; i++) {
      State proposal = permuteState();
      double delta = computeEnergy(proposal) - energy;
      double acceptanceProbability = std::min(1.0, std::exp(-delta / (energy * temperature)));
      // std::cout << "AccProb: " << acceptanceProbability << " Temp: " << temperature << " State: " << state[0] << ", "
      //           << state[1] << ", " << state[2] << std::endl;
      if (((double)rand() / RAND_MAX) < acceptanceProbability) {
        state = proposal;
        energy += delta;
      }
    }
  }

  void mcmcSimulate(size_t iterations) {
    for (size_t j = 0; j < iterations; j++) {
      mcmcSweep(tasks.size() * tasks.size());
      temperature = INITIAL_TEMPERATURE * std::pow(j + 1, SWEEP_EXPONENT);
    }
  }
};

py::list schedule(const py::list &tasks) {
  auto scheduler = MCMCScheduler();
  for (auto it = tasks.begin(); it != tasks.end(); ++it) {
    // unpack the tuple assuming it has exactly 4 elements (uid, duration, priority, location)
    auto tupleIterator = it->cast<py::tuple>().begin();
    auto task = Task{(tupleIterator++)->cast<std::string>(), (tupleIterator++)->cast<float>(),
        (tupleIterator++)->cast<int>(), tupleIterator->cast<int>(), tupleIterator->cast<float>()};
    scheduler.tasks.push_back(task);
    // std::cout << task.uid << ": " << task.duration << ", " << task.priority << ", " << task.location << std::endl;
  }
  scheduler.initState();
  scheduler.mcmcSimulate(15);
  auto result = py::list();
  auto spread = scheduler.spreadTasks(scheduler.state);
  for (size_t i = 0; i < spread.size(); i++) {
    result.append(py::make_tuple(spread[i].uid, spread[i].start, spread[i].duration));
  }
  return result;
}

PYBIND11_MODULE(libcppscheduler, m) {
  srand(time(NULL)); // seed the random number generator

  m.doc() = "Schedule tasks";
  m.def("schedule", &schedule, "Schedule tasks");
}
