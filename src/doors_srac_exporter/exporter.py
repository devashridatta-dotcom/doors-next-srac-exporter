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


def _require_mapping(mapping: dict[str, Any], key: str, label: str) -> dict[str, Any]:
    value = _require(mapping, key, label)
    if not isinstance(value, dict):
        raise ValidationError(f"Expected {label} to be an object: {key}")
    return value


def _selected_configuration(
    config: dict[str, Any], response: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Validate the caller-selected Reportable REST configuration.

    Configuration discovery is intentionally outside this exporter. The caller
    selects a configuration URI, requests ``coverpage=true``, and supplies the
    resulting response. The response cover page must identify the same
    configuration before any artifacts are exported.
    """
    reportable_rest = _require_mapping(
        config, "reportableRest", "Reportable REST settings"
    )
    _require(reportable_rest, "endpoint", "Reportable REST endpoint")
    if reportable_rest.get("coverpage") is not True:
        raise ValidationError("Reportable REST export must be requested with coverpage=true")

    selected = _require_mapping(
        reportable_rest, "configuration", "explicit Reportable REST configuration"
    )
    selected_uri = _require(selected, "uri", "selected configuration URI")

    coverpage = _require_mapping(response, "coverpage", "Reportable REST cover page")
    actual = _require_mapping(
        coverpage, "configuration", "cover-page configuration metadata"
    )
    actual_uri = _require(actual, "uri", "cover-page configuration URI")
    if actual_uri != selected_uri:
        raise ValidationError(
            "Reportable REST response configuration does not match the "
            "explicitly selected configuration"
        )

    selected_name = selected.get("name")
    actual_name = actual.get("name")
    if selected_name and actual_name and selected_name != actual_name:
        raise ValidationError(
            "Reportable REST response configuration name does not match the "
            "explicitly selected configuration"
        )
    return reportable_rest, {
        "uri": selected_uri,
        "name": selected_name or actual_name,
    }


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
    source_document = _require_mapping(
        document, "sourceDocument", "source document metadata"
    )
    if source_document.get("interface") != "IBM DOORS Next Reportable REST":
        raise ValidationError("Unsupported source interface")
    _require(source_document, "endpoint", "Reportable REST endpoint")
    if source_document.get("coverpage") is not True:
        raise ValidationError("Source metadata must record coverpage=true")
    document_configuration = _require_mapping(
        source_document, "configuration", "selected source configuration"
    )
    document_configuration_uri = _require(
        document_configuration, "uri", "selected source configuration URI"
    )
    for assertion in assertions:
        _require(assertion, "outcome", "assertion outcome")
        _require(assertion, "decisionStatus", "assertion decision state")
        source = _require(assertion, "source", "assertion source")
        _require(source, "url", "source artifact URL")
        source_configuration = _require_mapping(
            source, "configuration", "source baseline or configuration"
        )
        source_configuration_uri = _require(
            source_configuration, "uri", "source configuration URI"
        )
        if source_configuration_uri != document_configuration_uri:
            raise ValidationError(
                "Assertion source configuration does not match source document"
            )


def export_document(config: dict[str, Any], response: dict[str, Any]) -> dict[str, Any]:
    """Create an SRAC interchange document from normalized response artifacts."""
    product = _require(config, "product", "configuration product")
    component = _require(config, "component", "configuration component")
    _require(component, "purl", "configuration component identity")
    digest = _require(component, "digest", "configuration component digest")
    _require(digest, "algorithm", "configuration component digest algorithm")
    _require(digest, "value", "configuration component digest value")

    reportable_rest, selected_configuration = _selected_configuration(config, response)

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
            "configuration": selected_configuration,
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
        "exporter": config.get(
            "exporter", {"name": "doors-next-srac-exporter", "version": "0.2.0"}
        ),
        "product": product,
        "component": component,
        "sourceDocument": {
            "interface": "IBM DOORS Next Reportable REST",
            "endpoint": reportable_rest["endpoint"],
            "coverpage": True,
            "configuration": selected_configuration,
            "digest": {"algorithm": "SHA-256", "value": canonical_digest(response)}
        },
        "assertions": assertions,
    }
    validate_document(document)
    return document

