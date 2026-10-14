# selfrep-rodbeam: would a wooden or printed rod really replace the Mendel's steel rod?

Follow-up to `selfrep-redesign` (track 1, `PROJECTS.md`), taking up its first next step: replace one assumed penalty with a mechanical model. `selfrep-redesign` scored "wooden smooth rods" with an arbitrary penalty of 0.9. This project checks that substitution with a closed-form beam model. Produced with AI assistance (Claude). Computed only; no rod was built or tested.

**Builds on.** `selfrep-redesign` and `selfrep-closure` in this repository (Prusa Mendel bill of materials from the RepRap wiki; RepRap: Jones et al., *Robotica* 29(1), 2011, <https://doi.org/10.1017/S026357471000069X>). Euler-Bernoulli beam theory is textbook (for example Timoshenko, *Strength of Materials*). It builds on none of the labs in `prompt.md`.

## Method
- Each smooth rod is a simply supported beam with a point load P at midspan (the carriage): deflection = P L³ / (48 E I), I = π d⁴ / 64. Closed form, standard library only.
- Two questions per material: how much does an 8 mm rod deflect, and what diameter matches the 8 mm steel rod's deflection (d = 8 mm · (E_steel/E)^¼) or meets a tolerance?
- Then the matched rod is fed back into `selfrep-redesign`'s closure calculation, with rod mass from geometry and density instead of the earlier assumed 30 g.
- **Assumed inputs (mine, not measured):** 2.5 N per rod, 405 mm span, 0.2 mm tolerance, steel 200 GPa, densities 7850 / 700 / 1240 kg/m³ (steel / wood / PLA). Wood modulus along the grain is varied over 9.5–13 GPa. The 9.5 and 11.9 GPa figures are the green and 12%-moisture values for American beech in a web table I could not trace to its printed source (<https://amesweb.info/Materials/Youngs-Modulus-of-Wood.aspx>), and 13 GPa is a value reported for European beech in a journal table (<https://jwoodscience.springeropen.com/articles/10.1186/s10086-024-02157-x/tables/2>). The USDA *Wood Handbook* (FPL-GTR-190, 2010, chapter 5) is the standard source, but I did not check its table in this run. PLA modulus 2–3.5 GPa is a round range I assumed for printed bars; printed parts are anisotropic and often weaker.

## Reproduce
```bash
cd research/selfrep-rodbeam
python3 -m unittest discover -s tests -v   # 5 tests
python3 experiments/run.py                 # writes experiments/results.txt
```

## Results (from `experiments/results.txt`)
- An 8 mm steel rod deflects 0.086 mm under the assumed load. The same-size beech rod deflects 1.3 to 1.8 mm (15 to 21 times more) across the modulus range, and a PLA rod 4.9 to 8.6 mm (57 to 100 times).
- Matching steel stiffness needs a 15.8 to 17.1 mm beech rod (about 16 mm), or 22 to 25 mm in PLA. Meeting the 0.2 mm tolerance needs 12.8 to 13.9 mm in beech.
- The old penalty is not contradicted: the stiffness lost by a same-size dowel is 1 − E/E_steel = 0.94 at 11.9 GPa, close to the arbitrary 0.9, but this is a coincidence of two assumptions, not a validation.
- A matched beech rod set weighs 339 g (11.9 GPa) against 927 g for steel and 83 g for 8 mm beech. `selfrep-redesign`'s assumed 180 g for the six rods fits neither case.
- **A 16 mm rod does not fit the LM8UU bearings (8 mm bore)**, so the matched wooden rod only works together with printed bushings. In the closure calculation, matched beech plus printed bushings gives 49.0% / 31.7% / 20.8% (lines / mass / cost) against 43.1% / 22.4% / 15.9% baseline and 29 → 25 vitamin lines. The `selfrep-redesign` set of the same two substitutions gave 49.0% / 29.8% / 20.8%: line and cost closure are unchanged, mass closure differs by 1.9 points only because the rod mass is now geometric.
- Same-size dowel with LM8UU kept: 29 → 26 vitamin lines, 46.9% / 27.3% / 17.5%. Vitamin lines do not depend on rod diameter. The diameter only moves mass closure, and a heavier makeable rod raises it without the printer needing fewer vitamins.

## Limitations
- Static, single-load, linear-elastic beam only. No dynamics (a printer's carriage accelerates, so rod resonance and vibration matter), no wear at the bearing contact, no moisture or creep in wood, no straightness or surface finish, no shear deformation (non-negligible for a thick wooden rod), no fit tolerance of a printed bushing on a dowel.
- Every load, modulus, density and tolerance is assumed; the tolerance in particular sets which diameter "works".
- The conclusion "the substitution needs a 16 mm rod and printed bushings" holds only under these assumptions. A real redesign could shorten the span, add a middle support or use a box section.
- This does not decide whether the substitution is worth it: that needs the owner-step measurements below.

## Next steps
Replace the assumed bushing penalty the same way (contact stress and wear of printed bushing on dowel), then let a CMA-ES or LLM proposer choose span, diameter and supports in the `selfrep-redesign` loop.

## Owner steps
- Measure the deflection of a clamped beech dowel and a printed rod under a known weight, and replace the assumed moduli. Bill of materials: a 8 mm and a 16 mm beech dowel (price and date to be recorded when bought), a kitchen scale, a dial gauge.

## Outside dependencies (vitamins)
Python standard library plus the sibling `selfrep-closure` and `selfrep-redesign` source trees (relative paths). The wooden rods themselves (dowel stock) and the printer's filament are imported feedstock; motors, electronics, threaded rods and the hot end stay vitamins.
