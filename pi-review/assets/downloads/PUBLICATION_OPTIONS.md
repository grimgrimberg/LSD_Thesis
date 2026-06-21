# Publication And Sharing Options

Codex did not upload, publish, email, stage, commit, push, create a release, create a PR, or deploy this package.

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

## Option D: Static Local HTML / Site Link

Open locally:

```text
docs/reports/pi_thesis_share_package/site/index.html
```

To share manually, upload these together:

- `site/`
- `assets/`
- the Markdown files in the package root

Keep relative paths intact.

## Option E: Future GitHub Pages

This is future-only.

Possible future approach:

1. Get PI approval for public framing.
2. Decide whether this PI package should be public.
3. Commit the package.
4. Add it to a Pages build or static file host in a separate approved pass.

Do not build Pages or modify `_site/` as part of this package.
