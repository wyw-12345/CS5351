"""ADR-0002/0003 / REQ-FUNC-010: synthetic signed workflow across fresh CLI processes."""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    steps = []
    with tempfile.TemporaryDirectory(prefix="gradeaide-signed-demo-") as folder:
        external = Path(folder)
        private, trust, approval = external / "teacher.pem", external / "trusted.json", external / "approval.json"
        db = external / "grades.sqlite3"
        env = dict(os.environ, PYTHONIOENCODING="utf-8", GRADEAIDE_TRUST_STORE=str(trust),
                   GRADEAIDE_SIGNING_PASSWORD="synthetic-test-only-not-a-real-credential")  # pragma: allowlist secret - synthetic value or environment variable name

        def run(*args, expected=0):
            process = subprocess.Popen([sys.executable, "-X", "utf8", "-m", "src.cli", *map(str, args)],
                                       cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate(timeout=20)
            steps.append({"command": args[0], "pid": process.pid, "returncode": process.returncode})
            if process.returncode != expected:
                raise RuntimeError(f"synthetic {args[0]} failed: {stderr.decode('utf-8')}")
            return json.loads(stdout) if stdout.strip() else None

        run("keygen", "--private-key", private, "--trust-file", trust, "--teacher-id", "synthetic-teacher")
        proposal = run("propose", "--essay", "examples/essay.txt", "--rubric", "examples/rubric.json",
                       "--submission-id", "synthetic-submission", "--fixture", "examples/provider-fixture.json",
                       "--db", db)
        assert proposal["status"] == "pending_review"
        assert run("show", "--id", proposal["id"], "--db", db) == proposal
        common = ["--id", proposal["id"], "--hash", proposal["hash"], "--scores",
                  "examples/accepted-scores.json", "--reviewer", "SYNTHETIC TEST", "--db", db]
        signed = run("sign", *common, "--private-key", private, "--confirm-sign")
        approval.write_text(json.dumps(signed), encoding="utf-8")
        approved = run("approve", *common, "--approval", approval)
        assert approved["final_score"] == "72.00" and approved["approval_authentication"] == "verified"
        assert run("show", "--id", proposal["id"], "--db", db) == approved
        assert run("approve", *common, "--approval", approval) == approved
        signed["signature"] = "00" * 64
        approval.write_text(json.dumps(signed), encoding="utf-8")
        run("approve", *common, "--approval", approval, expected=2)
        print(json.dumps({"mode": "synthetic; automated test signing, not human review; no API",
                          "steps": steps, "final_score": "72.00", "persisted_across_processes": True,
                          "idempotent_retry": True, "forged_signature_rejected": True,
                          "temporary_keys_and_database_removed_after_demo": True}, indent=2))


if __name__ == "__main__":
    main()
