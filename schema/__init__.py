"""The command contract.

The single definition of what a valid swarm command is. Imported by data/,
train/, runtime/, and eval/ -- nothing here may be duplicated elsewhere.

Three validation layers, in order:
    cmd.gbnf     structure  -- constrains decoding; guarantees syntax, not meaning
    validate.py  meaning    -- Pydantic; clamps and logs, never rejects
    ../swarm/fsm.py legality -- refuses commands illegal in the current state

canon.py is the one comparator. Exp-1 (text) and Exp-3 (audio) call the same
function, which is why EM minus CRR on the same items is exactly the cost of
speech recognition.
"""
