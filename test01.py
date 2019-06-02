import os
import string
import random
import time
import unittest

import requests
import sys

DEBUG = "-doc" in sys.argv

if DEBUG:
    sys.argv.remove("-doc")
    print("DEBUG mode on\n")

DELAY_INTERVAL = 2  # seconds

api_server_address = os.environ.get('API_SERVER_ADDRESS', default='127.0.0.1:80')


def make_api_url(path: str) -> str:
    return 'http://' + api_server_address + '/api/v0' + path


def make_public_api_url(path: str) -> str:
    return make_api_url('/public' + path)


def make_protected_api_url(path: str) -> str:
    return make_api_url('/protected' + path)


def rand_str(n: int = 10) -> str:
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(n))


def rand_email() -> str:
    return 'user' + rand_str(10) + '@example.com'


def rand_password() -> str:
    return rand_str(10)


class TestSum(unittest.TestCase):
    def test_case01(self):
        credentials = {
            'email': rand_email(),
            'password': rand_password(),
        }

        if DEBUG:
            print("credentials: ", credentials)

        r = requests.post(url=make_public_api_url('/auth/profiles'), json=credentials)
        self.assertEqual(r.status_code, 200)

        if DEBUG:
            print('profile_status: ', r.json())

        info = r.json()
        user_id = info['userId']
        self.assertNotEqual(user_id, '')

        time.sleep(DELAY_INTERVAL)

        r = requests.post(url=make_public_api_url('/auth/sessions'), json=credentials)
        self.assertEqual(r.status_code, 200)

        session = r.json()
        session_id = session['sessionId']
        auth_token = session['authToken']
        self.assertNotEqual(session_id, '')
        self.assertNotEqual(auth_token, '')

        headers = {
            'Authorization': 'Bearer ' + auth_token
        }

        if DEBUG:
            print("headers: ", headers)

        r = requests.get(url=make_public_api_url('/users/' + user_id + '/profile'), headers=headers)
        self.assertEqual(r.status_code, 200)

        profile = r.json()

        if DEBUG:
            print('profile: ', r.json())

        profile_update = {
            'username':    'the_' + profile['username'],
            'fullName':    'The Full Name',
            'dateOfBirth': '2000-01-01',
        }

        r = requests.patch(url=make_protected_api_url('/users/' + user_id + '/profile'),
                           json=profile_update, headers=headers)
        self.assertEqual(r.status_code, 200)

        r = requests.get(url=make_public_api_url('/users/' + user_id + '/profile'), headers=headers)
        self.assertEqual(r.status_code, 200)

        profile = r.json()

        if DEBUG:
            print('new profile: ', profile)

        r = requests.get(url=make_public_api_url('/users?username=' + profile['username']), headers=headers)
        self.assertEqual(r.status_code, 200)

        if DEBUG:
            print('search by username: ', r.json())

        r = requests.get(url=make_protected_api_url('/documents?owner_id=' + user_id), headers=headers)
        self.assertEqual(r.status_code, 404)

        document_info = {
            'title':   'title',
            'subject': 'subject',
        }

        r = requests.post(url=make_protected_api_url('/documents'), json=document_info, headers=headers)
        self.assertEqual(r.status_code, 200)

        document_info = r.json()
        document_id = document_info['documentId']
        self.assertNotEqual(document_id, '')

        if DEBUG:
            print("document_id: ", document_id)

        r = requests.get(url=make_protected_api_url('/documents/' + document_id + '/content'), headers=headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, b'')

        document_content = b'raw_document_content'

        if DEBUG:
            print("document_content: ", document_content)

        r = requests.patch(url=make_protected_api_url('/documents/' + document_id + '/content'),
                           data=document_content, headers=headers)
        self.assertEqual(r.status_code, 200)

        r = requests.get(url=make_protected_api_url('/documents/' + document_id + '/content'), headers=headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.content, document_content)

        r = requests.delete(url=make_protected_api_url('/auth/sessions/' + session_id), headers=headers)
        self.assertEqual(r.status_code, 200)


if __name__ == '__main__':
    unittest.main()
