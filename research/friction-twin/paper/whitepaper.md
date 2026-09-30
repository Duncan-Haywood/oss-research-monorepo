# A twin with no dry friction says the loop converges; stiction makes the real one stick-slip

*Stylised: a scalar discrete PI loop on a massless load with dry friction; pure Python, every number is from `experiments/results.txt` (deterministic, about 1 s). The "real" system is itself simulated; no lab or field data. Negative and out-of-model results are marked.*

## Question
Joints, stages and gimbals have stiction: a breakaway force `fs` larger than the sliding (Coulomb) force `fc`. A twin that models only viscous damping predicts that a stable linear PI loop converges to zero error. Does the real loop converge, how large is the residual motion, which part of the friction causes it, and what does a twin need to predict it?

## Model
Load position `x` with unit viscous gain, driven through dry friction. Stuck: it moves only if `|u| > fs`, then slides in the sign `s` of `u`. Sliding: `x+ = x + u − s·fc` while `s·u > fc`, otherwise it sticks. Loop: `z+ = z + x`, `u = −(kp·x + ki·z+)`. For `fs = fc = 0` (the twin) the characteristic polynomial is `z² − (2−kp−ki)z + (1−kp)`; the twin claims convergence when its spectral radius is below 1. With `fs = fc` friction is a deadband on the control signal; the stiction drop is `d = fs − fc`. The map is piecewise linear and positively homogeneous of degree 1 in `(x, z, fs, fc)`. Amplitude is half the peak-to-peak of `x` over a tail window.

## Results
1. **The twin's convergence claim fails, and Coulomb-only friction does not fix it.** For five gain settings with twin radius 0.707–0.894 (twin `|x|` below 1e-123 after 3000 steps), a Coulomb-only twin (`fs=fc=0.5`) also comes to rest (amplitude 0). The real loop with `fs=1, fc=0.5` from `x0=10` hunts at amplitude 0.4810 / 0.7315 / 0.9182 / 0.7073 / 0.4744 for `(kp,ki)` = (0.5,0.1), (0.3,0.05), (0.2,0.2), (0.3,0.1), (0.5,0.2), with 407–1449 stuck intervals in the last 20000 steps. The cause is the stiction drop, not the friction level: the drop `d=0` case comes to rest from all three starts tried.
2. **The cycle is stick-slip, not a sinusoid.** Stuck intervals average 9.7–43 steps with relative spread 0.05–0.09, and each slide lasts 3.0–6.0 steps on average. The waveform is long flat dwells with a short slide, so a first-harmonic (describing-function) analysis, as used in `backlash-twin`, is not attempted here.
3. **Amplitude is set by the stiction drop, with a gain-dependent constant.** At `(0.5,0.1)`, amplitude/`d` is 0.91–0.98 for `d` = 0.01 … 0.5 and 0.9467 at `d=1` (200000 steps, last 20000; the three starts agree within 0.04 at every `d`). It is not exactly linear: the ratio moves by about 10% across two decades of `d`. At `fc=fs/2` the ratio is about 0.96 (`kp=0.5`), 1.46 (`kp=0.3, ki=0.05`) and 1.84 (`kp=0.2, ki=0.2`); no closed form for it is derived.
4. **Homogeneity.** Rescaling `fs, fc, x0` by a power of two (2⁻⁷, 2⁶) reproduces the trajectory bit for bit (max deviation 0). For scalings that are not powers of two (0.01, 100) the trajectories diverge pointwise (deviation 0.92, 0.91 of `fs` at 5000 steps) because the stick/slip decisions amplify rounding, yet the cycle amplitude stays close: amplitude/`fs` = 0.4793 / 0.4810 / 0.4765 for `fs` = 0.01 / 1 / 100. The claim is scale invariance of the statistic, not of individual orbits.
5. **Start and integral gain decide whether the loop hunts at all (negative result for single-run validation).** At `kp=0.5, fc=fs/2`, for `ki` = 0.01 and 0.02 the loop converges from `x0` = 10 and 2 but hunts from 0.5 (0.4861, 0.4849); at `ki=0.05` it hunts from 10 and 0.5 but converges from 2; for `ki ≥ 0.1` it hunts from every start (0.4721–0.4977). Once hunting, the amplitude is nearly independent of `ki` (0.4721–0.4977 for `ki` 0.1–0.4); `ki` changes the period, not the amplitude.
6. **Calibration sensitivity.** With true `d=0.5` (real amplitude 0.4801), a twin that has the stick-slip structure but assumes `d̂` = 0 / 0.1 / 0.25 / 0.4 / 0.6 / 0.75 predicts amplitude 0 / 0.0921 / 0.2315 / 0.3686 / 0.5725 / 0.7246, i.e. −100% / −81% / −52% / −23% / +19% / +51%. The prediction error is nearly proportional to the error in the drop, so a twin must identify `fs − fc` (a difference of two friction levels) to the relative precision it wants in the amplitude.

## Limitations
Massless load (no inertia, so no velocity-dependent overshoot of the slide), constant friction levels (no Stribeck curve, no dwell-time dependence, no presliding), no noise, single loop structure, five gain settings for the amplitude table and one for the sweeps; deterministic simulation, so no sampling error, but generality across plants is untested. Amplitude is measured over a tail window and varies slowly across cycles at small `d` (the 3000-step window under-reports it: at `d=0.02` the ratio was 0.86–0.90 with a 3000-step and 0.91–0.95 with a 20000-step window), so the ratios in result 3 carry roughly ±0.03. Nothing here is evidence about a particular actuator.

## Next steps
Closed form for the gain-dependent constant in result 3 (the slide map is piecewise linear); adding inertia and a Stribeck curve; dither and integrator-freeze compensation (companions `deadband-noise-twin` and `deadband-twin`); identifying `fs − fc` from logged data and a certified amplitude bound (link to `twin-certification`).

## References
- Armstrong-Hélouvry, B., Dupont, P. & Canudas de Wit, C. (1994). A survey of models, analysis tools and compensation methods for the control of machines with friction. *Automatica* 30(7), 1083–1138.
- Olsson, H., Åström, K. J., Canudas de Wit, C., Gäfvert, M. & Lischinsky, P. (1998). Friction models and friction compensation. *European Journal of Control* 4(3), 176–195.
- Åström, K. J. & Hägglund, T. (1995). *PID Controllers: Theory, Design, and Tuning*, 2nd ed. ISA.
- Khalil, H. K. (2002). *Nonlinear Systems*, 3rd ed. Prentice Hall.
- Zhao, W., Queralta, J. P. & Westerlund, T. (2020). Sim-to-real transfer in deep reinforcement learning for robotics: a survey. *IEEE SSCI*.
