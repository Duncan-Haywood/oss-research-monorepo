# garment-twonodegate

Follow-up to [`garment-twonodesteady`](../garment-twonodesteady) (track 6, `PROJECTS.md`), taking an item from its next steps: "test the infrared-gating textile bounds of `garment-thermal` section E under both choice sets and at steady state." Question: do the bounds for a textile whose infrared transmittance can switch between 0.15 (closed) and 0.8 (open), found in `garment-thermal` with that project's own two-node model after 3 h, hold when the model's design choices are switched to those of `pythermalcomfort` 4.6.1 and when the model is run to steady state? Everything is a model on a CPU; no person or fabric was measured. Produced with AI assistance (Claude).

**Builds on.** `research/garment-thermal` (section E, the gated-textile bounds), `research/garment-twonodeoptics` (the switchable two-node model with optics, used unchanged) and `research/garment-twonodesteady`; through them the `pythermalcomfort` package (MIT; 4.6.1), whose `two_nodes_gagge` documents itself as the model of Gagge et al. (1986), which I did not read. It builds on none of the CU Boulder groups in `prompt.md` and claims no connection to them.

**Citation check.** No new source. The 0.15 and 0.8 bounds are `garment-thermal`'s own round numbers, not measurements of any textile.

## Method
For two still rooms (air = radiant temperature 31 C and 16 C, 50% rh, v 0.1 m/s) at 1.2 met and 0.5 clo, `garment-twonodeoptics`' `flex.run` is run with infrared transmittance 0.15 (closed) and 0.8 (open) under all-`ours` and all-`ref` design choices, for 180 min and for 1440 min (steady state, checked against 2880 min). No switching dynamics: each state is held for the whole run, so these are bounds, as in `garment-thermal`. The model's moisture permeability is whatever `flex.run` fixes; sweat mass is not tracked there, so evaporative loss (W/m2) and wettedness stand in for `garment-thermal`'s sweat grams.

Tests (`tests/`, 11 pass): opening the gate lowers skin temperature in both rooms under both choice sets; in the hot room it lowers wettedness and evaporative loss; steady state is reached by 1440 min; the cool-room skin-temperature effect agrees between choice sets within 0.1 C.

## Reproduce
```bash
python3 -m pip install numpy scipy pytest pythermalcomfort==4.6.1
python3 experiments/run.py      # writes experiments/results.txt
python3 -m pytest -q
```

## Results (from `experiments/results.txt`)
- **Direction and size of the bounds are the same under both choice sets.** Opening the gate (0.15 to 0.8) lowers skin temperature by 0.25 C (`ours`) and 0.20 C (`ref`) at 31 C, and by 1.45 C and 1.43 to 1.46 C at 16 C. Core temperature moves by 0.02 to 0.05 C. At 31 C, wettedness falls by 0.039 (`ours`) and 0.037 (`ref`) and evaporative loss by 6.2 and 5.5 W/m2. These agree in sign and size with `garment-thermal` (skin 35.25 vs 35.00 C hot, 27.03 vs 25.57 C cool; that project's figures differ by up to 0.02 C from mine since its clothing and body constants are not identical to `flex.run`'s defaults).
- **Absolute levels depend on the choices; the gate effect does not.** At 31 C the `ref` choices put skin about 0.35 C lower and wettedness about 0.04 higher than `ours`; at 16 C `ref` skin is 0.15 C warmer at steady state.
- **Three hours is already steady.** In these rooms the 3 h and 1440 min end states are identical to the printed precision under `ours` and `ref` at 31 C, and under `ours` at 16 C; only `ref` at 16 C is still moving at 3 h (skin 27.62 C at 3 h, 27.15 C at steady state, a 0.47 C drift), the same slow transient that `garment-twonodesteady` found. The cool-room open-minus-closed difference changes by 0.03 C or less between 3 h and steady state.
- Reading: the gating bounds of `garment-thermal` are not an artefact of its design choices or of the 3 h horizon in this model. A real gate would depend on switching threshold and speed, which are not modelled.

## Limitations
Stylised: two rooms, one clothing level and metabolic rate, fixed 70 kg body, held-constant gate states, no sweat mass, no moisture in the cloth, `ref` optics are my construction (no reference has optics). Agreement between two implementations of one model family says nothing about real people or fabrics.

## Next steps
Read Gagge et al. (1986); add a published measurement table; model a switching gate with a threshold on skin temperature and compare it with the bounds.

## Owner steps
None required.

## Outside dependencies (vitamins)
Python, numpy, scipy, pytest, `pythermalcomfort` 4.6.1 (through `garment-twonodeoptics`) and that project's model. The transmittance bounds come from `garment-thermal`.
