# Reportable REST field mapping

The adapter expects a normalized JSON response from a caller-selected DOORS
Next Reportable REST configuration. The request must include `coverpage=true`.
The adapter does not discover configurations through OSLC.

| Normalized field | Source purpose | SRAC output |
| --- | --- | --- |
| `config.reportableRest.endpoint` | Explicit Reportable REST endpoint | `sourceDocument.endpoint` |
| `config.reportableRest.configuration` | Caller-selected configuration URI and name | `sourceDocument.configuration` and each `assertion.source.configuration` |
| `coverpage.configuration` | Configuration metadata returned with `coverpage=true` | Validated against the caller-selected configuration |
| `id`, `url`, `title` | Stable source artifact identity and human context | `source.artifactId`, `source.url`, `source.title` |
| `revision` | Exact artifact revision | `source.revision` |
| `projectArea` | ELM project scope | `source.projectArea` |
| `attributes.safetyRelevance` | Existing safety-relevance determination | `assertion.outcome` |
| `attributes.classificationScheme`, `classificationValue` | Existing external classification reference | `assertion.classification` |
| `attributes.decisionStatus` | Existing lifecycle/review state | `assertion.decisionStatus` |
| `attributes.rationale` | Existing source explanation | `assertion.rationale` |
| `review.reviewedBy`, `review.reviewedAt` | Existing reviewer and timestamp | `assertion.review` |
| `links[]` | Evidence and traceability references | `evidence[]` |

## Required controls

The exporter rejects an export when the selected configuration is absent, when
`coverpage=true` is not recorded, or when the response cover-page configuration
does not match the explicit selection. It also rejects artifacts that lack a
source URL, safety-relevance outcome, or decision status, and rejects exports
without a component pURL and digest. It never chooses an ambiguous mapping or
supplies a missing safety classification.

## Why Reportable REST

Reportable REST is the reference interface because it supplies artifact
identity, attributes, traceability, revisions, configuration-aware links, and
configuration metadata through the cover page. JRS and OSLC RM are outside the
current implementation. OSLC RM would only be reconsidered if future scope
requires configuration discovery or another capability not provided by the
selected Reportable REST export.

