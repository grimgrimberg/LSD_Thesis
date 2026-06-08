# DLPFC Granger Causality / Ego Dissolution

## Scope

Document the DLPFC, ego-dissolution, and emotional-arousal Granger-causality
analysis as author-only code pending manual contact.

## Verified Code Status

No public repository or archive has been verified in this workspace.

Review-derived method notes:

- Associated contact: `clayton.r.coleman@gmail.com`.
- Associated methods: Granger causality, fMRI/MEG fusion, theta-band
  thalamus-to-DLPFC information flow, ego dissolution, emotional arousal, and
  salience-network connectivity.
- The prompt states code was available from the lead author by email.

## Data Requirements

- fMRI and MEG data or already aligned multimodal derivatives.
- Granger-causality model order, preprocessing, and stationarity choices.
- Behavioral ego-dissolution and emotional-arousal scores.

## Dry-Run Check

```powershell
uv run python prior_art/scripts/dry_run_analysis_inputs.py dlpfc_granger_causality
```

## Reproduction Path

1. Do not send email automatically.
2. Use `prior_art/missing_code_contact_templates.md` for a manual request.
3. If code is shared, inspect license and redistribution terms before adding
   anything to this repository.
4. If code is not shared, document an independent implementation plan and mark
   it as non-original reproduction.

## Expected Outputs

- Directed connectivity or Granger-causality matrices.
- DLPFC/thalamus information-flow summaries.
- Correlations with ego-dissolution and emotional-arousal scores.

## Connection to the Surrogate Model

Maps to directed-control and salience/routing hypotheses, but remains outside
the current implemented evidence layers until author-only code or a verified
independent implementation is available.

## Blockers and Open Questions

- Code is author-only.
- Multimodal fMRI/MEG alignment is not specified.
- Behavioral scoring inputs are not verified locally.
