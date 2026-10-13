# Can a small arm assemble a copy of its own printed gripper? A stylised reach, grasp and insertion check

Pure Python, standard library only. A planar three-joint arm (links 0.20, 0.20 and 0.10 m, chosen for this study; not an SO-101 measurement) is asked to assemble a copy of its own gripper: 8 printed parts (palm, rack, two fingers, two pins, cover, side cap) plus vitamins (a servo and two screws). Each step is checked for grasp width, payload, reach with a tool-pitch tolerance (analytic two-link inverse kinematics, joint limits) and insertion force; a part can be placed only after its parent. All numbers below are from `experiments/results.txt`; part masses, forces and tray positions are illustrative values I chose, not measurements.

- **The root part gates everything.** The palm is the widest part (50 mm grasp) and every other part mounts on it, directly or through the rack. With an opening of 40 mm or less, printed-mass fraction assembled is 0.000 in every cell of the opening x push sweep; at 50 mm or more it depends on push force alone.
- **Insertion force, not reach or payload, is the next binding limit.** At the best base position, printed-mass fraction assembled is 0.466, 0.714 and 0.764 for push 4, 8 and 12 N, and 1.000 (all 8 printed parts) from 16 N. The two press-fit pins (14 N) and the cover (16 N) need the most. These thresholds follow from the forces I assigned; they are not measured.
- **Placing the base matters, and has a dead zone.** Sweeping the base position from 0 to 0.8 m along the tray line, 0 of 8 printed parts are assembled for base positions of 0.225 to 0.475 m: the first placements need the fingertip under or near the base, which a folded elbow cannot reach (elbow limit 150 deg), and the tray is too far from the base for the other picks. Away from that band the arm assembles 4 or 5 of 8 (0.764 of printed mass) at the default 12 N push.
- **Design for the arm helps only where the arm was the limit.** Replacing the screwed-on servo with a clip-in one makes the servo reachable-limited rather than tool-limited (the screws are not assemblable by this arm; 2 vitamins fewer). It does not change the printed fraction at 12 N, because the printed-part blocker there is insertion force.
- **Scale test.** With a fixed 60 mm opening, a gripper scaled to 0.6 to 1.2 of the default is fully assemblable (screwless, 16 N push); at scale 1.5 (75 mm palm) it is 0.000. So this arm can make copies up to its own opening, not larger ones.
- Not shown: any claim that this arm closes the loop on a physical gripper. The servo and screws are vitamins either way.

```bash
cd research/robofab-selfparts
PYTHONPATH=src python3 -m unittest discover -s tests -v   # 9 tests, <1 s
python3 experiments/run.py                                # <1 s; deterministic; writes experiments/results.txt
```

## Motivation

Track 4 (`robofab`) asks for arms that assemble their own parts, joining track 1 (self-replication; see `research/selfrep-closure`). Before any hardware test, a cheap model can say which limits of the arm (opening, push, base placement) decide how much of a copy of itself it could assemble, and which design choices of the part (joint type) remove a limit. The theme is sim-fidelity and sim-first design: the checker here is deliberately coarse and the README says what it leaves out.

## Builds on

The task-and-motion-planning and learning-from-demonstration directions of CAIRO Lab (Bradley Hayes, <https://cairo-lab.com/>), and the workcell-twin and manipulation directions of the HIRO Group (Alessandro Roncone, <https://hiro-group.ronc.one/>). No paper from either lab is reproduced and nothing here is affiliated with or endorsed by them.

Context, not reproduced: Jones et al. (2011), "RepRap – the replicating rapid prototyper", *Robotica* 29(1); Zykov et al. (2005), "Self-reproducing machines", *Nature* 435; Freitas and Merkle (2004), *Kinematic Self-Replicating Machines* (references in `paper/refs.bib`). Also, for assembly with learned and simulated insertion: Narang et al. (2022), "Factory", RSS; Tang et al. (2023), "IndustReal", RSS. Citations were taken from `PROJECTS.md`/memory and were not re-verified against the publishers in this run (no web access); check before citing. The sibling project `research/robofab-sequence` plans assembly order; this one does not reuse its code.

## Method

- **Arm** (`src/robofab_selfparts/model.py`). Planar 3R in a vertical plane: two-link IK for the wrist point after subtracting the tool length along the wanted pitch, both elbow branches, joint limits (shoulder -10 to 190 deg, elbow +-150 deg), pitch searched within +-15 deg in 1 deg steps. Payload 0.15 kg, gripper opening and tool push force are parameters.
- **Parts.** Mass, grasp width, tray pick point, mounting place point, pitch (down or horizontal), parent part, join type (slide, snap, press, screw) and insertion force.
- **Step check.** Fails on: grasp wider than opening; mass over payload; pick or place unreachable; insertion force over push; screw (the arm has no driver).
- **Assembly.** Greedy closure over the parent relation (a part is placed if its step passes and its parent is placed). Printed-mass fraction is the share of printed-part mass placed.
- **Sweeps.** Base position (0 to 0.8 m, step 25 mm), opening x push, screwed vs clip-in servo, gripper scale, push thresholds. Section 2 onwards report the best base position in the grid for each cell.

## Results

See the bullets above and `experiments/results.txt`; `paper/whitepaper.md` has the discussion.

## Limitations

Stylised. Planar kinematics with no obstacles, no collision between arm and fixtures, no dynamics, no grasp stability, no tolerance or alignment (so no peg-in-hole difficulty), one fixed tray layout, a single product, insertion forces and masses I chose, a deterministic sweep with no uncertainty. Forces needed for real snap fits depend on the print and design. A feasible step here says only that the stated checks pass, and nothing about a real arm; the self-referential question (can it make its own gripper?) is answered only for this parametrised model. Next to `robofab-insert` (learned insertion) the missing piece is a physics check of the step in MuJoCo.

## Next steps

Check the reach and force thresholds in a physics engine, add collisions with the fixture, vary tray layout and arm link lengths, plan the order of placements across subassemblies jointly with `robofab-sequence`, and feed the printed-fraction into `selfrep-closure` as the arm's contribution to closure.

## Owner steps

Not done here, and nothing was ordered. A physical test would print the 8 parts and use a low-cost open arm (such as the SO-101) and a force gauge to measure real insertion forces and grasp widths. A priced bill of materials is not given because no prices were verified in this run.

## Outside dependencies

None at run time (Python standard library). Vitamins of the modelled gripper: a servo and screws (the arm cannot make them). Produced with AI assistance (Claude).

MIT.
