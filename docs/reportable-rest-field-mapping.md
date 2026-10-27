# Reportable REST field mapping

The adapter expects a normalized JSON response. A DOORS Next deployment maps its selected Reportable REST API output—or a controlled JRS report—to this shape before passing it to the writer.

| Normalized field | Source purpose | SRAC output |
| --- | --- | --- |
| `id`, `url`, `title` | Stable source artifact identity and human context | `source.artifact` |
| `revision` | Exact artifact revision | `source.revision` |
| `projectArea` | ELM project scope | `source.projectArea` |
| `configuration` | Baseline or configuration context | `source.configuration` |
| `attributes.safetyRelevance` | Existing safety-relevance determination | `assertion.outcome` |
| `attributes.classificationScheme`, `classificationValue` | Existing external classification reference | `assertion.classification` |
| `attributes.decisionStatus` | Existing lifecycle/review state | `assertion.decisionStatus` |
| `attributes.rationale` | Existing source explanation | `assertion.rationale` |
| `review.reviewedBy`, `review.reviewedAt` | Existing reviewer and timestamp | `assertion.review` |
| `links[]` | Evidence and traceability references | `evidence[]` |

## Required controls

The exporter rejects an artifact when it lacks a source URL, baseline/configuration, safety-relevance outcome, decision status, or a component pURL and digest from the supplied export configuration. It never chooses an ambiguous mapping or supplies a missing safety classification.

## Reportable REST versus JRS

Use Reportable REST for the first implementation because the adapter controls the selected fields and can retain raw response digests. JRS is appropriate later where a controlled, immutable report definition is already governed by the organization.

