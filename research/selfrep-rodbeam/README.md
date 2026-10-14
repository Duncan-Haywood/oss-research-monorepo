# selfrep-rodbeam: could a printed or wooden rod replace the steel smooth rod of a RepRap?

Follow-up to `selfrep-redesign` (track 1, `PROJECTS.md`), whose "Next steps" asked for a mechanical model behind its assumed penalties. This project replaces the "wooden rods" penalty with a beam-bending calculation: how much does an 8 mm rod sag under the carriage if it is steel, birch dowel or printed PLA? Produced with AI assistance (Claude). Computed only; no real rod was tested.

**Builds on.** `selfrep-redesign` and `selfrep-closure` in this repository. Beam theory is textbook Euler–Bernoulli bending (for example Timoshenko and Gere, *Mechanics of Materials*); the formulas used are the standard centre-load and uniform-load deflections. Wood properties are only taken as an assumed range (see the USDA Forest Products Laboratory *Wood Handbook*, FPL-GTR-190, for real species data; I did not copy values from it). It builds on none of the labs in `prompt.md`.

## Method
- `src/selfrep_rodbeam/beam.py`: mid-span deflection of a solid round rod under a central point load, simply supported (F L³ / 48EI) or both ends clamped (F L³ / 192EI), plus self-weight sag, the equal-stiffness diameter (d ∝ E^−1/4) and the minimum diameter for a sag limit.
- **Assumed inputs, not measurements:** Young's modulus ranges (steel 190–210 GPa, birch dowel along the grain 9–15 GPa, printed PLA 1.5–3.5 GPa), a 400 mm unsupported span, carriage loads of 0.25 and 0.5 kg, and sag limits of 0.05 and 0.2 mm. Printed parts are anisotropic and print-dependent; one isotropic modulus is a crude stand-in.
- "Passes" probabilities draw E uniformly over each range (2000 draws, seed 0).

## Reproduce
```bash
cd research/selfrep-rodbeam
python3 -m unittest discover -s tests -v     # 6 tests, standard library only
python3 experiments/run.py                   # writes experiments/results.txt
```

## Results (from `experiments/results.txt`)
- At 8 mm and the light load, centre sag on the assumed 400 mm span is 0.081 mm (steel), 1.36 mm (birch) and 6.5 mm (PLA), simply supported; clamped ends divide these by 4.
- Rod diameter that matches an 8 mm steel rod's stiffness: about 16 mm for birch (15.3–17.4 over the modulus range) and about 24 mm for PLA (22.0–27.2).
- Against a 0.2 mm sag limit with the light load, the 8 mm steel rod passes in all draws, while 8 mm birch and PLA rods pass in none. Birch needs about 13 mm and PLA about 19 mm (simply supported), 9 and 13.5 mm clamped.
- Even steel exceeds a 0.05 mm limit at 8 mm on this span when simply supported, so the absolute limits matter as much as the ratios; the ratios (birch about 17×, PLA about 80× the steel sag at equal diameter) do not depend on them.
- Implication for `selfrep-redesign`: its wooden-rod substitution implicitly assumes a rod of a different size would fit the printed or bought linear bearings. Under these assumptions a like-for-like 8 mm wooden or printed rod would sag far more than steel, and a stiff-enough one is about twice (wood) or three times (PLA) the diameter, which would need different bearings or a shorter span. The penalty of 0.3–0.9 in that project is not derived from this model.

## Limitations
- Static, linear, single point load only. No bearing contact, friction, creep (PLA creeps), humidity (wood), buckling, vibration or shear deformation. Moduli, loads and limits are my assumptions with no measured data.
- Real X rods are usually shorter, doubly supported and carry less than a free span; the 400 mm centre load is a pessimistic stylised case. Hollow or ribbed printed sections and printed stiffening are not modelled.
- Results are about stiffness only; wear of a printed rod against bearings is not considered.

## Next steps
Measure the sag of real rods (owner step) and fit the modulus; add a beam-with-two-supports geometry matching the Prusa Mendel X axis; feed the stiffness requirement back into `selfrep-redesign` as a constraint replacing its penalty.

## Owner steps
- Hang a known mass at mid-span of a steel rod, a dowel and a printed rod on a measured span with a dial gauge; replace the assumed moduli with the measured ones.

## Outside dependencies (vitamins)
Python standard library only.
