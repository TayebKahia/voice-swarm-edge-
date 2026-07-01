"""The swarm: state machine, controllers, and both simulation backends.

Nothing here touches audio. Tests take a JSON command object and assert on drone
state, which is why swarm/ is separate from runtime/ -- test_fsm.py runs with no
microphone attached.

    fsm.py          flight state machine; refuses illegal transitions
    control.py      Boids, formation slot assignment, APF separation, PID nav
    env_numpy.py    fast backend, for iteration
    env_pyflyt.py   fidelity backend, for final results

Both backends implement the same SwarmEnv interface, so switching is one line.
The hard geometric velocity clamp lives at the integrator, not in the validator.
"""
