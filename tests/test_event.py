from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from csp_ingestion_schema import CspViolationEvent, Disposition, ReportFormat


def _sample_kwargs(**overrides):
    kwargs = {
        "document_uri": "https://example.com/page",
        "referrer": "",
        "effective_directive": "script-src-elem",
        "violated_directive": "script-src-elem",
        "original_policy": "default-src 'self'; report-uri /v1/csp-report/csp_01ABC",
        "disposition": Disposition.ENFORCE,
        "blocked_uri": "https://evil.example/malicious.js",
        "source_file": "https://example.com/page",
        "line_number": 10,
        "column_number": 5,
        "status_code": 200,
        "script_sample": "",
        "user_agent": "Mozilla/5.0",
        "source_format": ReportFormat.CSP_REPORT,
        "app_id": "csp_01ABC",
        "app_name": "Marketing Site",
        "environment": "prod",
        "aws_region": "us-east-1",
        "service_version": "1.0.0",
        "release": None,
        "request_id": "req-123",
        "received_at": datetime.now(UTC),
        "client_ip": "203.0.113.7",
    }
    kwargs.update(overrides)
    return kwargs


def test_constructs_from_csp_report_shaped_fields():
    event = CspViolationEvent(**_sample_kwargs())
    assert event.app_id == "csp_01ABC"
    assert event.disposition is Disposition.ENFORCE
    assert event.source_format is ReportFormat.CSP_REPORT


def test_constructs_from_reports_json_shaped_fields():
    event = CspViolationEvent(
        **_sample_kwargs(
            source_format=ReportFormat.REPORTS_JSON,
            violated_directive=None,
            release="1.4.2",
        )
    )
    assert event.source_format is ReportFormat.REPORTS_JSON
    assert event.violated_directive is None
    assert event.release == "1.4.2"


def test_release_defaults_to_none_when_customer_has_not_set_it():
    event = CspViolationEvent(**_sample_kwargs())
    assert event.release is None


def test_original_policy_is_optional():
    kwargs = _sample_kwargs()
    del kwargs["original_policy"]
    event = CspViolationEvent(**kwargs)
    assert event.original_policy is None


def test_round_trip_serialization():
    event = CspViolationEvent(**_sample_kwargs(release="2.0.0"))
    payload = event.model_dump_json()
    restored = CspViolationEvent.model_validate_json(payload)
    assert restored == event


def test_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        CspViolationEvent(**_sample_kwargs(unexpected_field="nope"))


def test_requires_app_id():
    kwargs = _sample_kwargs()
    del kwargs["app_id"]
    with pytest.raises(ValidationError):
        CspViolationEvent(**kwargs)
