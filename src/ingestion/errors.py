"""Typed errors for the live-ingestion layer (Gate J1).

Error taxonomy (see phase J1 spec section 8):
- ConfigurationError      : invalid configuration (permanent; never retried)
- SourceUnavailableError  : network / HTTP / timeout (transient; bounded retry)
- SourceResponseError     : malformed or invalid source response (retried once, bounded)
- ValidationError         : client input / response semantic failure (permanent; NOT retried)
"""

from __future__ import annotations


class IngestionError(Exception):
    pass


class ConfigurationError(IngestionError):
    """Invalid configuration; do not retry."""


class SourceUnavailableError(IngestionError):
    """Network failure, timeout, or non-2xx from the source (transient)."""


class SourceResponseError(IngestionError):
    """Response received but could not be parsed or did not match the contract."""


class ValidationError(IngestionError):
    """Semantic validation failure; do not retry."""


RETRIABLE_ERRORS = (SourceUnavailableError, SourceResponseError)