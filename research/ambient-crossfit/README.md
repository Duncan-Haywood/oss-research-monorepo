# ambient-crossfit: do cross-fitting and a validation-chosen cap make doubly robust learning from an assistant's own feedback work?

Track 2 (ambient AI assistant), follow-up to `ambient-drclip`, whose first next step was "cross-fitted outcome models combined with a cap, and a cap chosen by validation rather than a grid". Produced with AI assistance. **Stylised, simulated results only**: every distribution is chosen by me and nothing is a claim about a real user, device or product. **Negative/mixed result**: the two additions do not beat the simple fixed-cap fits of `ambient-drclip`.

## Motivation

`ambient-drclip` showed that capping the inverse propensity removes the doubly robust (DR) collapse with an informed prior but not with an uninformed one, and that the cap was never chosen without peeking at held-out streams. Here the outcome model is cross-fitted (each window's prediction comes from a model that never saw it) and the cap is picked from logged data alone.

## Builds on (and does not claim affiliation with)

- `research/ambient-drclip` (and through it `ambient-dr`, `ambient-ips`, `ambient-bandit`): simulated windows, &epsilon;-greedy policy, MAP logistic fit, DR pseudo-labels, copied into `src/ambient_crossfit/core.py` so the project is self-contained.
- Cross-fitting for doubly robust estimators is a standard device; I cite no specific result and the implementation here is my own, not a reproduction. DR itself: Robins, Rotnitzky and Zhao (1994), *J. Amer. Statist. Assoc.* 89(427):846&ndash;866; Dud&iacute;k, Langford and Li (2011), ICML (as cited in `ambient-dr`).

No research group from `prompt.md` is built on; there is no lab tag.

## Method

Same world, policy, seeds and scoring as `ambient-drclip` (fits at hour 100; 20 seeds; &epsilon; &isin; {0.002, 0.005, 0.02}; two priors; scored on 20 fresh 100 h held-out streams with no exploration). New fits:

- `dr_plain`: unclipped DR, outcome model = clip10 fit on all spoken windows (in-sample).
- `dr_cf`: unclipped DR, outcome model cross-fitted over 2 random folds.
- `dr_cf_sel`: cross-fitted outcome model plus a cap chosen from {1, 5, 20, 100, &infin;}. For each cap, fit on fold 1 and score the fitted policy on fold 0 by an inverse-propensity estimate of utility (reward seen only where the logged policy spoke, weight 1/&pi;, uncapped). The best cap is then used to fit on all windows.
- `dr_cf_prior_sel`: the same with the prior alone as outcome model.

`biased`, `clip10`, `random_matched` and `full` are as before; `random_matched` and `full` use labels a deployed assistant never sees.

## Reproduce

```bash
cd research/ambient-crossfit
pip install numpy pytest
PYTHONPATH=src python3 -m pytest -q tests       # 5 tests
PYTHONPATH=src python3 experiments/run.py       # about 6 minutes, writes experiments/results.txt
```

## Results (from `experiments/results.txt`; held-out utility per hour, mean over 20 seeds; oracle 12.71)

| prior | &epsilon; | biased | clip10 | dr_plain | dr_cf | dr_cf_sel | dr_cf_prior_sel | random_matched |
|---|---|---|---|---|---|---|---|---|
| uninformed | 0.002 | 1.59 | &minus;33.17 | &minus;48.77 | &minus;49.54 | &minus;30.35 | 4.87 | 12.09 |
| uninformed | 0.005 | &minus;0.15 | &minus;62.95 | &minus;15.89 | &minus;42.66 | &minus;13.16 | &minus;1.13 | 12.13 |
| uninformed | 0.020 | &minus;13.08 | &minus;96.19 | &minus;49.54 | &minus;36.17 | &minus;17.54 | 0.35 | 3.65 |
| informed | 0.002 | 10.62 | 11.70 | 0.26 | 2.80 | 5.15 | 11.79 | 12.48 |
| informed | 0.005 | 10.84 | 12.15 | 11.00 | 10.85 | 12.13 | 12.30 | 12.48 |
| informed | 0.020 | 11.42 | 12.52 | 12.35 | 12.34 | 12.51 | 12.28 | 12.53 |

`biased`, `clip10` and `dr_plain` (= `dr_clip10`) reproduce `ambient-drclip` for the same seeds; `random_matched` draws its random subset after the cross-fitting draws, so its subset differs from `ambient-drclip` (12.09 against 12.15 at uninformed &epsilon; = 0.002, 3.65 against 12.52 at uninformed &epsilon; = 0.02). That one cell shows how much one random subset can move a fit with this prior. Standard deviations (often tens of utility/h) and the chosen caps are in `results.txt`.

1. **Cross-fitting alone does not fix the unclipped estimator.** `dr_cf` is no better than `dr_plain` at the cells where the latter collapses (informed &epsilon; = 0.002: 2.80 against 0.26, both with standard deviations of 29&ndash;41; uninformed: &minus;36 to &minus;50). The collapse is driven by the 1/&epsilon; weights, not by overfitting of the outcome model, in this world.
2. **A validation-chosen cap helps a little at best.** `dr_cf_sel` is above `dr_cf` in most cells but stays far below the biased fit with the uninformed prior (&minus;13 to &minus;30) and below it at informed &epsilon; = 0.002 (5.15 against 10.62). The IPS validation estimate is itself noisy at small &epsilon;, and the chosen caps are spread over the whole grid (see `results.txt`), which is consistent with selection on noise, though I did not test that.
3. **Prior as outcome model plus selected cap is the best DR variant here, but not better than fixed caps.** With the informed prior `dr_cf_prior_sel` scores 11.79, 12.30 and 12.28, in line with the fixed `m = prior` fits of `ambient-drclip` (12.17, 12.35, 12.34 at c = 100), so selection recovered roughly what the best fixed cap gave without peeking at held-out data, at the cost of a more complex procedure. With the uninformed prior it scores 4.9, &minus;1.1 and 0.4 with a large spread at &epsilon; &ge; 0.005 (std 36&ndash;39), no better than the biased fit or the prior's own 4.01 seen in `ambient-drclip`.
4. **No DR variant approaches the random-subset control** (about 12.1 with the uninformed prior at the two smaller &epsilon;), which uses labels of windows the assistant stayed silent on.

## Limitations

- Same stylised world as `ambient-drclip`: independent windows, instant noise-free feedback, a model with the true functional form, costs chosen by me.
- One fit hour, one prevalence, 20 seeds, 2 folds, one validation split, one cap grid. Variance with the uninformed prior is very large, so only large gaps are reliable; I ran no significance tests.
- The validation estimate uses one held-out fold; repeated or K-fold selection was not tried. No self-normalised or switching estimators were tried.
- The `random_matched` control uses a different random subset than in `ambient-drclip` (see above), so it is not an exact reproduction.

## Next steps

- Self-normalised or "switch" DR estimators, which are designed for small propensities, against the capped forms.
- Repeated K-fold cap selection, or a larger validation share, to see whether selection noise is the limit.
- A better outcome model than the prior or the clip10 fit.
- Real accept/dismiss logs, if the owner opts in to collecting them.

## Outside dependencies

numpy (and pytest for the tests). No model, dataset, service or hardware is used.
