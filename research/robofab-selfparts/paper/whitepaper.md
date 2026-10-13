# Which limit of a small arm decides how much of its own gripper it can assemble? A stylised check

*Produced with AI assistance (Claude). Stylised, simulation-only; masses, forces and layout are chosen values, not measurements.*

**Question.** If a three-joint arm were asked to assemble a copy of its own printed gripper, which of its limits (gripper opening, push force, base placement, no screwdriver) decides how much it can do?

**Model.** See `README.md`: planar 3R arm, analytic IK with joint limits and a pitch tolerance, per-part grasp, payload, reach and insertion-force checks, parent-before-child closure; 8 printed parts and 3 vitamins.

**Findings (from `experiments/results.txt`).**
1. The opening must exceed the root part's grasp width: at 40 mm or less nothing can be assembled, because every part hangs off the palm (50 mm).
2. Above that, push force sets the result: printed-mass fraction 0.466, 0.714, 0.764 at 4, 8, 12 N and 1.000 from 16 N (the servo does not matter here: only printed parts count). The thresholds follow from forces I assigned.
3. Base position has a dead band (0.225 to 0.475 m): no printed part is assembled, since early steps need a fingertip position under the base that the elbow limit forbids, or the tray is out of reach.
4. A screwless redesign removes a tool-limited step but, at 12 N, the printed fraction is unchanged; the arm's own limits bind first.
5. With a fixed 60 mm opening, the arm assembles copies scaled 0.6 to 1.2 of the default and none at 1.5.

**Limits.** Planar kinematics, no collisions, dynamics or tolerances; chosen parameters; a deterministic sweep. Nothing here is a claim about a physical arm.

**References.** `refs.bib` (Jones et al. 2011; Zykov et al. 2005; Freitas and Merkle 2004), taken from `PROJECTS.md` and not re-verified in this run.
