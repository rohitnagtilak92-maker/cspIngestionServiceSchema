from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class ReportFormat(str, Enum):
    """Which browser format the raw report arrived in."""

    CSP_REPORT = "csp-report"
    REPORTS_JSON = "reports+json"


class Disposition(str, Enum):
    ENFORCE = "enforce"
    REPORT = "report"


class CspViolationEvent(BaseModel):
    """The single internal shape every CSP violation report is normalized into.

    Produced by cspIngestionService (both application/csp-report and
    application/reports+json normalize into this), consumed by
    cspIngestionServiceLambdas and cspIngestionServiceApi.

    URL fields (document_uri, blocked_uri, source_file) are assumed already
    sanitized by cspIngestionService's sanitize.py before this model is
    constructed — this model does not re-sanitize them.
    """

    # --- normalized from the browser report ---
    document_uri: str
    referrer: str | None = None
    effective_directive: str
    violated_directive: str | None = None
    original_policy: str
    disposition: Disposition
    blocked_uri: str
    source_file: str | None = None
    line_number: int | None = None
    column_number: int | None = None
    status_code: int | None = None
    script_sample: str | None = None
    user_agent: str | None = None
    source_format: ReportFormat

    # --- enrichment, added by the collector itself ---
    app_id: str
    app_name: str
    environment: str
    aws_region: str
    service_version: str
    release: str | None = None
    request_id: str
    received_at: datetime
    client_ip: str

    model_config = {"extra": "forbid"}
