# How hard to grip: what a digital twin with the wrong friction law does to a robot's grasp force

Pure Python, no dependencies. A two-finger grasp holds an object iff `2μN ≥ L`, `L = m(g+a)`; real friction `μ` is lognormal with log-sd `s`, and the cost is `J(N) = c_d·P(slip) + c_f·N`. Substituting `N = N0·e^{−sz}` (`N0 = L/(2μ0)`) makes `P(slip) = Φ(z)` and gives a closed-form optimal force `z* = s − √(2 ln(1/(ρ√(2π))))`. Results, all from `experiments/results.txt`: in the base case the optimum grips 107% above the median slip threshold and drops 1.9% of objects (grid and a time-stepped Coulomb simulation agree). A twin with one deterministic friction value grips exactly at its own slip threshold, so the real drop probability is `Φ(b/s)`, `b = ln(μ_twin/μ0)`: 0.50 for a median-matched twin, `Φ(s/2)=0.57` for a mean-matched one, 0.87 for 1.5× too-high friction (regret 5× the optimum). A randomised twin of width `s_T` has real drop `Φ((b+s_T z_T)/s)` exactly; a wider twin can cancel a friction bias on one task (b=0.4 by s_T=0.64) but the fix does not transfer across masses (regret 9% at 0.1 kg, 14% at 4 kg). A 1.5× safety factor gives 12–49% drops where 1% needs 2.3–9.6×. Setting the twin's threshold from `n` real friction measurements by a plug-in quantile inflates a 1% drop target exactly to 2.7% at n=10 (56 measurements to be within 25%); a corrected multiplier fixes it, and the second-order expansion is off by 11–21% at small n. See `paper/whitepaper.md`.

```bash
cd research/grasp-twin
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 7 tests, ~1 s
PYTHONPATH=src python3 experiments/run.py                 # ~1 min; output in experiments/results.txt
```

**Builds on.** The digital-twin and sim-to-real-for-manipulation directions of the HIRO Group (<https://hiro-group.ronc.one/>) and the CAIRO Lab (<https://cairo-lab.com/>); no specific paper from either is reproduced and nothing here is affiliated with or endorsed by those labs. Coulomb-friction force closure follows Murray, Li & Sastry 1994, *A Mathematical Introduction to Robotic Manipulation*; dynamics randomisation follows Tobin et al. 2017 and Peng et al. 2018; the finite-data step is the predictive-quantile problem (Geisser 1993, *Predictive Inference*). Companion to the twin projects `twin-transfer`, `randomized-twin`, `handover-twin`.

Stylised: scalar static load, lognormal friction with a chosen (not measured) spread, no friction-cone geometry or compliance, the twin solves its own expected-cost problem exactly rather than learning, no hardware or real friction data. MIT.
