# Validation — 2026-11-17

Passed:
- 10 unittest/Streamlit AppTest cases (see test-results.txt): allocation conservation, oversized/boundary jobs, price independence, invalid/overflow values, missing/expired/ambiguous/wrong-route rates, rate units and normalization, repeated runs, equipment switching invalidates displayed result, separate session defaults, no-job flow.
- All 16 archived source blobs verified against original Git object SHA-1s. SHA-256 included in provenance manifest.
- Python compile check and pip dependency consistency check.
- Streamlit launched locally; /_stcore/health and / both HTTP 200.
- Focused independent code review; date/text normalization and finite-overflow findings fixed. Equipment changes reset scenario input; now explicitly warned in UI before selection. No cross-session data path observed, not a security certification.
- Basic tracked-source scan found no credential-marker hits or data files among archived source files. Private code/commit metadata is still private, regardless of this scan.

Not done:
- Real browser screenshot/visual inspection, actual XLSX/CSV file uploader/download end-to-end tests.
- Docker image build (Docker unavailable) or hosted Render verification.
- Real carrier quote integration or live price averages.
- Authenticated company deployment. Public source publication subsequently authorized by repository owner.

Snapshot/history scope: original default-branch HEAD files plus 49 commit metadata entries across five repositories. Full Git histories remain on original repos. A private git ls-remote attempt could not authenticate; no mirror is claimed.

Publication review: all 35 tracked files scanned for secret patterns; archived Python string literals inspected for company/customer/account/contact identifiers. No matches found. All original commit identities are user/GitHub noreply addresses; no private email addresses found. Legacy rate constants remain unverified and are not market averages. No customer data files or databases are included.
