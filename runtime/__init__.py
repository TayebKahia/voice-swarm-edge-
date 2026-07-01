"""The live voice pipeline. Sound in, validated command out.

Branch B -- the language path, 2,500 ms p95 from end of speech:
    audio.py -> vad.py -> stt.py -> parser.py -> bus.py

Branch A -- the reflex path, <=150 ms from keyword offset:
    audio.py -> branch_a.py -> bus.py

Branch A carries two classes only, "swarm hold" and "swarm abort", and bypasses
speech recognition and the language model entirely. Every bus message carries a
monotonic sequence number and a branch tag; the state machine drops any Branch B
message whose sequence number is below the highest applied Branch A message.
That sequence rule is the correctness guarantee. Killing a decode mid-flight is
an optimisation on top of it.
"""
