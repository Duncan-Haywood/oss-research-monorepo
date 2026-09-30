"""Reproduces every number in paper/whitepaper.md. Run: PYTHONPATH=src python3 experiments/run.py > experiments/results.txt"""
from friction_twin.model import run_loop, twin_radius, amplitude, stick_slip_stats

N = 60000
GAINS = ((0.5, 0.1), (0.3, 0.05), (0.2, 0.2), (0.3, 0.1), (0.5, 0.2))

print("Friction twin: massless load, dry friction (stiction fs, Coulomb fc <= fs); twin has none. Loop z+=z+x, u=-(kp*x+ki*z), x+=u-s*fc.")

print("\n== 1. Twin converges; Coulomb-only twin rests; real stiction loop hunts (fs=1, fc=0.5, x0=10, %d steps, tail 3000) ==" % N)
print("kp    ki     twin radius  twin |x| end  Coulomb-only twin amp  real amp  max|x|   stuck intervals  mean stuck  spread  slide steps")
for kp, ki in GAINS:
    tw = abs(run_loop(kp, ki, 0.0, 0.0, 10.0, 3000)[0][-1])
    cu = amplitude(run_loop(kp, ki, 0.5, 0.5, 10.0, N)[0])
    xs, sl = run_loop(kp, ki, 1.0, 0.5, 10.0, N)
    k, m, sp, ms, mx = stick_slip_stats(xs, sl)
    print("%-5g %-6g %-12.3f %-13.1e %-22.2g %-9.4f %-8.4f %-16d %-11.1f %-7.2f %.2f" % (kp, ki, twin_radius(kp, ki), tw, cu, amplitude(xs), mx, k, m, sp, ms))

print("\n== 2. Homogeneity (kp=0.5, ki=0.1, fc=fs/2, x0=10 fs, 5000 steps): max |trajectory/fs - reference| ==")
ref = run_loop(0.5, 0.1, 1.0, 0.5, 10.0, 5000)[0]
for lam in (2.0 ** -7, 2.0 ** 6, 0.01, 100.0):
    x = run_loop(0.5, 0.1, lam, 0.5 * lam, 10.0 * lam, 5000)[0]
    print("fs=%-10g max dev = %.3g" % (lam, max(abs(a / lam - b) for a, b in zip(x, ref))))
print("amplitude/fs over %d steps:" % N, "  ".join("fs=%g: %.4f" % (lam, amplitude(run_loop(0.5, 0.1, lam, 0.5 * lam, 10.0 * lam, N)[0]) / lam) for lam in (0.01, 1.0, 100.0)))

print("\n== 3. Stiction drop sweep (kp=0.5, ki=0.1, fs=1, fc=1-d): amplitude and max|x| relative to d, three starts (200000 steps, tail 20000) ==")
print("d       amp/d (x0=10)  amp/d (x0=2)  amp/d (x0=0.5)  max|x|/d (x0=10)")
for d in (1.0, 0.5, 0.2, 0.1, 0.05, 0.02, 0.01, 0.0):
    row, mx = [], 0
    for x0 in (10.0, 2.0, 0.5):
        xs, sl = run_loop(0.5, 0.1, 1.0, 1 - d, x0, 200000)
        row.append(amplitude(xs, 20000))
        if x0 == 10.0:
            mx = stick_slip_stats(xs, sl)[4]
    if d > 0:
        print("%-7g %-14.4f %-13.4f %-15.4f %.4f" % (d, row[0] / d, row[1] / d, row[2] / d, mx / d))
    else:
        print("%-7g amp = %.2g, %.2g, %.2g (stiction = Coulomb: deadband, comes to rest)" % (d, *row))

print("\n== 4. Integral gain (kp=0.5, fs=1, fc=0.5): amplitude by start ==")
print("ki     twin radius  x0=10    x0=2     x0=0.5")
for ki in (0.01, 0.02, 0.05, 0.1, 0.2, 0.4):
    r = [amplitude(run_loop(0.5, ki, 1.0, 0.5, x0, 80000)[0]) for x0 in (10.0, 2.0, 0.5)]
    print("%-6g %-12.3f %-8.4f %-8.4f %.4f" % (ki, twin_radius(0.5, ki), *r))

print("\n== 5. Mis-calibrated twin with stiction: predicted amplitude vs real (kp=0.5, ki=0.1, true fs=1, fc=0.5 i.e. d=0.5, x0=2) ==")
real = amplitude(run_loop(0.5, 0.1, 1.0, 0.5, 2.0, N)[0])
print("real amp = %.4f" % real)
print("assumed d   twin amp   error vs real")
for dh in (0.0, 0.1, 0.25, 0.4, 0.5, 0.6, 0.75):
    a = amplitude(run_loop(0.5, 0.1, 1.0, 1 - dh, 2.0, N)[0])
    print("%-11g %-10.4f %+.1f%%" % (dh, a, 100 * (a - real) / real))
