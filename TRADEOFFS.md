# Tradeoffs

1. I did not build authentication and role-based tenant access. The data model is tenant-scoped, but production auth would need SSO, tenant-aware permissions, and reviewer/approver roles. Building a fake login would add noise without proving the ingestion model.

2. I did not build live SAP, utility, or Concur API connectors. The assignment asks for realistic shapes, and real connectors would mostly be credential handling, customer setup, retries, and vendor-specific edge cases. CSV ingestion keeps the prototype reviewable while preserving source lineage.

3. I did not build a full emission-factor library. Factors are fixed at import time in a small map so the audit behavior is explicit. A production factor service would need geography, date validity, factor source/versioning, and category-specific calculation methods.
