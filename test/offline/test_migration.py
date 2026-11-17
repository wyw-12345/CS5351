"""ADR-0003 / REQ-INV-006: real SQLite v1 migration, rollback and historical provenance."""
import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from src.contracts import canonical, digest
from src.grade_store import GradeStore
from test.support import ESSAY, RUBRIC, SCORES, feedback


class MigrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "legacy.sqlite3"
        self.payload = {"essay": ESSAY, "rubric": RUBRIC, "advice": {
            "status": "pending_review", "reason": None, "feedback": feedback(), "metadata": {}},
            "essay_hash": digest(ESSAY), "rubric_hash": digest(RUBRIC), "created_at": "historical"}
        self.audit = {"proposal_id": "old", "proposal_hash": digest(self.payload),
                      "reviewer": "old audit label", "reason": "", "accepted_scores": SCORES,
                      "final_score": "72.00", "approved_at": "historical",
                      "calculator_version": "1.0", "previous_status": "pending_review"}
        with closing(sqlite3.connect(self.path)) as db, db:
            db.executescript("CREATE TABLE proposals(id TEXT PRIMARY KEY, payload TEXT, digest TEXT, status TEXT);"
                             "CREATE TABLE grades(proposal_id TEXT PRIMARY KEY, score TEXT, audit TEXT, digest TEXT);"
                             "PRAGMA user_version=1;")
            db.execute("INSERT INTO proposals VALUES (?,?,?,?)",
                       ("old", canonical(self.payload), digest(self.payload), "approved"))
            db.execute("INSERT INTO grades VALUES (?,?,?,?)",
                       ("old", "72.00", canonical(self.audit), digest(self.audit)))

    def test_legacy_migration_retains_unsigned_history(self):
        """REQ-INV-003/006: old records remain explicit unverified history, with original payload bytes."""
        with GradeStore(self.path, migrate_legacy=True) as store:
            result = store.get("old")
            self.assertEqual(result["final_score"], "72.00")
            self.assertEqual(result["approval_authentication"], "legacy_unverified")
            self.assertEqual(result["submission_id"], "legacy:old")
            self.assertEqual(result["proposal"], self.payload)
            self.assertEqual(result["audit"], self.audit)
            self.assertEqual(store.connection.execute("PRAGMA user_version").fetchone()[0], 2)
            with self.assertRaises(PermissionError):
                store.approve("old", result["hash"], SCORES, "teacher")
        with GradeStore(self.path, migrate_legacy=True) as store:
            self.assertEqual(store.get("old"), result)

    def test_corrupt_legacy_migration_rolls_back_schema(self):
        """REQ-INV-006: corrupt source aborts migration without committing ALTER TABLE."""
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE proposals SET digest='corrupted'")
        with self.assertRaises(ValueError):
            GradeStore(self.path, migrate_legacy=True)
        with closing(sqlite3.connect(self.path)) as db, db:
            self.assertEqual(db.execute("PRAGMA user_version").fetchone()[0], 1)
            columns = {r[1] for r in db.execute("PRAGMA table_info(proposals)")}
            self.assertNotIn("submission_id", columns)
            self.assertEqual(db.execute("SELECT digest FROM proposals").fetchone()[0], "corrupted")

    def test_unknown_schema_preserves_file(self):
        """REQ-INV-006: refuse unsupported database versions without changing existing bytes."""
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("PRAGMA user_version=99")
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            GradeStore(self.path, migrate_legacy=True)
        self.assertEqual(self.path.read_bytes(), before)


    def test_default_open_cannot_implicitly_migrate(self):
        """REQ-FUNC-007 / REQ-INV-006: ordinary inspection cannot silently migrate a v1 database."""
        before = self.path.read_bytes()
        with self.assertRaises(ValueError):
            GradeStore(self.path)
        self.assertEqual(self.path.read_bytes(), before)
