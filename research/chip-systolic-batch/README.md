# chip-systolic-batch: does a larger batch let a systolic array beat MAC lanes on a tiny quantised MLP? (negative at 4 to 16 vectors)

Follow-up to `chip-systolic` in the LLM chip-design-loop track (`PROJECTS.md`, track 3), answering its first "Next step". The same Python generator emits Verilog for an R x C output-stationary systolic array running the 8-8-4 integer MLP on a batch of R vectors, now for R = 4, 8, 16. Each design is simulated in Icarus Verilog (must match the integer NumPy reference bit for bit and in cycle count) and scored with Yosys against `chip-accel`'s MAC-lane engine, which processes the batch as R sequential runs. Produced with AI assistance (Claude). Preliminary and small: one toy network, one seed, one tool version, one generic-gate script. No LLM is in this loop.

**Builds on.** Nothing from the CU Boulder groups in `prompt.md`; no connection is claimed. Systolic dataflow: H. T. Kung, "Why systolic architectures?", *IEEE Computer* 15(1):37-46, 1982, <https://doi.org/10.1109/MC.1982.1653825> (bibliographic details checked by search; paper not read in full). `model.py`, `baseline_gen.py`, `gen.py` and `flow.py` derive from `research/chip-systolic` and `research/chip-accel` (same author, MIT).

## Reproduce
```bash
sudo apt-get install -y yosys iverilog      # Yosys 0.33, Icarus 12.0 here
pip install numpy
cd research/chip-systolic-batch
PYTHONPATH=src python -m unittest discover -s tests     # about 1 minute
PYTHONPATH=src python experiments/run.py                # about 25 minutes; rewrites experiments/results.txt
```

## Results (from `experiments/results.txt`)
The RTL matched NumPy on all 32 checked vectors for all 14 systolic configurations, with every cycle count equal to `cycles(C, R)`. Configurations with R x C > 32 were skipped: Yosys was OOM-killed (about 14 GB) on 16x8, so the grid is incomplete.

cells x cycles / R (per vector; lower is better) at the best point of each design:

| WB | R | best systolic | best MAC-lane |
|---|---|---|---|
| 4 | 4 | 4x4: 77608 | P=4: 48546 |
| 4 | 8 | 8x4: 100462 | P=4: 48546 |
| 4 | 16 | 16x2: 171475 | P=4: 48546 |
| 6 | 4 | 4x4: 153137 | P=4: 84100 |
| 6 | 8 | 8x4: 239835 | P=4: 84100 |
| 6 | 16 | 16x2: 326828 | P=4: 84100 |

- **Negative result.** A larger batch does not rescue the array here: its per-vector cost rises with R (1.6x to 3.9x worse than the best MAC-lane engine), whereas the sequential MAC-lane engine's per-vector cost is constant by construction.
- Latency still favours the array (for example 8x4: 59 cycles against 160 for P=8 on 8 vectors, at 4 bits) but at 8x the cells (13622 against 1674 for P=4 at 4 bits).
- Likely cause (not isolated): the array's PE count and flip-flops grow with R, since rows are batch rows, while fan-in stays 8 so fill and drain is a large share of each tile. The comparison is not like for like in silicon: a MAC-lane engine replicated R times would be the fairer area-matched baseline, which this project does not score. A fan-in sweep was not run.

## Limitations
- One 8-8-4 network, one seed, 4 and 6 bit weights only (8 bit omitted for runtime). Incomplete grid (see above). Gate counts from one generic ABC script; no timing, power or layout. MAC-lane figures are `cycles(P) x R` from the verified `chip-accel` formula, not re-simulated. Nothing here describes a fabricated chip.

## Next steps
Sweep fan-in (wider first layer) rather than batch; score a replicated-MAC-lane baseline; weight-stationary variant; a stubbed `ANTHROPIC_API_KEY`-gated proposer under the `chip-ppa-loop` equivalence gate.

## Outside dependencies
Yosys and Icarus Verilog (apt), NumPy (pip). No LLM API, OpenROAD or PDK.
