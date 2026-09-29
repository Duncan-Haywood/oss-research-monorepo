# Anytime-valid audits: how many checks to slash a corrupted trace, without inflating false slashes

*Working note, MIT licensed. Stylised; pure-Python numerical checks, no claims about any deployed protocol.*

## Motivation
Refereed verification (`spot-check-slashing`, `verification-game`, `reproducible-refereed-training`) audits sampled steps of a committed training trace. Floating-point drift makes each check noisy: an honest step is flagged with probability a, a corrupted one with p>a. Two practical questions: how many audits before slashing, and can the referee *keep auditing until convinced* without slashing honest provers by chance? The betting / e-process view (Ville's inequality; Shafer–Vovk; Ramdas et al.) is the sequential cousin of the scoring-rule and wagering mechanisms in `wagering-modular-experts`: an e-process is the wealth of a bettor against "honest".

## Model (`src/anytime_audit/model.py`)
Audit outcomes X_t ~ Bern(a) under H0 (honest). Slash when an e-process E_t ≥ 1/δ. E1 fixed-n exact binomial test; naive *peeking* (re-run it after every audit); SPRT tuned to an assumed p₁; and the Beta(1,1)-**mixture** e-process E_t = k!(n−k)!/(n+1)! · a^{−k}(1−a)^{−(n−k)}, a nonnegative martingale under H0 (tested exactly), so P(sup_t E_t ≥ 1/δ) ≤ δ at *any* stopping rule.

## Results (`experiments/results.txt`; a=0.05, δ=0.05)
**R1 (peeking slashes honest provers).** Re-running the level-δ test after every audit up to N=1000 falsely slashes 28.4% of honest provers (19% checking every 50 audits) versus 3.7% for the fixed-n test and 1.6% for the mixture e-process, which is guaranteed ≤δ.

**R2 (speed).** Expected audits to slash follow ln(1/δ)/KL(p‖a) (Wald). At p=0.2: ideal 21.4, SPRT that knows p 25.2, mixture 32.4, fixed-n for 80% power 27. The mixture pays for not knowing p: ratio to ideal 1.57 at δ=0.05, 1.37 at 0.01, 1.25 at 0.001, consistent with a ½ln n regret term that vanishes relative to ln(1/δ).

**R3 (misspecification).** A fixed test planned for a severe corruption (p=0.4, n=7) has power 0.28 against a subtle one (p=0.15); an SPRT tuned to 0.4 has *negative* drift at p=0.15 and detects only 55% within 5000 audits. The mixture detects 100% with mean 68 audits (ideal 43). Adaptivity, not raw speed, is the mixture's value.

## Implications
A referee should set the audit budget adaptively and accept only e-value-thresholded slashes; peeking at a p-value is an exploitable false-slash channel (an honest prover's expected loss is stake × false-slash rate, which feeds the deterrence and stake conditions of `spot-check-slashing`). The e-process also composes across jobs and verifiers (product of independent e-values), a route to pooled evidence in `multi-verifier-audit`.

## Limits
i.i.d. Bernoulli flags with known honest rate a (in practice a is itself estimated from drift measurements; a plug-in needs a conservative upper bound), no adaptive adversary choosing which steps look corrupted, no cost-of-audit optimisation, and the mixture prior is not optimised (a Beta prior on p>a only, or a Krichevsky–Trofimov-style mix, should tighten R2).
