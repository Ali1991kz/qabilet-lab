import copy
import io
from unittest.mock import patch
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('rename', Path(__file__).parents[1] / 'scripts/rename-firebase-login.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)

class Fake:
    def __init__(self):
        self.email = r.OLD
        self.profile = {'updateTime': 'v1', 'fields': {k: {'stringValue': v} for k, v in {
            'id':'teacher_1', 'role':'teacher', 'email':r.OLD, 'classCode':'ABC123', 'name':'Teacher'}.items()}}
        self.writes = []
        self.occupied = False
        self.failure = None
    def lookup(self, **criteria):
        if criteria.get('email') == [r.NEW] and self.occupied:
            return [{'localId':'other', 'email':r.NEW}]
        if criteria.get('localId') == ['teacher_1'] or criteria.get('email') == [self.email]:
            return [{'localId':'teacher_1', 'email':self.email}]
        return []
    def document(self, uid):
        return copy.deepcopy(self.profile)
    def rename(self, uid, email):
        assert uid == 'teacher_1'
        self.email = email
        self.writes.append(('auth', email))
    def sync(self, uid, document):
        assert document['updateTime'] == 'v1'
        if self.failure == 'before':
            raise RuntimeError('Firestore rejected')
        self.profile['fields']['email']['stringValue'] = r.NEW
        self.writes.append(('profile', r.NEW))
        if self.failure == 'after':
            raise RuntimeError('Response lost')

class RenameTest(unittest.TestCase):
    def test_cloud_shell_credentials_include_quota_project_on_lookup(self):
        with patch.object(r.urllib.request, 'urlopen', return_value=io.BytesIO(b'{"users":[]}')) as call:
            r.AdminClient('test-token').lookup(email=[r.OLD])
        request = call.call_args.args[0]
        self.assertEqual(request.get_header('X-goog-user-project'), 'qabiletlab')
        self.assertEqual(request.get_header('Authorization'), 'Bearer test-token')

    def test_dry_run_has_no_writes(self):
        f=Fake();r.migrate(f);self.assertEqual(f.writes, [])
    def test_retains_identity_and_profile(self):
        f=Fake();before=copy.deepcopy(f.profile);r.migrate(f, True)
        before['fields']['email']['stringValue']=r.NEW
        self.assertEqual(f.profile, before);self.assertEqual(f.email, r.NEW)
    def test_occupied_target_stops_before_auth(self):
        f=Fake();f.occupied=True
        with self.assertRaises(RuntimeError):r.migrate(f, True)
        self.assertEqual(f.writes, [])
    def test_student_is_never_changed(self):
        f=Fake();f.profile['fields']['role']['stringValue']='student'
        with self.assertRaises(RuntimeError):r.migrate(f, True)
        self.assertEqual(f.writes, [])
    def test_firestore_failure_rolls_back_auth(self):
        f=Fake();f.failure='before'
        with self.assertRaisesRegex(RuntimeError, 'қайтарылды'):r.migrate(f, True)
        self.assertEqual(f.email, r.OLD);self.assertEqual(r.field(f.profile,'email'),r.OLD)
    def test_lost_commit_response_is_verified(self):
        f=Fake();f.failure='after';r.migrate(f, True)
        self.assertEqual(f.email, r.NEW);self.assertEqual(r.field(f.profile,'email'),r.NEW)

if __name__ == '__main__':unittest.main()
