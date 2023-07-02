# Melon UI

A CalDav Task Application written in Qt6.

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
