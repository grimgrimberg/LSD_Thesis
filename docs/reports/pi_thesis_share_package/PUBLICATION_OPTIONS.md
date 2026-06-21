# Publication And Sharing Options

The original offline package pass did not upload, publish, email, stage, commit, push, create a release, create a PR, or deploy this package. A later hosting pass wires it into GitHub Pages as a static supervisor pitch package.

Primary hosted URL after deployment:

```text
https://grimgrimberg.github.io/LSD_Thesis/pi-review/
```

## Option A: Send By Email

Use this for the first PI contact.

1. Paste the short email from `EMAIL_TO_PI.md`.
2. Attach `PI_REVIEW_BRIEF.md`.
3. Attach `EVIDENCE_AND_CALCULATIONS.md` if you want plot-level detail included upfront.
4. Attach `assets/screenshots/` or include the whole folder as a ZIP.

You may manually convert `PI_REVIEW_BRIEF.md` to PDF if preferred.

## Option B: Send As A ZIP

Manual PowerShell command from repo root:

```powershell
New-Item -ItemType Directory -Force docs\reports\pi_thesis_share_package\dist
Compress-Archive -Path docs\reports\pi_thesis_share_package\* -DestinationPath docs\reports\pi_thesis_share_package\dist\PI_THESIS_SHARE_PACKAGE.zip
```

This command was not run by Codex in this package pass.

## Option C: GitHub Link

Manual commands after review:

```powershell
git status --short --untracked-files=all
git add docs/reports/pi_thesis_share_package/
git commit -m "docs: add PI thesis share package"
git push origin HEAD
```

Then send the GitHub tree link to:

```text
docs/reports/pi_thesis_share_package/
```

Do not commit generated/raw/cache artifacts outside the package.

## Option D: GitHub Pages Pitch URL

Use this as the primary share path after the Pages workflow finishes:

```text
https://grimgrimberg.github.io/LSD_Thesis/pi-review/
```

Key direct pages:

- `https://grimgrimberg.github.io/LSD_Thesis/pi-review/pages/pitch-slides.html`
- `https://grimgrimberg.github.io/LSD_Thesis/pi-review/pages/figure-atlas.html`
- `https://grimgrimberg.github.io/LSD_Thesis/dashboard/`

## Option E: Static Local HTML / Site Link

Open locally:

```text
docs/reports/pi_thesis_share_package/deliverable_website/OPEN_ME_FIRST.html
```

To share manually, upload these together:

- `site/`
- `assets/`
- the Markdown files in the package root

Keep relative paths intact.
