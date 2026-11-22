# ADR-0005: proposed additional human reviewer

Status: proposed; not activated by this draft. Date: 2026-11-23.

Add Hanley-T to the existing human reviewer allowlist, retaining this-kong and unohhh1. GitHub readback confirms Hanley-T has write permission and PR #8 is authored by Chr11111s. The requester reports delegated authorization from this-kong; this is not an authenticated approval by this-kong and does not establish independence from all contributions.

An existing eligible reviewer must assess this change and whether Hanley-T independently reviewed the affected work. Hanley-T must not approve this own governance PR. No human approval is asserted by the assisting AI. An account allowlist does not make AI-generated review independent human review.

Scope: policy membership only. Keep status, thresholds, test baseline and required contexts unchanged. No historical tests-first exception is granted. The current PR #8 remains blocked until its remaining evidence is complete.

Activation: existing authorized human review and owner-controlled merge into main; then B synchronizes PR #8 with the new trusted base. B must update the PR's CODEOWNERS mapping consistently with the reviewer list and recheck the E02 equality test, accompanying safety snapshots/contracts and AI-use log under the existing governance procedure. main currently does not contain that CODEOWNERS file or those candidate snapshots; do not import the whole candidate into this small policy proposal.

After synchronization, a human using Hanley-T may submit their actual reviewed decision on the final PR #8 SHA, provided independence has been confirmed. Do not reuse an old approval or attribute a Hanley-T submission to this-kong. B reruns the gates against the updated base/head. This proposal does not claim CI success or fix bootstrap, mutation or semantic blockers.

Rollback: remove only Hanley-T from the policy through a reviewed governance change and synchronize the corresponding CODEOWNERS entries. Existing reviewers remain authorized.

Validation: parse policy JSON and assert only reviewers changed, preserving all existing members and all other policy fields. No application/runtime/test code is changed.