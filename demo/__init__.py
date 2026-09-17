"""The live demonstration of Chapter 6 (sec:demonstration-protocol): the workstation side.

    workstation.py   bus consumer, state machine, link, simulation and display (Parts A and B)
    rehearse.py      publishes tab:demo-script onto the bus in place of the Raspberry Pi

The device side is `runtime/main.py`; the link from the state machine to the controller is
`swarm/link.py`. Nothing here is measured: a run writes its log and trajectory to `demo_runs/`,
never to `results/`.
"""
