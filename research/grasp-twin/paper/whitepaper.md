# How hard to grip: what a wrong-friction digital twin does to a robot's grasp force

*Status: stylised analytical study with simulation checks; no real friction data, no hardware. All numbers are in `experiments/results.txt`.*

## Abstract
A manipulator lifts an object with a two-finger grasp and picks a grip force `N` in a digital twin. The object slips iff `2μN < L`, `L = m(g+a)`. Real friction `μ` varies per object and surface; we take it lognormal with log-sd `s`. With cost `J(N) = c_d·P(slip) + c_f·N`, the change of variable `N = N0·e^{−sz}`, `N0 = L/(2μ0)`, makes `P(slip) = Φ(z)` and gives a closed-form optimum `z* = s − √(2 ln(1/(ρ√(2π))))`, `ρ = s·c_f·N0·e^{−s²/2}/c_d`. In the base case (m=0.5 kg, μ0=0.5, s=0.35, c_f·N0/c_d=0.064) the optimum grips 107% above the median slip threshold and drops 1.9% of objects. A twin with a single deterministic friction value `μ_T` has a corner optimum: it grips exactly at its own slip threshold, so the real drop probability is `Φ(b/s)` with `b = ln(μ_T/μ0)`: 0.50 for a median-matched twin, `Φ(s/2)=0.57` for a mean-matched one, 0.87 at 1.5× too-high friction. A randomised twin of width `s_T` has real drop probability `Φ((b + s_T z_T)/s)` exactly. Adding a width can cancel a bias on one task (b=0.4 fixed by s_T=0.64) but the compensation does not transfer to other masses (regret 9% at 0.1 kg, 14% at 4 kg). Setting the twin from `n` real friction measurements by a plug-in quantile inflates the real drop probability, exactly, by 2.7× at n=10 and δ=1%, and needs 56 measurements to be within 25% of the target.

## 1. Motivation and prior work
Simulators represent contact friction by a single Coulomb coefficient per material pair, while real coefficients vary with surface condition, contamination and wear. Dynamics randomisation (Tobin et al. 2017; Peng et al. 2018) is the standard remedy; here we ask what it buys *exactly* in the simplest grasp where the answer is closed-form. The question sits in the digital-twin and sim-to-real-for-manipulation direction of the HIRO Group (<https://hiro-group.ronc.one/>) and the CAIRO Lab (<https://cairo-lab.com/>); no specific paper of either is reproduced and nothing here is affiliated with or endorsed by them. Force-closure with Coulomb friction is textbook (Murray, Li & Sastry 1994). The finite-data result is the predictive-quantile problem (Geisser 1993).

## 2. Model
Load `L = m(g+a)` at peak lift acceleration; two contacts; slip iff `2μN < L` (validated against a time-stepped Coulomb simulation, §5.1). Real `ln μ ~ N(ln μ0, s²)`. `J(N) = c_d P(slip) + c_f N`. Twin: friction `lognormal(ln μ_T, s_T)`, `s_T = 0` deterministic.

## 3. Results
**Optimal force.** With `z = (ln N0 − ln N)/s`, `J(z) = c_dΦ(z) + c_f N0 e^{−sz}` and `J'(z) = c_dφ(z) − s c_f N0 e^{−sz}`. Using `φ(z)e^{sz} = e^{s²/2}φ(z−s)`, `J'=0` iff `φ(z−s) = ρ`, with roots `s ± √(2 ln(1/(ρ√(2π))))`. The lower root is the minimiser (`J'` goes − to + to −), and it beats not gripping (`J=c_d`) only if `J(z*)<c_d`. Matched to a 40 000-point grid to 4 decimals (z* = −2.0750).

**Corner theorem.** As `s_T→0`, `s_T z_T→0`: the deterministic-friction twin grips at `L/(2μ_T)` provided `c_d > c_f L/(2μ_T)`, otherwise never grips. Real drop probability `Φ(b/s)` is independent of the cost ratio. Table (base case): b = −0.4/0/0.4/0.6 gives drop 0.13/0.50/0.87/0.96 and real cost 0.222/0.564/0.916/0.992 against an optimum of 0.151. A sim-to-real gap of "friction is off by 20%" is not a 20% problem: it decides whether half the objects fall.

**Randomised twin.** Real drop `Φ((b + s_T z_T)/s)` matches the direct computation to four decimals for `s_T ∈ [0.05, 1]`. With b=0 the regret is minimised at `s_T = s` (0, by construction) and is asymmetric: too narrow (0.2) costs 23% of `J*`, too wide (0.5) 7%. With b=0.4 (twin friction 1.49× too high) `s_T=0.35` still drops 13.8% and costs +53%; the best width is 0.64.

**Compensation does not transfer.** The width 0.64 that zeroes regret on the 0.5 kg task gives regret 8.7% (0.1 kg), 2.0% (0.25 kg), 2.3% (1 kg), 8.8% (2 kg), 14.3% (4 kg; real drop 0.50). The bias and the width move the force differently as the load and the cost ratio change, so a width tuned on one object hides, but does not repair, a wrong mean.

**Safety factors.** Scaling a deterministic twin's force by `k` gives drop `Φ((b − ln k)/s)`, so 1% needs `k = exp(b − s·z_{0.01})`: 2.26 (b=0, s=0.35), 3.37 (b=0.4), 9.59 (b=0.4, s=0.8). The common `k=1.5` gives drop 12% at b=0, s=0.35, and 49% at b=0.4. Real cost at b=0.4: k=1.5: 0.558; k=2: 0.287; k=3.37: 0.155; optimum 0.151.

**Finite friction data.** Setting the slip threshold at `ȳ + k·ŝ` (on `ln μ`) from `n` real measurements gives expected drop probability `E Φ(kŝ/s/√(1+1/n))`, `ŝ²/s² ~ χ²_{n−1}/(n−1)` (one-dimensional integral; matches Monte Carlo to ±0.0002 for n≥10). At `k = z_δ` and δ=1%: n=5, 10, 20, 50, 100 give 5.05%, 2.69%, 1.75%, 1.28%, 1.13%; the inflation is fixed by `n` alone, not by the twin's mean error. Corrected multipliers `k_n` reaching exactly 1%: −4.105, −2.959, −2.602, −2.429 (plug-in −2.326). At δ=5% the inflation is milder (1.51× at n=10). The second-order expansion in `1/n` is off by 11% at n=10 and 21% at n=5 for δ=1% (0.0240 and 0.0401 vs exact 0.0269 and 0.0505), so it should not be used for rare-event targets at small `n`.

## 4. Limitations
Scalar static load; no grasp dynamics beyond the slip threshold; no friction-cone geometry, torsional friction, compliance, or sensing of contact; real friction assumed lognormal and independent per grasp with a known scale `s` and load (the lognormal `s` is a chosen value, not a measurement); the twin is assumed to solve its own expected-cost problem exactly rather than learn by RL; no hardware or real data. The dynamic simulator checks the static threshold to 1%; it does not validate the physical assumptions.

## 5. Reproduce
`PYTHONPATH=src python3 -m unittest discover -s tests -v` (7 tests, ~1 s); `PYTHONPATH=src python3 experiments/run.py > experiments/results.txt` (~1 min).

## 6. Next steps
Measure real friction spread on a pair of surfaces and compare with the lognormal assumption; extend to a friction-cone/torque model; learn `N` by policy gradient in the randomised twin and compare to the closed form; pair with the audit machinery of `twin-audit` to certify a twin's friction pessimism online.

## References
```bibtex
@book{murray1994mathematical, author={Murray, Richard M. and Li, Zexiang and Sastry, S. Shankar}, title={A Mathematical Introduction to Robotic Manipulation}, publisher={CRC Press}, year={1994}}
@inproceedings{tobin2017domain, author={Tobin, Josh and Fong, Rachel and Ray, Alex and Schneider, Jonas and Zaremba, Wojciech and Abbeel, Pieter}, title={Domain Randomization for Transferring Deep Neural Networks from Simulation to the Real World}, booktitle={IROS}, year={2017}}
@inproceedings{peng2018sim, author={Peng, Xue Bin and Andrychowicz, Marcin and Zaremba, Wojciech and Abbeel, Pieter}, title={Sim-to-Real Transfer of Robotic Control with Dynamics Randomization}, booktitle={ICRA}, year={2018}}
@book{geisser1993predictive, author={Geisser, Seymour}, title={Predictive Inference: An Introduction}, publisher={Chapman \& Hall}, year={1993}}
```
