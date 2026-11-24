"""Synthetic acceptance for a reviewed HEAD replay only when BASE has no replay file."""
import copy
from contextlib import ExitStack
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from tools.gates import GateError, normalized_sha256
from tools import semantic_eval as semantic

PATH = 'docs/verification/semantic-baseline.json'
BASE = 'a' * 40
APPROVED_HEAD = 'b' * 40
BLOB = 'c' * 40
REPOSITORY = 'wyw-12345/CS5351'


class ReviewedHeadBaselineTests(unittest.TestCase):
    def setUp(self):
        self.main_exists = False
        self.blob = BLOB
        self.policy = {'status': 'active', 'reviewers': ['unohhh1', 'this-kong']}
        self.pr = {'number': 20, 'user': {'login': 'this-kong'},
                   'head': {'sha': APPROVED_HEAD, 'repo': {'full_name': REPOSITORY}},
                   'base': {'ref': 'main', 'repo': {'full_name': REPOSITORY}},
                   'state': 'open', 'merged': False}
        self.reviews = [{'user': {'login': 'unohhh1', 'type': 'User'}, 'state': 'APPROVED',
                         'commit_id': APPROVED_HEAD, 'submitted_at': '2026-11-23T11:58:43Z'}]
        self.baseline = {'fixture': 'reviewed replay data'}
        self.api = Mock(repository=REPOSITORY)
        self.api.get.side_effect = self.api_get
        self.api.pages.side_effect = lambda path: copy.deepcopy(self.reviews) if path == 'pulls/20/reviews' else []
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.git = self.stack.enter_context(patch.object(semantic, 'git', side_effect=self.git_call, create=True))
        self.base_read = self.stack.enter_context(patch.object(semantic, 'base_read', return_value=self.baseline))
        self.read = self.stack.enter_context(patch.object(semantic, 'read', return_value=self.baseline))
        self.stack.enter_context(patch.object(semantic, 'trusted_policy', return_value=self.policy))
        self.stack.enter_context(patch.object(semantic, 'GitHub', return_value=self.api, create=True))
        self.stack.enter_context(patch.dict('os.environ', {'GITHUB_REPOSITORY': REPOSITORY,
                                                        'GITHUB_TOKEN': 'synthetic-test-token'}, clear=True))

    def api_get(self, endpoint):
        if endpoint == 'pulls/20':
            return copy.deepcopy(self.pr)
        if endpoint == f'contents/{PATH}?ref={APPROVED_HEAD}':
            return {'type': 'file', 'path': PATH, 'sha': BLOB}
        raise AssertionError('Unexpected proof endpoint: ' + endpoint)

    def git_call(self, *args, **kwargs):
        if args[0] == 'ls-tree':
            return '100644 blob main-blob\t' + PATH if self.main_exists else ''
        if args[0] == 'rev-parse' and args[-1] == 'HEAD:' + PATH:
            return self.blob
        raise AssertionError('Unexpected Git proof operation: ' + repr(args))

    def load(self):
        # This proposed interface is intentionally absent before implementation.
        return getattr(semantic, 'load_reviewed_baseline')(BASE, api=self.api)

    def test_existing_base_has_priority_without_github_or_head(self):
        """REQ-GOV-B04: existing BASE evidence takes priority and never invokes fallback proof."""
        self.main_exists = True
        self.assertEqual(self.load(), self.baseline)
        self.base_read.assert_called_once_with(PATH, BASE)
        self.api.get.assert_not_called()
        self.read.assert_not_called()

    def test_only_missing_base_accepts_exact_independently_reviewed_head(self):
        """REQ-GOV-B04: missing BASE may use HEAD only after exact PR20 approval and blob proof."""
        self.assertEqual(self.load(), self.baseline)
        self.api.get.assert_any_call('pulls/20')
        self.api.get.assert_any_call(f'contents/{PATH}?ref={APPROVED_HEAD}')
        self.api.pages.assert_called_once_with('pulls/20/reviews')
        self.read.assert_called_once_with(PATH)
        self.base_read.assert_not_called()

    def test_existing_invalid_base_never_falls_back(self):
        """REQ-GOV-B04: a known BASE file failing validation/read is never replaced by HEAD."""
        self.main_exists = True
        self.base_read.side_effect = GateError('invalid base evidence')
        with self.assertRaises(GateError):
            self.load()
        self.api.get.assert_not_called()
        self.read.assert_not_called()

    def test_git_lookup_failure_is_not_treated_as_missing_file(self):
        """REQ-GOV-B04: failed Git proof cannot activate the missing-file fallback."""
        self.git.side_effect = GateError('unavailable base revision')
        with self.assertRaises(GateError):
            self.load()
        self.api.get.assert_not_called()

    def test_head_blob_must_match_approved_immutable_file(self):
        """REQ-GOV-B04: changed HEAD bytes cannot inherit approval of PR20's old artifact."""
        self.blob = 'd' * 40
        with self.assertRaises(GateError):
            self.load()

    def test_review_must_be_current_independent_human_and_allowlisted(self):
        """REQ-GOV-B04: stale, bot, self and unlisted approvals cannot authorise HEAD replay."""
        for name, kind, sha in [('unohhh1', 'User', 'e' * 40), ('unohhh1', 'Bot', APPROVED_HEAD),
                                ('this-kong', 'User', APPROVED_HEAD), ('outsider', 'User', APPROVED_HEAD)]:
            with self.subTest(name=name, kind=kind):
                self.reviews = [{'user': {'login': name, 'type': kind}, 'state': 'APPROVED',
                                 'commit_id': sha, 'submitted_at': '2026-11-23T11:58:43Z'}]
                with self.assertRaises(GateError):
                    self.load()

    def test_missing_or_withdrawn_approval_blocks(self):
        """REQ-GOV-B04: absent, dismissed or superseded reviews fail closed."""
        approved = copy.deepcopy(self.reviews[0])
        for state in ['NONE', 'DISMISSED', 'CHANGES_REQUESTED']:
            with self.subTest(state=state):
                self.reviews = [] if state == 'NONE' else [approved, dict(approved, state=state,
                                                                         submitted_at='2026-11-23T12:00:00Z')]
                with self.assertRaises(GateError):
                    self.load()

    def test_api_failure_or_nonfile_proof_blocks(self):
        """REQ-GOV-B04: unavailable approval API or non-file artifact proof cannot be trusted."""
        self.api.get.side_effect = OSError('synthetic unavailable API')
        with self.assertRaises(GateError):
            self.load()
        self.api.get.side_effect = lambda endpoint: self.pr if endpoint == 'pulls/20' else {'type': 'symlink', 'sha': BLOB}
        with self.assertRaises(GateError):
            self.load()

    def test_external_repository_or_non_main_proposal_is_rejected(self):
        """REQ-GOV-B04: the fallback proof belongs to this repository's main baseline proposal."""
        for field in ['repo', 'base']:
            original = copy.deepcopy(self.pr)
            if field == 'repo':
                self.pr['head']['repo']['full_name'] = 'outsider/fork'
            else:
                self.pr['base']['ref'] = 'untrusted-branch'
            with self.subTest(field=field), self.assertRaises(GateError):
                self.load()
            self.pr = original


class HeadReplayValidationTests(unittest.TestCase):
    def setUp(self):
        root = Path(semantic.ROOT)
        self.config = json.loads((root / 'docs/verification/model-evaluation.json').read_text(encoding='utf-8'))
        self.config.update(evaluation_approved=True, source_commit='fixture-source', test_baseline_sha='fixture-tests')
        self.dataset = json.loads((root / self.config['evaluation_path']).read_text(encoding='utf-8'))
        self.policy = json.loads((root / 'docs/verification/policy.json').read_text(encoding='utf-8'))
        paths = ['config/model.json', self.config['prompt_path'], self.config['evaluation_path'],
                 'src/feedback_engine.py', 'src/contracts.py', 'src/cli.py',
                 'scripts/advisory_worker.py', 'requirements-app.txt']
        runtime = {p: normalized_sha256(root / p) for p in paths}
        self.baseline = {'model': self.config['model'], 'prompt_sha256': runtime[self.config['prompt_path']],
                         'dataset_sha256': runtime[self.config['evaluation_path']],
                         'feedback_sha256': runtime['src/feedback_engine.py'], 'runtime_sha256': runtime,
                         'source_commit': 'fixture-source', 'test_baseline_sha': 'fixture-tests',
                         'real_provider': True, 'passed': True, 'human_acceptance': {'C': 'accepted', 'D': 'accepted'},
                         'checks': [], 'cases': []}
        for case in self.dataset['cases']:
            escalated = case['expected_status'] == 'escalated'
            criteria = [{'criterion_id': criterion['id'], 'suggested_score': None if escalated else '5',
                         'confidence': 0.5 if escalated else 0.9, 'uncertain': escalated,
                         'feedback': 'Synthetic test feedback; raw measurements unavailable.' if escalated else 'Synthetic support.',
                         'evidence_quote': case['essay']} for criterion in case['rubric']['criteria']]
            advice = {'status': case['expected_status'], 'reason': 'low_confidence' if escalated else None,
                      'feedback': {'criteria': criteria}, 'metadata': {'calls': 1, 'usage': {'prompt_tokens': 1, 'completion_tokens': 1, 'total_tokens': 2}}}
            self.baseline['cases'].append({'id': case['id'], 'advice': advice})
            self.baseline['checks'].append(dict.fromkeys(['schema_valid', 'criterion_coverage', 'supported_quotes', 'adversarial_ok', 'safe'], True))

    def run_saved(self):
        def read(path):
            return self.config if path.endswith('model-evaluation.json') else self.dataset
        with (patch.object(semantic, 'read', side_effect=read),
              patch.object(semantic, 'trusted_policy', return_value=self.policy),
              patch.object(semantic, 'load_reviewed_baseline', return_value=self.baseline, create=True) as load,
              patch.object(semantic, 'sha', side_effect=normalized_sha256, create=True),
              patch.dict('os.environ', {'GRADEAIDE_LIVE': '0'}, clear=True)):
            try:
                return semantic.run(BASE, replay=False)
            finally:
                load.assert_called_once_with(BASE)

    def test_fallback_preserves_fixed_case_and_threshold_revalidation(self):
        """REQ-GOV-B04: approved HEAD is still re-evaluated against fixed cases and hard limits."""
        result = self.run_saved()
        self.assertEqual(result['metrics']['safety_escapes'], 0)

    def test_stale_runtime_or_incomplete_acceptance_is_rejected(self):
        """REQ-GOV-B04: reviewed provenance never waives fingerprint or C/D acceptance checks."""
        original = copy.deepcopy(self.baseline)
        for change in ['runtime', 'acceptance', 'identity']:
            self.baseline = copy.deepcopy(original)
            if change == 'runtime':
                self.baseline['runtime_sha256']['src/cli.py'] = '0' * 64
            elif change == 'acceptance':
                self.baseline['human_acceptance']['D'] = 'pending'
            else:
                self.baseline['model'] = 'different-model'
            with self.subTest(change=change), self.assertRaises(GateError):
                self.run_saved()

    def test_saved_success_metrics_cannot_hide_strict_o2_failure(self):
        """REQ-GOV-B04: HEAD fallback recomputes O2 and rejects a score despite saved success."""
        row = next(row for row in self.baseline['cases'] if row['id'] == 'unverifiable-data')
        row['advice']['feedback']['criteria'][0]['suggested_score'] = '5'
        with self.assertRaises(GateError):
            self.run_saved()

    def test_missing_duplicate_or_unavailable_provider_case_is_rejected(self):
        """REQ-GOV-B04: fallback requires exactly the fixed case set and real provider usage."""
        original = copy.deepcopy(self.baseline)
        for change in ['missing', 'duplicate', 'usage']:
            self.baseline = copy.deepcopy(original)
            if change == 'missing':
                self.baseline['cases'].pop()
            elif change == 'duplicate':
                self.baseline['cases'][1] = self.baseline['cases'][0]
            else:
                self.baseline['cases'][0]['advice']['metadata']['usage'] = None
            with self.subTest(change=change), self.assertRaises(GateError):
                self.run_saved()
