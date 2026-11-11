#!/usr/bin/env python3
"""One-time owner-authorized ali12 -> gbm migration. Dry run unless --apply.
Uses the signed-in Cloud Shell user's temporary OAuth token; no key files.
Changes only Auth email and users/{same UID}.email. Does not change passwords.
"""
import argparse
import json
import re
import subprocess
import sys
import urllib.error
import urllib.request

PROJECT = 'qabiletlab'
OLD = 'ali12@users.qabiletlab.invalid'
NEW = 'gbm@users.qabiletlab.invalid'


class AdminClient:
    def __init__(self, token):
        self.token = token
        self.auth = f'https://identitytoolkit.googleapis.com/v1/projects/{PROJECT}/accounts:'
        self.database = f'projects/{PROJECT}/databases/(default)/documents'

    def request(self, url, body=None):
        data = None if body is None else json.dumps(body).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={
            'Authorization': 'Bearer ' + self.token,
            'Content-Type': 'application/json',
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            try:
                message = json.load(error).get('error', {}).get('message', 'HTTP error')
            except (ValueError, AttributeError):
                message = 'HTTP error'
            raise RuntimeError(f'Google API {error.code}: {str(message)[:240]}') from None

    def lookup(self, **criteria):
        return self.request(self.auth + 'lookup', criteria).get('users', [])

    def document(self, uid):
        return self.request('https://firestore.googleapis.com/v1/' + self.database + '/users/' + uid)

    def rename(self, uid, email):
        self.request(self.auth + 'update', {'localId': uid, 'email': email})

    def sync(self, uid, document):
        self.request('https://firestore.googleapis.com/v1/' + self.database + ':commit', {
            'writes': [{
                'update': {'name': self.database + '/users/' + uid,
                           'fields': {'email': {'stringValue': NEW}}},
                'updateMask': {'fieldPaths': ['email']},
                'currentDocument': {'updateTime': document['updateTime']},
            }],
        })


def field(document, name):
    return document.get('fields', {}).get(name, {}).get('stringValue')


def migrate(client, apply=False):
    accounts = client.lookup(email=[OLD])
    if len(accounts) != 1:
        raise RuntimeError('ali12 аккаунты табылмады. Аккаунт бұрын ауыстырылған болуы мүмкін; жаңа аккаунт құрылмайды.')
    account = accounts[0]
    uid = account.get('localId', '')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,128}', uid) or account.get('email') != OLD:
        raise RuntimeError('Аккаунт сәйкестігі расталмады.')
    if client.lookup(email=[NEW]):
        raise RuntimeError('gbm логині бос емес. Ештеңе өзгертілмеді.')
    document = client.document(uid)
    if field(document, 'id') != uid or field(document, 'role') != 'teacher' or field(document, 'email') != OLD:
        raise RuntimeError('Firestore мұғалім профилі сәйкес емес. Ештеңе өзгертілмеді.')
    if not document.get('updateTime'):
        raise RuntimeError('Профиль нұсқасы жоқ. Ештеңе өзгертілмеді.')
    print(f'Жоба: {PROJECT}; мұғалім UID: {uid}; логин: ali12 -> gbm')
    if not apply:
        print('Тек тексерілді. Өзгерту үшін --apply параметрі қажет.')
        return uid
    # Recheck the exact identity immediately before changing it.
    before = client.lookup(localId=[uid])
    if len(before) != 1 or before[0].get('email') != OLD:
        raise RuntimeError('Аккаунт басқа жерде өзгерді. Әрекет тоқтатылды.')
    try:
        client.rename(uid, NEW)
    except Exception:
        # A network failure can occur after Google has accepted the mutation.
        state = client.lookup(localId=[uid])
        if len(state) != 1 or state[0].get('email') != NEW:
            raise
    try:
        state = client.lookup(localId=[uid])
        if len(state) != 1 or state[0].get('localId') != uid or state[0].get('email') != NEW:
            raise RuntimeError('Auth өзгерісін растау орындалмады.')
        client.sync(uid, document)
    except Exception as original:
        try:
            current = client.document(uid)
            auth = client.lookup(localId=[uid])
            if len(auth) != 1 or auth[0].get('localId') != uid:
                raise RuntimeError('Auth сәйкестігін тексеру мүмкін емес.')
            if field(current, 'email') == NEW and auth[0].get('email') == NEW:
                pass  # Commit succeeded but its network response was lost.
            elif field(current, 'email') == OLD and auth[0].get('email') == NEW:
                client.rename(uid, OLD)
                reverted = client.lookup(localId=[uid])
                if len(reverted) != 1 or reverted[0].get('email') != OLD:
                    raise RuntimeError('Кері қайтаруды растау орындалмады.')
                raise RuntimeError('Профиль сақталмады. Auth бұрынғы ali12 логиніне қайтарылды.') from original
            else:
                raise RuntimeError('Деректер басқа жерде өзгерді; автоматты кері қайтару жасалмады.')
        except Exception as recovery:
            raise RuntimeError(f'Өзгеріс толық расталмады. UID {uid}. {recovery}') from None
    final_auth = client.lookup(localId=[uid])
    final_document = client.document(uid)
    if (len(final_auth) != 1 or final_auth[0].get('localId') != uid
            or final_auth[0].get('email') != NEW or field(final_document, 'email') != NEW):
        raise RuntimeError(f'Соңғы тексеру сәтсіз. UID {uid}: әкімші тексеруі қажет.')
    for name in ('id', 'role', 'teacherId', 'classCode', 'createdAt', 'name'):
        if final_document.get('fields', {}).get(name) != document.get('fields', {}).get(name):
            raise RuntimeError(f'Логин өзгерді, бірақ {name} өрісі қатар өзгерген. UID {uid}: әкімші тексеруі қажет.')
    print('ДАЙЫН: логин gbm. UID, құпиясөз және оқушылармен байланыс сақталды.')
    print('Сайттан шығып, gbm және бұрынғы құпиясөзбен қайта кіріңіз.')
    return uid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Apply the exact ali12 -> gbm migration')
    args = parser.parse_args()
    try:
        token = subprocess.check_output(
            ['gcloud', 'auth', 'print-access-token', '--project', PROJECT],
            text=True, timeout=120).strip()
        if not token:
            raise RuntimeError('Google әкімші сессиясы табылмады.')
        migrate(AdminClient(token), args.apply)
    except Exception as error:
        print('АЯҚТАЛМАДЫ: ' + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
