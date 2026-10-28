# DOORS Next SRAC Exporter

A read-only reference exporter that converts selected IBM Engineering Requirements Management / DOORS Next records into a portable Safety Relevance Assertion Capability (SRAC) interchange document.

DOORS Next remains authoritative. This exporter neither writes to DOORS Next nor infers safety relevance, assigns ASIL, performs hazard analysis, or approves a safety decision. It transports already-authored lifecycle information and binds it to an explicit product and software-component identity.

## Architecture

The exporter is centered on IBM DOORS Next Reportable REST. The caller selects
the configuration explicitly in `config.example.json` and obtains the export
with `coverpage=true`. Before processing artifacts, the exporter verifies that
the configuration URI and name reported by the cover page match the selected
configuration. A mismatch fails closed.

The exporter does not query OSLC RM or attempt to discover configurations.
OSLC may be considered separately if a future use case requires configuration
discovery or capabilities outside this read-only export scope.

## Current scope

The initial implementation supports an offline Reportable REST response export. It produces:

- source URLs, project area, revision, and baseline/configuration context;
- explicit Reportable REST endpoint and selected configuration metadata;
- validation of `coverpage=true` configuration metadata;
- component pURL, version, and digest binding;
- an externally authored safety-relevance outcome and optional classification;
- review state, reviewer, timestamps, rationale, and traceability links; and
- a SHA-256 digest of the exact source response used for the export.

The response adapter is intentionally small and uses the normalized fixture
shape documented in
[docs/reportable-rest-field-mapping.md](docs/reportable-rest-field-mapping.md).
A deployment-specific client maps IBM Reportable REST output into that input
shape without changing the SRAC writer. HTTP authentication and retrieval stay
outside the converter so credentials never need to enter the interchange code.

## Run the demonstrator

```powershell
python -m doors_srac_exporter `
  --config config.example.json `
  --input fixtures/reportable-rest-response.json `
  --output srac-export.json
```

Validate the output:

```powershell
python -m doors_srac_exporter --validate srac-export.json
```

Run tests with:

```powershell
python -m unittest discover -s tests -v
```

## Security and deployment notes

- Use an organization-approved service identity and least-privilege, read-only access.
- Do not place credentials, access tokens, or real lifecycle records in the repository.
- Pin an export to a baseline or configuration before creating evidence for review.
- Pass the configuration URI explicitly and request `coverpage=true`; never infer
  the configuration from artifact names.
- Treat source URLs and evidence links as references; access control remains the responsibility of the source system.

## Status

This is a reference adapter and interchange demonstrator, not an IBM product integration or a claim of IBM endorsement.

