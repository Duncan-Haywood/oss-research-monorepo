"""Writes experiments/results.txt. Standard library only."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from selfrep_rodbeam import beam as b

LENGTH = 0.40      # m, assumed unsupported span of an X-axis rod
LOADS = {"light (carriage 0.25 kg)": 0.25, "heavy (carriage 0.50 kg)": 0.50}
LIMITS = {"0.05 mm": 5e-5, "0.2 mm": 2e-4}   # assumed acceptable sag
D_STEEL = 0.008

out = []
P = out.append
P("selfrep-rodbeam results (assumed moduli, loads and limits; see README)\n")
P(f"span {LENGTH*1e3:.0f} mm, simply supported centre load; clamped values in brackets\n")
for lname, m in LOADS.items():
    F = m * b.G
    P(f"== load {lname}: F = {F:.2f} N")
    for mat, (lo, E, hi) in b.MATERIALS.items():
        I = b.inertia_solid(D_STEEL)
        dl = b.deflection(E, I, LENGTH, F) * 1e3
        dc = b.deflection(E, I, LENGTH, F, "clamped") * 1e3
        dsw = b.self_weight_deflection(E, I, LENGTH, {"steel": 7850, "birch_dowel": 650, "pla_printed": 1240}[mat],
                                       3.14159265 * D_STEEL ** 2 / 4) * 1e3
        P(f"  {mat:12s} 8 mm rod: sag {dl:.4f} mm [{dc:.4f}], own weight {dsw:.5f} mm")
    for lim_name, lim in LIMITS.items():
        for mat, (lo, E, hi) in b.MATERIALS.items():
            dmin = b.min_passing_diameter(E, LENGTH, F, lim) * 1e3
            dmin_c = b.min_passing_diameter(E, LENGTH, F, lim, "clamped") * 1e3
            pr = b.pass_probability(mat, D_STEEL, LENGTH, F, lim)
            P(f"  limit {lim_name}: {mat:12s} min diameter {dmin:5.1f} mm [{dmin_c:5.1f}]; "
              f"8 mm rod passes in {pr*100:5.1f}% of modulus draws")
    P("")
P("Equal-stiffness diameter to an 8 mm steel rod (nominal moduli):")
for mat, (lo, E, hi) in b.MATERIALS.items():
    P(f"  {mat:12s} {b.equal_stiffness_diameter(E, 200e9, D_STEEL)*1e3:5.1f} mm "
      f"(range {b.equal_stiffness_diameter(hi, 200e9, D_STEEL)*1e3:.1f}-{b.equal_stiffness_diameter(lo, 200e9, D_STEEL)*1e3:.1f})")
open(os.path.join(os.path.dirname(__file__), "results.txt"), "w").write("\n".join(out) + "\n")
print("\n".join(out))
