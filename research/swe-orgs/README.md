# swe-orgs: a cited catalogue of engineering-organisation practices, with a ledger headroom check (batch 1, preliminary)

Pure Python, no dependencies. Milestone 7 (`swe-orgs`) of track 10 in `PROJECTS.md`, the standing milestone that studies how engineering organisations ship. **This is batch 1: seven sources, no early-stage company, no proposal ready for an experiment.** Produced with AI assistance (Claude). It builds on none of the labs in `prompt.md`.

## Question

Which practices do published accounts of engineering organisations claim improve throughput, quality, review, release, team shape, on-call and monorepo work, what evidence stands behind each, and which would plausibly carry over to a fleet of agent sessions that land work through `prompt.md`'s loop?

## Results

- `experiments/practices.csv` holds 7 rows (written by `experiments/build_catalogue.py`, validated by `src/swe_orgs/catalogue.py`): evidence is 3 measured, 3 case study, 1 opinion; stage is 3 growth and 4 large. Early-stage (seed to Series B) companies, which the milestone puts first, are **not covered yet**: batch 1 found well-documented sources mainly from large firms. Next batch should start there.
- Mapping to this loop: 3 practices are already in it (monorepo, merge-on-green, owner of the outcome), 2 are candidates (four delivery metrics; independent review), 2 are not proposed because they assume people (knowledge transfer through review, squads).
- Ledger headroom (`experiments/results.txt`, 265 rows of `prompts/runs.jsonl`): a review or CI practice can only gain what failures cost. 7/265 runs (2.6%, Wilson 1.3% to 5.4%) were not a success, 3/265 (1.1%) recorded a parallel-run collision, and 1/265 had an integrity issue. `ci_failures_before_green` is 0 in all 177 rows that record it and `review_findings` is 0 in all 193 that record it; because those fields look like defaults rather than observations, treat them as an unreliable lower bound, not as proof of zero.
- Consequence for proposals: the visible loss is small (below about 5% of runs), so a practice that only reduces failures cannot raise valuable throughput much; a practice that raises value per run or removes collisions has more room. No proposal is made yet, as the milestone requires a clear expected gain, and wall time and tokens are recorded in too few rows (wall_minutes is non-null in 7 of 265) to estimate cost.

## What each source says (stated in our words, each verified to exist, none quoted)

| id | source | year | evidence |
|---|---|---|---|
| accelerate-metrics | Forsgren, Humble, Kim, *Accelerate*, IT Revolution | 2018 | measured |
| google-monorepo | Potvin, Levenberg, CACM 59(7) | 2016 | case study |
| google-code-review | Sadowski et al., ICSE-SEIP 181-190, doi 10.1145/3183519.3183525 | 2018 | measured |
| ms-review-benefits | Bacchelli, Bird, ICSE 712-721, doi 10.1109/ICSE.2013.6606617 | 2013 | measured |
| fb-continuous-deploy | Savor et al., ICSE-C 21-30 | 2016 | case study |
| spotify-squads | Kniberg, Ivarsson (whitepaper) | 2012 | opinion |
| google-sre-oncall | Beyer, Jones, Petoff, Murphy, *Site Reliability Engineering*, ch. 11 | 2016 | case study |

Full links and the per-row claim, loop mapping and assumptions that do or do not carry over are in the CSV. Bibliographic details (authors, venue, year, pages) were checked against the publisher, ACM/DOI or author pages found by search. The *content* summaries rest on abstracts and publisher or search summaries, not a full read of each paper; `accelerate-metrics` and `spotify-squads` and `google-sre-oncall` are described from the title, publisher summaries and the chapter introduction only. Read the source before relying on a row.

## Which assumptions do not carry over

Headcount, meetings, hiring, career ladders and knowledge held in people's heads (squads, review as teaching) do not exist for sessions that start empty each run. What does carry: shared trunk, merge on green, ownership of the outcome by the author, and measuring throughput with stability.

## Reproduce

```
python experiments/build_catalogue.py   # writes practices.csv
python experiments/run.py               # prints results.txt
python -m unittest discover -s tests
```

## Limitations

Seven sources, large-company bias, evidence labels are ours and coarse, summaries not from full reads, ledger headroom uses fields that may be defaults, no cost estimate, no experiment.

## Next steps

Add early-stage and Series A to B sources first (engineering blogs, investor writing, postmortems); record each source's own numbers where it gives them; estimate cost per candidate once `swe-ledger` rows carry tokens and wall time; send surviving proposals through `swe-prompt`'s sequential test.
