### Exp-4: formation validation (RQ3)

150 trials: 50 per formation, 60 s each, 50 Hz, seed = trial index x 42, initial positions N(0, 0.5 m) about the centroid.

| Formation | n | FA (mean +/- sd) | FA min | meets NFR-13 | conv. rate | conv. median [IQR] s | collisions | clamp |
| :--- | ---: | :--- | ---: | ---: | ---: | :--- | ---: | ---: |
| circle | 50 | 1.000 +/- 0.000 | 1.000 | 50/50 | 1.00 | 4.06 [4.00, 4.08] | 0 | 150 |
| line | 50 | 1.000 +/- 0.000 | 1.000 | 50/50 | 1.00 | 3.26 [3.21, 3.32] | 0 | 141 |
| wedge | 50 | 1.000 +/- 0.000 | 1.000 | 50/50 | 1.00 | 2.30 [2.21, 2.38] | 0 | 141 |

**NFR-12 --- collisions: 0 observed** across all trials (a collision is a pair closer than 0.35 m). The closest approach recorded was 0.800 m against a clamp distance of 0.8 m. The hard geometric clamp at the integrator resolved 432 pair violations, which is the honest companion figure: each one is an occasion on which the artificial potential field alone did not keep two drones apart. The claim is therefore zero collisions *observed*, backed by that clamp --- not zero collisions guaranteed by APF, which with discrete timesteps and bounded acceleration would be unprovable.

**NFR-13 --- FA >= 0.85** (fraction of drones within tau = 0.5 m of their *assigned* slot, averaged over the final 5 s).

One-way ANOVA on formation accuracy: **not applicable** --- every trial produced 1; there is no variance to partition.
    This is a saturated metric, and it should be read as a statement about the protocol rather than about the controller. Table 15 fixes the initial dispersion at N(0, 0.5 m) and the trial length at 60 s; against a formation several metres across, that leaves every run converged within the first few seconds and roughly 55 s of settled flight for FA to average over. The pre-registered protocol is reported as pre-registered rather than made harder after the fact to manufacture variance --- but the honest reading is that FA does not discriminate between these three formations, and convergence time is the metric that does.

One-way ANOVA on convergence time across formations: F(2, 147) = 3500.687, p = 1.032e-124.
  - Tukey HSD circle vs line: difference +0.795 s [0.745, 0.845], p = 2.154e-14
  - Tukey HSD circle vs wedge: difference +1.755 s [1.705, 1.805], p = 2.154e-14
  - Tukey HSD line vs wedge: difference +0.960 s [0.910, 1.010], p = 2.154e-14

Trials are replicates, not a second factor: the design is one-way (Table 15).
