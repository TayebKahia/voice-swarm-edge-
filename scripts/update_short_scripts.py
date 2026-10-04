#!/usr/bin/env python3
"""Update SLIDES_AND_NOTES.md with short, simple, precise spoken scripts for all 33 slides."""

import re
import sys
from pathlib import Path

# Dictionary of concise scripts for slides 1 to 33
SCRIPTS = {
    1: {
        "time": "45 sec",
        "script": """Good morning Mister President, honorable members of the jury, Professor Khaldi, and guests.
Today, I present my graduation defense fulfilling the dual requirements for the Master of Science in AI and Data Science and the State Engineering Degree in Computer Science.
Our work is structured into two complementary tracks:
First, the Master's track: foundational scientific research on Small Language Models, formal grammars, and edge quantization trade-offs.
Second, the Engineering track: systems architecture, a dual-path real-time safety runtime, and autonomous drone swarm control on edge hardware.
Let us begin."""
    },
    2: {
        "time": "50 sec",
        "script": """In field operations like surveillance and inspection, a single operator cannot manually pilot multiple drones with joysticks. Natural voice commands enable direct, high-level tactical control.
However, in remote environments, cloud connectivity is unavailable. All computation—speech recognition, language understanding, and swarm coordination—must run 100% locally on the edge.
Our hardware target is a constrained Raspberry Pi 5 with 8 gigabytes of RAM and a pure ARM CPU.
Our challenge: How can we achieve reliable, natural voice control on an inexpensive edge CPU while guaranteeing mathematical safety and real-time execution?"""
    },
    3: {
        "time": "55 sec",
        "script": """We divide the problem cleanly across the two diplomas:
The Master’s thesis addresses Research Question 1: What is the optimal accuracy–efficiency trade-off for sub-1B parameter models on an edge CPU? This delivers Contributions C1, C2, and C3 through our thermal and multi-model benchmarks.
The Engineering thesis addresses Research Questions 2 and 3: Can the system meet real-time latency budgets, survive drone rotor noise, and fly collision-free? This delivers Contribution C4 through our dual-path runtime and swarm controller.
In short: the Master's track selects the model; the Engineering track deploys and validates it in embodied flight."""
    },
    4: {
        "time": "40 sec",
        "script": """Here is our defense roadmap:
We begin with Part I, the Master’s track, examining formal grammars, fine-tuning, quantization, and our multi-model benchmark.
Next, a brief bridge highlights why language models alone cannot safely fly drone swarms.
Then, Part II covers the Engineering track: our dual-path safety architecture, acoustic robustness in propeller noise, and multi-UAV collision avoidance.
Finally, we conclude with our live demonstration, an honest requirements compliance audit, and future perspectives.
Let us begin with Part I."""
    },
    5: {
        "time": "55 sec",
        "script": """Part I addresses Research Question 1: the edge accuracy–efficiency dilemma.
Standard Large Language Models require cloud server farms. In contrast, Small Language Models—under 1 billion parameters—can run locally on an edge CPU without internet access.
However, edge execution creates a strict trade-off: models above 1 billion parameters are too slow for interactive control, while models under 0.5 billion risk poor parameter extraction.
Furthermore, we must determine whether 4-bit integer quantization preserves command parsing accuracy.
Our target envelope requires at least 85% Exact Match accuracy with a decode latency under 1.1 seconds on the Raspberry Pi 5."""
    },
    6: {
        "time": "55 sec",
        "script": """Our literature review identified three distinct research gaps:
Gap 1: Prior studies on grammar-constrained decoding evaluate only base models, leaving unmeasured whether fine-tuned models still benefit from formal grammars. We address this with Contribution C1.
Gap 2: Existing voice datasets focus on smart-home assistants like Alexa, with zero public corpora for multi-UAV swarm commands. We solve this with Contribution C2.
Gap 3: Hardware papers report raw tokens-per-second, while quantization papers test general NLP perplexity on cloud GPUs. None measure task-level parsing accuracy and edge latency together on sub-1B models. We close this with Contribution C3."""
    },
    7: {
        "time": "50 sec",
        "script": """Our first contribution, C1, is a formal command schema enforced by a GBNF grammar.
We chose GBNF because it executes natively inside `llama.cpp`'s C++ sampling loop, incurring zero Python runtime overhead on the ARM CPU.
During token generation, any token violating our context-free grammar receives a logit mask of minus infinity, making syntax errors mathematically impossible to emit.
We bounded all grammar rules—capping numbers to three digits and drone IDs to 0 through 4.
This guarantees 100% JSON schema validity by construction and prevents infinite generation loops."""
    },
    8: {
        "time": "55 sec",
        "script": """Contribution C2 is our label-first dataset pipeline.
Instead of collecting arbitrary text and fitting code to it, we define valid flight command schemas first, then generate diverse natural language utterances. This ensures every sample produces an executable flight mission.
Crucially, we eliminate data leakage through template-family isolation.
Standard random splitting allows identical phrasing patterns to leak between training and test sets. Instead, we isolate entire sentence structures: if a phrasing pattern is used in training, it never appears in the test set.
When the model succeeds on unseen phrasing, it proves genuine semantic understanding rather than memorization."""
    },
    9: {
        "time": "55 sec",
        "script": """To adapt base language models to our flight schema, we use Low-Rank Adaptation (LoRA).
Full fine-tuning updates hundreds of millions of parameters, demanding massive optimizer memory and risking catastrophic forgetting of natural language syntax.
LoRA freezes the pre-trained weights and injects trainable low-rank decomposition matrices ($r=16, \\alpha=32$).
We target all linear projections—both self-attention and MLP feed-forward layers.
This updates less than 1% of total parameters—approximately 5 million weights—trained over 3 epochs with AdamW and cosine decay, preventing overfitting while maintaining reasoning capability."""
    },
    10: {
        "time": "55 sec",
        "script": """On an edge CPU, autoregressive token generation is memory-bandwidth bound: for each generated token, the CPU must stream all model weights through RAM.
Quantization accelerates execution by compressing weights from 16-bit floats to 4-bit integers, reducing memory bus traffic by approximately 70%.
We adopt the GGUF standard and evaluate FP16, Q8_0, and Q4_K_M.
Q4_K_M uses 256-weight super-blocks, retaining higher precision on critical attention projections while heavily compressing less sensitive layers.
This shrinks the model footprint from 1 gigabyte to 350 megabytes, keeping peak resident RAM under 0.68 gigabytes."""
    },
    11: {
        "time": "55 sec",
        "script": """Our benchmark evaluates three open-weight architectures on the Raspberry Pi 5: SmolLM2-360M, Qwen2.5-0.5B, and Llama-3.2-1B, running under `llama.cpp`.
Before benchmarking latency, Experiment 0 investigated thermal behavior under sustained load.
Without active cooling, the CPU throttled on 100% of trials, dropping the clock from 2.4 GHz to 1.5 GHz.
With an active cooler, thermal throttling dropped to 0%, clock speeds remained stable, and decode throughput increased by up to 68.5%.
This established our protocol: edge latency benchmarks are valid only under verified, active thermal stabilization."""
    },
    12: {
        "time": "55 sec",
        "script": """Table 17 presents the benchmark results on our 200-sample golden voice test set at Q4_K_M precision.
Exact Match requires 100% correct parsing of both intent and numerical slots.
Qwen2.5-0.5B achieved 93.5% Exact Match and a perfect 1.000 Intent F1, with a p95 decode latency of 1,033 milliseconds—satisfying our 1.1-second ceiling while using only 0.68 gigabytes of RAM.
Llama-3.2-1B achieved 91.0% Exact Match, but required 1,842 milliseconds—missing our latency budget by 67%—and consumed 1.63 gigabytes of RAM.
SmolLM2-360M was fast at 785 milliseconds, but dropped to 76.0% accuracy.
Qwen2.5-0.5B outperformed the 1.2B model in accuracy while running nearly twice as fast."""
    },
    13: {
        "time": "50 sec",
        "script": """In our main benchmark, model size and architecture varied simultaneously.
To isolate architecture as a variable, we introduced an iso-parameter control: H2O-Danube3-500M with 514 million parameters, matched within 4% of Qwen2.5’s 494 million.
Under identical training and testing conditions, Qwen2.5-0.5B achieved 93.5% Exact Match versus 87.0% for Danube3—a 6.5 percentage point advantage.
An exact McNemar test confirms this difference is statistically significant ($p = 0.0023$).
This proves that at the sub-billion parameter scale, pre-training corpus quality and architectural design outweigh marginal parameter differences."""
    },
    14: {
        "time": "50 sec",
        "script": """Because all models were evaluated on the exact same 200 test items, observations are paired, rendering independent t-tests invalid.
We applied exact McNemar paired tests on discordant pairs, with a Bonferroni-corrected threshold of $\\alpha = 0.0167$.
The statistical test confirmed that the 2.5 percentage point accuracy difference between Qwen2.5-0.5B and Llama-3.2-1B is not statistically significant ($p > 0.05$).
Because their accuracy is statistically equivalent, Qwen2.5 is the clear engineering choice: it executes 1.8 times faster and uses less than half the memory."""
    },
    15: {
        "time": "50 sec",
        "script": """We evaluated the empirical cost of quantization and conducted an ablation on our grammar constraint.
Quantizing Qwen2.5-0.5B from FP16 to Q4_K_M reduced Exact Match accuracy by only 1.5 percentage points. In exchange, RAM usage dropped by 70% and decode speed doubled, confirming 4-bit quantization is highly viable for edge robotics.
Next, our ablation study removed the GBNF grammar.
Without grammar constraints, the fine-tuned model occasionally omitted closing brackets, hallucinated undefined fields, or generated conversational filler.
This demonstrates that while fine-tuning teaches semantics, formal grammars remain essential to guarantee valid execution."""
    },
    16: {
        "time": "55 sec",
        "script": """To conclude the Master’s track, we formalize model selection using the Pareto frontier.
A configuration is Pareto-optimal if no competing model can improve latency without sacrificing accuracy.
Llama-3.2-1B is strictly dominated by Qwen2.5-0.5B: Qwen achieves higher accuracy, runs 1.8 times faster, and uses half the RAM.
On the non-dominated frontier, SmolLM2-360M is the fastest at 785 milliseconds, but falls below our 85% accuracy requirement.
Qwen2.5-0.5B Q4_K_M is the only candidate on the Pareto frontier that satisfies all operational constraints simultaneously.
We freeze this model and deploy it to Part II: the State Engineering track."""
    },
    17: {
        "time": "55 sec",
        "script": """In Part I, our language model achieved 93.5% accuracy in 1.03 seconds.
However, a text parser alone cannot safely control a physical drone swarm.
First, real flight introduces acoustic noise: spinning propellers degrade speech recognition.
Second, the safety-latency dilemma: drones moving at 3 meters per second travel 9 meters in 3 seconds. Waiting for an LLM to decode an emergency stop would lead to catastrophic crashes.
Third, language models lack physical awareness of battery levels, aerodynamics, and collisions.
To bridge this chasm, Part II introduces a real-time, deterministic, dual-path architecture to wrap the language model in physical safety guarantees."""
    },
    18: {
        "time": "50 sec",
        "script": """Part II addresses Research Questions 2 and 3: meeting real-time latency budgets and maintaining robustness in drone rotor noise.
We establish two distinct operational budgets based on command urgency:
First, the Reflex Path: emergency commands like 'hold' and 'abort' must reach flight controllers in under 150 milliseconds.
Second, the Cognitive Path: complex tactical formations allow a 2.5-second budget from End of Speech.
As shown on the timeline, this 2.5-second budget is partitioned across endpointing, speech recognition, language model inference, and bus validation."""
    },
    19: {
        "time": "55 sec",
        "script": """Contribution C4 is our Decoupled Dual-Path Runtime Architecture, running 100% offline on the Raspberry Pi 5.
Analogous to the human nervous system, we separate immediate spinal reflexes from conscious reasoning:
Branch A is our Reflex Path. A lightweight openWakeWord spotter monitors raw audio frames for emergency commands—'swarm hold' and 'swarm abort'—bypassing speech recognition entirely.
Branch B is our Cognitive Path. Silero VAD segments utterances, `whisper.cpp` transcribes the audio, Qwen parses the JSON parameters, and Pydantic validates the values.
Crucially, Branch A features preemption: triggering an emergency reflex instantly cancels in-flight LLM inference and seizes the command bus."""
    },
    20: {
        "time": "50 sec",
        "script": """Branch A operates under a strict Fail-Safe Membership Rule: an intent qualifies for the reflex path if and only if a false activation causes the swarm to do less, never more.
Only two commands satisfy this condition: 'swarm hold' and 'swarm abort'. If the keyword detector triggers erroneously, the drones simply freeze or land safely. Commands causing motion—such as takeoff or translation—are strictly excluded.
Audio is processed in 80-millisecond frames with a 1-second debounce.
Every reflex command carries a higher monotonic sequence timestamp, ensuring the flight controller immediately discards any slower, late-arriving cognitive command."""
    },
    21: {
        "time": "55 sec",
        "script": """Branch B handles natural language sentences in three sequential steps:
First, Silero VAD monitors the audio stream, using a 450-millisecond silence threshold to detect the end of speech.
Second, `whisper.cpp` transcribes the 16 kHz audio using the `tiny.en` model quantised to Q5 precision on 3 CPU cores. We prime the decoder with a domain prompt to bias it toward drone flight vocabulary.
Third, the transcript is posted to our local `llama-server`, parsing the command under the GBNF grammar.
In our deployed configuration, the server evaluated the full system prompt on each turn without KV-cache prefixing, introducing an un-cached prefill delay that we analyze in Experiment 2."""
    },
    22: {
        "time": "50 sec",
        "script": """Running audio capture, keyword spotting, speech recognition, and language modeling simultaneously risks CPU thread contention and audio dropouts.
To guarantee determinism, we apply asymmetric CPU core pinning via Linux `taskset`:
Core 0 is our Guardian Core, dedicated exclusively to audio acquisition, ring buffers, the reflex spotter, and OS scheduling. It is physically isolated from compute spikes.
Cores 1, 2, and 3 are allocated to heavy neural inference.
Because speech recognition and language parsing execute sequentially, Whisper and Qwen share Cores 1 through 3 without contention.
This ensures the reflex safety path remains responsive regardless of background computational load."""
    },
    23: {
        "time": "55 sec",
        "script": """We implement Defense in Depth through three independent validation layers before any command reaches the flight controllers:
Layer 1 is Structural Validity: GBNF grammar decoding ensures 100% syntactically correct JSON.
Layer 2 is Semantic Validity: Pydantic clamps numerical parameters to safe flight envelopes—such as altitudes between 0.5 and 10 meters. We apply a fail-soft policy: out-of-bounds values are safely clamped rather than crashing the system.
Layer 3 is Operational Legality: our 50 Hz Flight State Machine verifies current state legality, rejecting formation commands if the swarm is grounded.
Furthermore, an `abort` state locks the system, requiring a physical, manual operator reset before flight can resume."""
    },
    24: {
        "time": "55 sec",
        "script": """Our swarm controller coordinates 5 quadrotors at 50 Hz using Artificial Potential Fields (APF). Attractive forces guide drones to target slots in Circle, Line, or Wedge geometries, while repulsive forces maintain inter-agent separation.
To evaluate flight before hardware deployment, we developed two Software-in-the-Loop backends behind a unified interface:
PyFlyt provides realistic aerodynamics, motor lag, and rotor wash on the PyBullet physics engine.
A vectorized NumPy backend enables rapid multi-trial Monte Carlo testing.
Validated commands are published from the Raspberry Pi over a Zenoh UDP bus to the workstation, introducing under 3 milliseconds of communication delay."""
    },
    25: {
        "time": "60 sec",
        "script": """Experiment 2 benchmarks end-to-end latency on the cooled Raspberry Pi 5, following an honest engineering attribution:
First, the Reflex Path: p95 latency was 545 milliseconds against our 150-millisecond target. Our instrumentation revealed that board compute and bus transmission took only 18 milliseconds; the remaining latency stems from the 80-millisecond audio framing and the keyword spotter's sliding window.
Second, Preemption: 100% of the 78 in-flight language model decodes were successfully cancelled upon receiving a reflex keyword.
Third, the Cognitive Path: p95 latency reached 3.12 seconds against our 2.5-second target. The breakdown identified two bottlenecks: Whisper transcription took 1,449 milliseconds, and prompt prefill took 751 milliseconds due to uncached prompt evaluation."""
    },
    26: {
        "time": "55 sec",
        "script": """Experiment 3 evaluates acoustic robustness in quadrotor noise.
We digitally mixed our 200 golden audio recordings with real UAV propeller noise from the DREGON dataset across five Signal-to-Noise Ratios.
In clean audio, the Command Recognition Rate is 69.0%. Because our text parser alone achieves 93.5%, the speech recognition front-end introduces a 24.5 percentage point degradation.
As noise intensifies, performance holds steady down to 15 dB SNR, but degrades to 59.0% at 10 dB and 48.5% at 5 dB.
A one-way ANOVA ($F = 6.03, p = 8.6 \\times 10^{-5}$) and Tukey HSD tests confirm that significant acoustic degradation begins at 10 dB, establishing the operational acoustic envelope for field deployment."""
    },
    27: {
        "time": "55 sec",
        "script": """Experiment 4 evaluated swarm flight across 150 automated 60-second trials—50 each for circle, line, and wedge.
We observed zero collisions across all 150 trials.
Crucially, this safety was not achieved by Artificial Potential Fields alone. Our deterministic Geometric Separation Clamp intervened 432 times across 144 trials, overriding velocities whenever crossing trajectories brought drones within 0.8 meters. This proves that potential fields alone are insufficient for multi-UAV safety; a hard deterministic clamp is mandatory.
In convergence speed, the wedge formation converged fastest at a median of 2.30 seconds due to minimal path crossing, followed by the line at 3.26 seconds, and the circle at 4.06 seconds ($p < 10^{-120}$)."""
    },
    28: {
        "time": "55 sec",
        "script": """Table 21 presents our formal Requirements Compliance Matrix across 17 engineering criteria: 7 are fully met, 5 are missed with diagnosed root causes, 2 are undemonstrated, 2 require physical flight, and 1 is our live demonstration.
In an engineering defense, diagnosing misses is as valuable as meeting targets:
Reflex latency was bounded by audio framing and spotter windowing, not processor speed.
Cognitive latency was extended by Whisper compute and uncached prompt prefill.
Recognition accuracy was capped by acoustic transcription noise.
Finally, the safe-failure rate missed its target because fine-tuned language models inherently tend to emit plausible commands rather than abstaining with `unknown`.
All targets were fixed prior to testing, and every bottleneck is localized."""
    },
    29: {
        "time": "65 sec",
        "script": """We now begin Block IV: the Live Demonstration, running 100% offline on the Raspberry Pi 5.
We execute our pre-registered 8-step operational protocol:
First: 'Take off to five metres'—the swarm ascends to a 5-meter hover.
Second: 'Form a circle with radius five metres'—drones smoothly converge to circular positions.
Third: 'Move north ten metres'—the swarm translates while preserving formation geometry.
Fourth, our Preemption Test: I command 'Form a line with spacing three metres', and immediately trigger: 'SWARM HOLD!' Branch A detects the keyword, aborts the language model mid-inference, and the swarm freezes.
Fifth: We re-command the 3-meter line, and the formation completes.
Sixth: 'Land'—the drones descend to touchdown.
Seventh, our Abort Test: We command takeoff, and mid-air trigger: 'SWARM ABORT!' Motors cut immediately, and the state machine locks.
Eighth: Shouting vocal commands now does nothing. We press the physical reset button to restore the system to `LANDED`.
All pass criteria are verified."""
    },
    30: {
        "time": "55 sec",
        "script": """To synthesize our graduation project across both degrees:
In the Master’s track, we solved the foundational AI research problem:
Contribution C1 proved that C++ pushdown grammar constraints guarantee 100% schema validity at zero runtime overhead.
Contribution C2 established a verified, leakage-free multi-UAV command dataset.
Contribution C3 demonstrated through Pareto optimization that a 0.5B model at 4-bit quantization outperforms larger models on an edge CPU.
In the State Engineering track, we solved the embodied robotics problem:
Contribution C4 delivered the Decoupled Dual-Path Architecture, proving that a reflex bypass lane, CPU core pinning, and layered validation resolve the safety-latency dilemma, while our geometric clamp achieved 100% collision-free swarm flight.
Together, these contributions demonstrate that natural, safe drone swarm control can run completely offline on a low-cost single-board computer."""
    },
    31: {
        "time": "55 sec",
        "script": """Rigorous scientific research requires addressing limitations honestly:
First, Acoustic Scope: our audio evaluation used a single primary speaker. While controlled against the DREGON dataset, real-world deployment requires testing multi-speaker accents and outdoor wind turbulence.
Second, Latency Gaps: reflex latency was limited by audio framing buffers, while the cognitive path exceeded its budget due to uncached prompt prefill.
Third, the Simulation-to-Reality Gap: our collision-free guarantee in kinematic simulation utilized an integrator clamp. Physical airframes require reformulating collision avoidance at the thrust and acceleration level.
Fourth, Model Abstention: when audio was heavily garbled, the fine-tuned model tended to guess plausible commands rather than abstaining with `unknown`.
These documented limitations directly shape our future engineering roadmap."""
    },
    32: {
        "time": "55 sec",
        "script": """Our future work follows a three-phase roadmap:
In the short term, implementing KV-cache prefixing will save over 500 milliseconds of prefill latency, and log-probability confidence gating will enable safe abstention on noisy audio.
In the medium term, we will reformulate swarm collision avoidance using Control Barrier Functions at the motor acceleration level in aerodynamic simulation.
In the long term, we aim to deploy the pipeline onto physical Bitcraze Crazyflie drone swarms in field flight trials.
In closing, this project proves that formal grammars, efficient quantization, and a dual-path runtime make natural, safe voice control feasible on edge robotics.
I express my deepest gratitude to my supervisor, Professor Belkacem Khaldi, for his continuous guidance and support.
I sincerely thank the members of the jury for their time and evaluation, as well as the faculty of ESI-SBA, my colleagues, and my family.
Thank you for your attention. I am now ready for your questions."""
    },
    33: {
        "time": "20 sec",
        "script": """This backup slide summarizes our granular benchmark parameters, LoRA training hyperparameters, and statistical hypothesis tests. I welcome any questions regarding our experimental data, p-values, or architectural decisions."""
    }
}

def format_spoken_script(script_text):
    paragraphs = [p.strip() for p in script_text.strip().split("\n\n") if p.strip()]
    formatted_lines = []
    for i, p in enumerate(paragraphs):
        # Format blockquote
        clean_lines = [line.strip() for line in p.split("\n") if line.strip()]
        joined = " ".join(clean_lines)
        formatted_lines.append(f'  > "{joined}"')
        if i < len(paragraphs) - 1:
            formatted_lines.append('  >')
    return "\n".join(formatted_lines)

def update_slides_file(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find each slide block
    slide_pattern = r'(### Slide (\d+):[^\n]*\n)(.*?)(?=\n### Slide \d+:|\Z)'
    
    def replace_slide(match):
        header = match.group(1)
        num = int(match.group(2))
        body = match.group(3)

        if num not in SCRIPTS:
            return match.group(0)

        data = SCRIPTS[num]
        new_time = data["time"]
        new_script_text = format_spoken_script(data["script"])

        # Check for Presenter Notes section
        if "🗣️ Private Presenter Notes" in body:
            notes_sub_pattern = r'(\* \*\*Target Time\*\*:[^\n]*\n\* \*\*Spoken Script[^\n]*\n)(.*?)(\n\* \*\*|\n---|\Z)'
            
            def replace_notes_body(n_match):
                prefix_lead = f"* **Target Time**: `{new_time}`\n* **Spoken Script (Concise & Precise)**:\n"
                tail = n_match.group(3)
                return prefix_lead + new_script_text + tail

            new_body = re.sub(notes_sub_pattern, replace_notes_body, body, flags=re.DOTALL)
            return header + new_body
        else:
            return match.group(0)

    updated_content = re.sub(slide_pattern, replace_slide, content, flags=re.DOTALL)

    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(updated_content)

    print(f"Updated {md_path} successfully!")

if __name__ == '__main__':
    md_file = Path('/home/kahia-tayeb/PFE/presentation/SLIDES_AND_NOTES.md')
    update_slides_file(md_file)
