"""Pure conversion and validation functions for the reference exporter."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any


class ValidationError(ValueError):
    """Raised when an export lacks required provenance or identity data."""


def canonical_digest(value: Any) -> str:
    """Return a deterministic SHA-256 digest of JSON-compatible input."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _require(mapping: dict[str, Any], key: str, label: str) -> Any:
    value = mapping.get(key)
    if value is None or value == "":
        raise ValidationError(f"Missing required {label}: {key}")
    return value


def validate_document(document: dict[str, Any]) -> None:
    if document.get("schema") != "https://example.org/srac/interchange/v0.1":
        raise ValidationError("Unsupported or missing SRAC interchange schema")
    _require(document, "product", "product")
    _require(document, "component", "component")
    assertions = _require(document, "assertions", "assertions")
    if not isinstance(assertions, list) or not assertions:
        raise ValidationError("At least one assertion is required")
    component = document["component"]
    _require(component, "purl", "component identity")
    digest = _require(component, "digest", "component digest")
    _require(digest, "algorithm", "component digest algorithm")
    _require(digest, "value", "component digest value")
    for assertion in assertions:
        _require(assertion, "outcome", "assertion outcome")
        _require(assertion, "decisionStatus", "assertion decision state")
        source = _require(assertion, "source", "assertion source")
        _require(source, "url", "source artifact URL")
        _require(source, "configuration", "source baseline or configuration")


def export_document(config: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    """Create an SRAC interchange document from normalized response artifacts."""
    product = _require(config, "product", "configuration product")
    component = _require(config, "component", "configuration component")
    _require(component, "purl", "configuration component identity")
    digest = _require(component, "digest", "configuration component digest")
    _require(digest, "algorithm", "configuration component digest algorithm")
    _require(digest, "value", "configuration component digest value")

    artifacts = _require(response, "artifacts", "response artifacts")
    if not isinstance(artifacts, list) or not artifacts:
        raise ValidationError("Response must contain at least one artifact")

    assertions: list[dict[str, Any]] = []
    for artifact in artifacts:
        attrs = _require(artifact, "attributes", "artifact attributes")
        review = artifact.get("review", {})
        source = {
            "system": "DOORS Next / ELM",
            "artifactId": _require(artifact, "id", "artifact identity"),
            "url": _require(artifact, "url", "artifact source URL"),
            "title": artifact.get("title"),
            "revision": artifact.get("revision"),
            "projectArea": artifact.get("projectArea"),
            "configuration": _require(artifact, "configuration", "artifact baseline or configuration"),
        }
        assertions.append(
            {
                "id": f"doors-next:{source['artifactId']}:{source['revision'] or 'unversioned'}",
                "outcome": _require(attrs, "safetyRelevance", "safety-relevance outcome"),
                "rationale": attrs.get("rationale"),
                "classification": {
                    "scheme": attrs.get("classificationScheme"),
                    "value": attrs.get("classificationValue"),
                },
                "decisionStatus": _require(attrs, "decisionStatus", "decision status"),
                "review": {
                    "reviewedBy": review.get("reviewedBy"),
                    "reviewedAt": review.get("reviewedAt"),
                },
                "source": source,
                "evidence": artifact.get("links", []),
            }
        )

    document = {
        "schema": "https://example.org/srac/interchange/v0.1",
        "generatedAt": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "exporter": config.get("exporter", {"name": "doors-next-srac-exporter", "version": "0.1.0"}),
        "product": product,
        "component": component,
        "sourceDocument": {
            "digest": {"algorithm": "SHA-256", "value": canonical_digest(response)}
        },
        "assertions": assertions,
    }
    validate_document(document)
    return document

