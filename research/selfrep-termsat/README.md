# selfrep-termsat: with a saturating goods market, how much does a resale value for the fleet change when the shop stops copying?

Follow-up to `selfrep-terminal` and `selfrep-satmarket` in the self-replicating manufacturing track (`PROJECTS.md`, track 1), taking the "combine the terminal value with the saturating market (DP with a terminal reward)" next step that `selfrep-terminal` lists. Produced with AI assistance (Claude).

**Builds on.** `research/selfrep-satmarket` (its fluid model, Euler step, bang-bang search and DP; imported by relative path, not copied), `research/selfrep-terminal` (the terminal-value objective and the closed form `T - ts = 1/k - s/a` for linear revenue) and `research/selfrep-growth` (per-copy work `W` = 50.0 h), from `research/selfrep-closure` (RepRap Prusa Mendel; Jones et al., "RepRap – the replicating rapid prototyper", *Robotica* 29(1), 2011, <https://doi.org/10.1017/S026357471000069X>). Backward dynamic programming is the method of Bellman (1957), *Dynamic Programming*, Princeton University Press. The question follows von Neumann (1966) and Freitas and Merkle (2004). No paper's result is reproduced. This project builds on none of the CU Boulder groups in `prompt.md` and claims no connection to them.

## Method
- **Model.** Fleet `n`, copy share `u`, `n' = k u n` with `k = 1/W` (no failures), goods revenue `R(g) = a c (1 - exp(-g/c))` for `g = (1 - u) n`, as in `selfrep-satmarket`. Objective: revenue over T = 600 h plus `s` x (machines at T). `s` is swept as a fraction of `a/k` (= 50 per machine), the never-switch threshold of the linear market in `selfrep-terminal`. All inputs are assumed.
- **DP.** `src/selfrep_termsat/model.py` repeats the `selfrep-satmarket` backward induction (400 log-spaced fleet points, 21 control levels) with terminal condition `V_T(n) = s n`. One change: a successor beyond the top of the fleet grid is valued by linear extrapolation in `n`. With the flat edge value of `selfrep-satmarket`, a first run gave a DP policy that was beaten by plain bang-bang (up to 0.7%) and a table value 9-10% off, so the edge handling was changed and the experiment rerun; the results below are from the rerun only.
- The reported DP policy is the feedback rule read from the table and simulated with the same Euler scheme as the bang-bang search (1 h grid), so the two J values are comparable.

## Reproduce
```bash
cd research/selfrep-termsat
python3 -m unittest discover -s tests -v   # 4 tests, <1 s (needs ../selfrep-satmarket)
python3 experiments/run.py                 # about 30 s; writes experiments/results.txt
```

## Results (from `experiments/results.txt`; T = 600 h, a = 1, no failures, all assumed)
- **Linear market (`c` = infinity) reproduces `selfrep-terminal`.** The DP switch is at 550, 562, 575 h for `s` = 0, 12.5, 25 (0, 0.25, 0.5 a/k) and at 599-600 h for `s` >= a/k, with 0-1 h of interior control; bang-bang matches the DP policy to the printed precision.
- **Saturation plus a resale value makes copying to the end the optimum at low `s`.** At `c` = 1000 and 100, already `s` = 12.5 (0.25 a/k) gives a DP policy that copies throughout (u < 0.5 only from t = 600 h), while at `s` = 0 the switch is at 398 h and 287 h. The reason is the scale: the fleet reaches about 1.4 x 10^5 machines, so `s N_T` (about 1.8 x 10^6) is far larger than the revenue a market of capacity 1000 can pay over the whole horizon (at most `a c T` = 6 x 10^5).
- **Intermediate case.** At `c` = 10^4, `s` = 12.5 and 25 give an interior ramp of 66 h and 25 h at the end, and bang-bang reaches 93.9% and 99.5% of the DP policy; at `s` >= a/k bang-bang is the optimum again. At `s` = 0 the ramp is 90 h and bang-bang 95.5%, as in `selfrep-satmarket`.
- **DP accuracy.** The DP policy is at least as good as best bang-bang in every row. The table value `V0` is 5.1-5.8% above the simulated policy value wherever the fleet nears the grid top (the linear extrapolation and 1 h Euler step overstate it), and within 0.3% for `s` = 0 and `c` <= 10^4. This matches the interpolation error reported in `selfrep-satmarket` for steep value functions. The DP optimum is the optimum of the discretised problem, not a proof about the continuous one; the last time step touches the grid edge and its control is not meaningful.

## Limitations
- Stylised. `s`, `a`, `c`, `W` are assumptions. The result that a small `s` dominates in a saturating market is driven by valuing 10^5 machines at a fixed price each, which no real used-machine market would pay: a resale market saturates too (the next step).
- Cash is free, one machine type, continuous fleet, no wear-out, no failures in the sweep.
- Only `c` in {infinity, 10^4, 10^3, 10^2} and five `s` values; the shapes between them are not mapped. The DP table error above means margins under about 5% in `V0` should not be read as rankings.

## Next steps
Make the resale price fall with the number of machines offered (a saturating terminal value `S(n)`), which should restore an interior switch; add the cash constraint (two-state DP); map `c` between 10^3 and 10^4.

## Owner steps
- Find the real resale value of a used RepRap-class printer, and the size of that market, with a source and date for each price.
- Replace the assumed goods value `a` and market capacity `c` with measured ones, as for `selfrep-satmarket`.

## Outside dependencies (vitamins)
Python standard library only, plus the sibling `selfrep-satmarket`, `selfrep-growth` and `selfrep-closure` source trees (relative paths). The vitamins of the printers it describes are those of `selfrep-closure`.
