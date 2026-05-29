# ds006072 Minimum Payload Plan

This is a concrete acquisition bridge for external validation. It is not a psilocybin replication result until the selected payloads are local, empirical-viewer records are written, and unchanged scoring is applied.

- Status: `minimum_validation_payloads_local_ready_for_extraction`
- Claim status: `minimum_payloads_local_ready_not_yet_extracted`
- Required comparable subjects: `3`
- Selected subjects: `3`
- Local-ready selected subjects: `3`
- Selected files: `6`
- Selected bytes: `3078165976`

## Selected files

| Subject | Condition | Session | File | Local ready | Bytes |
| --- | --- | --- | --- | ---: | ---: |
| P1 | active_control_mtp | Drug1 | sub-1_Drug1_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii | true | 544220208 |
| P1 | psilocybin | Drug2 | sub-1_Drug2_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii | true | 544220208 |
| P2 | active_control_mtp | Drug2 | sub-2_Drug2_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii | true | 544220064 |
| P2 | psilocybin | Drug1 | sub-2_Drug1_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii | true | 544220064 |
| P3 | active_control_mtp | Drug1 | sub-3_Drug1_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii | true | 357065368 |
| P3 | psilocybin | Drug2 | sub-3_Drug2_rsfMRI_uout_bpss_sr_noGSR_sm4.dtseries.nii | true | 544220064 |

## Next commands

- `.\.venv\Scripts\python.exe scripts\build_ds006072_payload_plan.py`
- `.\.venv\Scripts\python.exe scripts\build_ds006072_payload_plan.py --execute`
- `.\.venv\Scripts\python.exe scripts\build_ds006072_comparable_validation.py`

## Blocker

Minimum paired ds006072 processed CIFTI payloads are local. Run the extraction writer, then unchanged scoring.
