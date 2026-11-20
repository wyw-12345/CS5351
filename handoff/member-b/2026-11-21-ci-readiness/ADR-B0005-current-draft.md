# ADR-B0005 update draft for the current A verification baseline

**Status:** Proposed for independent review. Candidate branch only. Extends the earlier B integration proposal held in PR #4.

The signed A API, CLI-injected configuration, prompt v1.2, and current fixed test set supersede the old B assumptions. Retain A's modules and configuration entry points. Record the actual API surface and governance document fingerprints, using LF-normalized SHA-256 for text snapshots. Verify the runtime permission boundary independently.

The live evaluator checks the current case reasons, matching criterion IDs, valid quotes, score and confidence bounds, and the absence of an authoritative total. It uses reviewed model/dataset configuration and runtime opt-in. Offline evaluator fixtures verify behavior without external calls. Rollback consists of discarding this isolated candidate before integrating it.

The team still needs real policy baseline approval, a reviewed transition for existing work, and a verified protected branch. Historical commits and the retrospective test proposal cannot supply prior approval. Any release change requires a reviewed exact-head diff and operational evidence.
