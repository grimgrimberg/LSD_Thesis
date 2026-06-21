# PI Thesis Share Package - Sender Guide

Snapshot date: 2026-06-18

This folder is a PI-facing review package for the LSD thesis workbench. Codex created it locally only. Codex did not publish, upload, email, stage, commit, push, open a PR, create a release, or deploy anything.

## What To Send First

Send these files first:

1. `EMAIL_TO_PI.md` - paste the short email into your message.
2. `PI_REVIEW_BRIEF.md` - attach or link as the main brief.
3. `EVIDENCE_AND_CALCULATIONS.md` - attach or link if the PI wants plot-level details.
4. `site/index.html` - optional offline landing page for browsing the package.

If you want the cleanest first message, paste the short email and attach `PI_REVIEW_BRIEF.md` plus the `assets/screenshots/` folder.

## What To Attach

Recommended attachment set:

- `PI_REVIEW_BRIEF.md`
- `PROBLEMS_AND_NEXT_STEPS.md`
- `EVIDENCE_AND_CALCULATIONS.md`
- `METHODS_AND_DATA_SKILLS.md`
- `SCHOLARLY_CONTEXT.md`
- `assets/screenshots/dashboard-overview.png`
- `assets/screenshots/dashboard-ranking.png`
- `assets/screenshots/dashboard-robustness.png`
- `assets/screenshots/dashboard-empirical.png`
- `assets/screenshots/dashboard-prior-art.png`
- `assets/screenshots/dashboard-figures.png`

The full folder can also be zipped and sent as one review bundle.

## What To Paste In Email

Use the short version in `EMAIL_TO_PI.md` for the first contact. Use the detailed version only if your PI prefers more context upfront.

## What To Show Live

Recommended live walkthrough order:

1. `site/index.html`
2. `PI_REVIEW_BRIEF.md`
3. `assets/screenshots/dashboard-overview.png`
4. `assets/screenshots/dashboard-ranking.png`
5. `assets/screenshots/dashboard-robustness.png`
6. `assets/screenshots/dashboard-empirical.png`
7. `assets/screenshots/dashboard-prior-art.png`
8. `assets/screenshots/dashboard-figures.png`
9. `PROBLEMS_AND_NEXT_STEPS.md`

If the local FastAPI dashboard is already running in your own review session, use it as a live supplement. This package itself does not start a server.

## What Not To Claim

Do not say:

- The thesis is finished.
- The model simulates subjective experience.
- The model proves receptor-level LSD biology.
- The dashboard proves clinical validity.
- The current evidence is biological ground truth.
- Motion/confound proof is complete.
- Zenodo DOI/archive publication is complete.
- Run-02/music is primary evidence.

Safe wording:

> The infrastructure and evidence package are ready for PI review. The current evidence supports model-level macro-dynamic mechanism ranking, with explicit claim gates and blockers.

## Recommended Meeting Order

1. Start with the one-paragraph summary from `PI_REVIEW_BRIEF.md`.
2. Show the dashboard overview screenshot and explain the claim-gated posture.
3. Show mechanism ranking: C, E, D, A, B.
4. Show robustness and explain internal robustness versus external validation.
5. Show empirical viewer and explain paired LSD/placebo summary inspection.
6. Show prior-art inventory and how it prevents overclaiming.
7. Show Figure Deck and the blocked motion/archive gates.
8. End with `PROBLEMS_AND_NEXT_STEPS.md` and ask the PI to choose the next scientific blocker.

## Manual Link Options

GitHub folder link after committing and pushing:

```powershell
git status --short --untracked-files=all
git add docs/reports/pi_thesis_share_package/
git commit -m "docs: add PI thesis share package"
git push origin HEAD
```

Then send the GitHub tree link to `docs/reports/pi_thesis_share_package/`.

Cloud drive link:

1. Upload `docs/reports/pi_thesis_share_package/` to Google Drive, OneDrive, or Dropbox.
2. Share view access with your PI.
3. Point them first to `PI_REVIEW_BRIEF.md` or `site/index.html`.

Static site upload:

1. Upload `site/` plus `assets/` together.
2. Keep relative paths intact.
3. Do not treat this as a public release until the PI approves the scientific framing.

Local HTML preview:

Open this file in a browser:

```text
docs/reports/pi_thesis_share_package/site/index.html
```

No network dependency is required.
