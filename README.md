# Melon Task Scheduler + UI

A CalDav Todo-List (/ Task-Scheduling) Application that uses Markov chain Monte-Carlo to optimise a task schedule.
It also features a User Interface written with Qt6.

To start the GUI:

```python
from melongui.main import main
main() # to start the GUI
```

which launches a User Interface such as the one depicted in Figure 1.
To load todos from a remote calendar, as specified in the configuration file, and
schedule them, use the following code-snippet:

```python
from melon.melon import Melon
from melon.scheduler.rust import RustyMCMCScheduler
melon = Melon()
melon.autoInit()
melon.scheduleAllAndExport("task-schedule.ics", Scheduler=RustyMCMCScheduler)
```

Creation of and interaction with \texttt{Todo}s in the calendar can be simple:

```python
from melon.melon import Melon

melon = Melon()  # loads the config and initialises
melon.autoInit()  # initiates a network connection to the server
matches = list(melon.findTask("Submit report"))
matches[0].complete()  # marks the todo as complete and syncs

calendar = melon.calendars["My Calendar"]
calendar.sync()  # fetches updates from the server
todo = calendar.createTodo("New Todo")
todo.dueDate = datetime.date.today()
todo.save()  # saves the todo to the server
```

In order to run the scheduler on demonstration data, please run

```python
from melon.scheduler.rust import RustyMCMCScheduler
tasks = generateManyDemoTasks(N=80)
scheduler = RustyMCMCScheduler(tasks)
result = scheduler.schedule()
```

If not specified in the initialiser, Melon loads a configuration file located in the user’s
home configuration directory, so on Linux `~/.config/melon/config.toml`. The
file uses Tom’s Obvious, Minimal Language (TOML) format and has the following
contents:

```toml
[client]
url = "https://my-caldav-server.org:2023/dav/user/calendars/"
username = "user"
password = "password"
```

Melon is a Python package on a Markov chain Monte-Carlo (MCMC), using Metropolis-Hastings with Simulated Annealing, optimisation of task scheduling.
The idea would be to automatically schedule a set of tasks into a calendar based on due date, duration estimate (perhaps dynamically updated), task priority, associated project affiliation and most importantly, location.
State permutations would be generated randomly according to a probability distribution, starting from a good initial guess of ordering tasks by due date and priority.

One can then define multiple optimisation metrics, based on the number of performed tasks weighted by priority and the need to switch locations.
So in some sense, reducing the need for commute to e.g. work and scheduling hybrid / on-site tasks according to that (resembling the travelling-salesman problem).
One could also make that very context dependent using project affiliations or certain keywords, automating the process.
All of this should be done keeping the due date in mind.
Another challenge is to encode task dependencies i.e. task B requiring the completion of task A beforehand.

Coding-wise this will include the algorithm itself, appropriate configuration and furthermore, I would like to integrate the system with a CalDAV endpoint for use with my personal calendar, making it accessible through a GUI (separated from the Python interface, so that one would be able to run the algorithm without).
Of course there will be tests and documentation on how to set things up, use the library on its own and how to install the GUI application.
An extension would be for the scheduler to learn about task properties based on user behaviour when rescheduling, etc. (detecting procrastination of an important task) and perhaps optimising suggestions based on that.

As performance might become an issue for MCMC, we will attempt the use of low-level languages such as C++ in combination with tools such as pybind11, to outsource short performance-critical code sections away from Python to another language?

The task check icon is the logo of the \textit{Tasks.org} Free and Open Source Android App, which may be found [here](https://github.com/tasks/tasks/tree/main/graphics).

## Troubleshooting

If you stumble accross

`This application failed to start because no Qt platform plugin could be initialized. Reinstalling the application may fix this problem.`

make sure to install `libxcb-cursor0`:

```bash
sudo apt install libxcb-cursor0
```
