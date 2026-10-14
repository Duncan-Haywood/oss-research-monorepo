import pathlib, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "selfrep-rodbeam" / "src"))
sys.path.insert(0, str(ROOT / "selfrep-redesign" / "src"))
from selfrep_rodbeam import beam as b
from selfrep_redesign import design as d
from selfrep_closure.bom import Part

PROCS = {"fdm", "cnc", "laser"}
LENGTHS = {"350 mm 8 mm smooth rod": .350, "405 mm 8 mm smooth rod": .405, "420 mm 8 mm smooth rod": .420}
P, TOL, L = 2.5, 0.2e-3, 0.405      # N per rod, m allowed deflection, m span: all ASSUMED
out = []
out.append(f"Assumed: load {P} N per rod at midspan, span {L*1e3:.0f} mm, deflection tolerance {TOL*1e3:.2f} mm, steel E 200 GPa")
out.append("\nmidspan deflection of an 8 mm rod (mm) and diameter needed to match steel / meet tolerance (mm)")
out.append("material            E(GPa)  defl@8mm  vs steel  d_match  d_tol  mass of 6-rod set at d_match (g)")
mats = [("steel", 200, "steel"), ("beech, E=9.5", 9.5, "wood"), ("beech, E=11.9", 11.9, "wood"),
        ("beech, E=13", 13, "wood"), ("PLA, E=2", 2, "pla"), ("PLA, E=3.5", 3.5, "pla")]
for name, E, m in mats:
    E *= 1e9
    dd = b.deflection(P, L, E, b.D0)
    dm = b.matched_diameter(E)
    mass = sum(2 * b.rod_mass_g(m, l, dm) for l in LENGTHS.values())
    out.append(f"{name:18} {E/1e9:6.1f}  {dd*1e3:8.3f}  {dd/b.deflection(P,L,b.E_STEEL,b.D0):6.1f}x {dm*1e3:7.1f} "
               f"{b.tolerance_diameter(P,L,E,TOL)*1e3:6.1f}  {mass:8.0f}")

# closure effect
E_W = 11.9e9
dm = b.matched_diameter(E_W)
steel_set = sum(2 * b.rod_mass_g("steel", l, b.D0) for l in LENGTHS.values())
wood8 = sum(2 * b.rod_mass_g("wood", l, b.D0) for l in LENGTHS.values())
woodm = sum(2 * b.rod_mass_g("wood", l, dm) for l in LENGTHS.values())
out.append(f"\nsmooth-rod set mass: steel 8 mm {steel_set:.0f} g (selfrep-closure: 2*140+2*160+2*165=930 g); beech 8 mm {wood8:.0f} g; "
           f"beech matched ({dm*1e3:.1f} mm) {woodm:.0f} g; selfrep-redesign assumed 6*30 = 180 g")

def parts_with(wood_mass_total, bushings):
    names = set(LENGTHS)
    if bushings:
        names.add("LM8UU linear bearing")
    ps = [p for p in d.design(()) if p.name not in names]
    ps.append(Part("wood dowel rods", 6, "rod", wood_mass_total / 6, 0.3, ("cnc",), "assumed", feedstock="wood dowel"))
    if bushings:
        ps.append(d._printed("printed bushing", 10, 6.0))
    return ps

out.append("\nclosure (lines/mass/cost, printer+router+laser shop):")
rows = [("baseline (steel rods, LM8UU)", d.design(())),
        ("redesign's assumed dowel (180 g, LM8UU kept)", d.design((4,))),
        ("beech 8 mm, geometric mass, LM8UU kept", parts_with(wood8, False)),
        (f"beech matched {dm*1e3:.1f} mm + printed bushings", parts_with(woodm, True)),
        ("redesign: printed bushings + assumed dowel", d.design((0, 4)))]
for name, ps in rows:
    out.append(f"  {name:48}" + "/".join(f"{100*d.closure_of(ps, PROCS, m):5.1f}%" for m in ("lines", "mass", "cost"))
               + f"   vitamin lines {d.vitamin_kinds(ps, PROCS)}")
out.append("\nnote: closure counts the makeable share of part mass; a bigger makeable rod raises mass closure without the "
           "printer needing fewer vitamins. Vitamin lines are the fairer comparison.")
text = "\n".join(out)
print(text)
(pathlib.Path(__file__).parent / "results.txt").write_text(text + "\n")
