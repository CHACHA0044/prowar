"""
Tests for the chunked, transactional dataset ingestion engine.
SKIPPED: DB ingestion has been replaced by the static CSV architecture (Phase 2.6).
         The IngestionService is no longer used at runtime.  These tests are preserved
         for reference but marked skip to avoid import errors from removed DB settings.
"""

import pytest

pytestmark = pytest.mark.skip(
    reason="DB ingestion replaced by static CSV architecture (Phase 2.6). "
    "See backend/app/services/dataset_service.py for the current data layer."
)
