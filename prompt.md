# Repository prompt

The standing brief for work on this repository.

## Mission
Build a public research portfolio (MIT-licensed) that supports PhD applications in ML/AI, robotics & autonomy, operations research, or industrial engineering in a CS / math / econ / finance department. Produce work a faculty member would take seriously: white papers written to publishable standard, reproducible code, implementations, and benchmarks. Quality beats volume: prefer deepening, correcting or consolidating an existing artifact over starting a new, thinner one.

## Central theme
Simulating and training with digital clones (digital twins) of physical-world systems, including sim-to-real transfer, simulation fidelity, and learning in simulation for real benefit. Every project should connect to this theme where it reasonably can.

## Research groups to build on
Read their recent papers, code and project pages. Implement, reproduce, extend, and follow up the implications of their work.

Robotics & autonomy (priority):
- ARPG, Christoffer Heckman (CS): https://arpg.colorado.edu/
  Perception, SLAM, radar/lidar, field and subterranean robotics, vision-language navigation, generative 3D occupancy and scene synthesis.
  Directions: generative digital twins of environments, sensor simulation (especially radar), sim-to-real for perception, multi-robot mapping in simulation.
- CAIRO Lab, Bradley Hayes (CS): https://cairo-lab.com/
  Task and motion planning, learning from demonstration, explainable AI, human-robot collaboration.
  Directions: learning from demonstration inside digital twins, explainable planners evaluated in simulation, simulated human models for training collaborative robots.
- HIRO Group, Alessandro Roncone (CS): https://hiro-group.ronc.one/
  Embodied intelligence, social intelligence, robots in chemistry labs.
  Directions: digital twins of lab and manipulation workcells, embodied learning in simulation, sim-to-real for manipulation.
- Autonomous Systems IRT: https://www.colorado.edu/irt/autonomous-systems/
- RECUV (unmanned vehicles): https://www.colorado.edu/recuv/
  Directions: UAV and field-robot simulation, targeted observation of severe weather, safe autonomy with verification.

## Output standards
- Each artifact lives in its own directory with a README covering motivation, which group's work it builds on (with citations), method, how to reproduce, results, limitations, and next steps.
- Never fabricate results. Report only what the code actually produced. Mark anything preliminary or negative as such.
- White papers use proper citations (BibTeX) and credit prior work accurately.
- Never cite from memory. Every reference must be checked against a real source (DOI, arXiv, publisher or lab page) for authors, title, venue and year before it is committed. A citation that cannot be verified is removed, not guessed.
- State plainly when results come from simulation only. Never imply real-robot, real-sensor or field validation that did not happen.
- Tag each artifact with the lab(s) it relates to, so it can be cited when contacting that faculty member.
- Prefer lightweight, runnable simulators (e.g. MuJoCo, PyBullet, Isaac or Gazebo only when needed) and small experiments that finish on modest hardware.

## Authorship & AI attribution
- The research, code and writing in this repository are produced by Claude (Anthropic's AI model) through Claude Code, directed and reviewed by Duncan Haywood. Say so accurately in each README and white paper (e.g. "Written by Claude (Anthropic) via Claude Code, directed by Duncan Haywood"). Never present the work as solely human-authored, and never overstate the human's or the AI's part.
- Credit what each artifact builds on: the papers, code, datasets and simulators it reproduces or extends, with citations, so a reader can tell what is new here and what is not.
- Commits carry the Claude co-author trailer.

## Licensing & attribution
- Original work is MIT-licensed.
- Third-party code keeps its original license. Check compatibility before vendoring, and prefer dependencies over copying.
- Never imply affiliation with, or endorsement by, any lab, professor or company. Say "builds on" or "reproduces", never "with" or "for".

## Portfolio site
Maintain a GitHub Pages site listing each artifact: a one-line summary, related lab, and links to the paper, code and results. Keep it current as work merges.

## Verification (about 25% of effort)
Spend roughly a quarter of each work session auditing what is already in the repository rather than adding to it. Pick artifacts not recently audited (featured and most-linked first) and check:
- Correctness: tests pass; numbers in the README and paper match what the code produces when rerun; the method does what the text says; the maths and units are right.
- Academic integrity: citations exist and are accurate; claims stay within what the results support; limitations and negative results are stated.
- Credit and licensing: prior work and the labs are credited accurately, with "builds on" wording and no implied affiliation; third-party code keeps its license; AI authorship is stated.
Fix what you find, or mark it clearly in the artifact's README if it cannot be fixed yet. Record each audit (date, artifact, what was checked, what was found and fixed) in the commit message, so the error rate can be measured over time.

## Workflow
Work on feature branches. Before merging, make sure tests and CI pass, READMEs are complete, and citations are checked. Merge changes when done, and merge other branches and PRs that are ready for merge and haven't been merged yet.
