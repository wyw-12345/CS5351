# B tests-only review on the current A implementation

**Baseline:** A `10f5b8de9b9f51fd60cd227ee7d8b71c78970c10`, with D ADR-0001 through ADR-0003. This is an independent acceptance candidate for existing A code. It records no retroactive implementation approval.

The previous B REQ patch targeted eight obsolete test contexts. The current A branch already covers most of those behaviors. The changes to A's existing tests expand seven shorthand requirement annotations into registered IDs. Their executable ASTs match the original functions. The updated B suite uses the current signed approval API with ephemeral fixture keys. Independent arithmetic oracles, durable-state checks and privacy checks cover all eight invariants; the runtime isolation portion of REQ-INV-007 remains open.

| Check | Result |
| --- | --- |
| `python -m unittest discover -s test/offline` | 73 passed, including all 65 A tests and the 8 updated B tests. |
| `python -m unittest discover -s test/governance -v` | 3 passed, including a fresh local benchmark, a credential-free subprocess run with a Python loopback guard, and exact checks of registered IDs and mapped locators. The loopback guard covers the test runner process. OS isolation is a separate requirement. |
| `python scripts/validate_requirements.py --strict --json` | Registry/schema pass. 37 of 47 REQ IDs have executable test locators. Exit 2 indicates incomplete traceability. Every ID appears in the map, with missing locators and partial verification explicitly described. |
| Ruff `E4,E7,E9,F,I` on `test/` with `scripts, src, test` marked first-party | Passed. |

No live provider requests were made. The ten gaps in strict coverage belong to the current live-performance run (PERF-003), approval/CI governance (B01/B02/B05/B06), E's permission, review and module/tool controls (E01–E04), and requirement co-evolution enforcement (C01). Locators already present in the map can still have pending external or human evidence. Invariant entries marked negative describe linked negative cases. Mutation status is separate.

**Next review:** A/D confirm that the new fixtures use the intended approval and persistence contracts. C reviews the test map and any registry verification strings that refer to older governing files. The independent test reviewer reviews the exact SHA. B then adapts the CI and snapshots against this test baseline. E owns the OpenCode runtime and permission evidence. A/B can produce current live performance results after the model run is authorized.
