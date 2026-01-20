import base64
import os
import subprocess
import sys
import time
from collections.abc import Callable

import pytest
import requests
from flask import Response
from flask.testing import FlaskClient

from .config import TestConfig
from src.app import create_app

BASE_DIR_TESTS = os.path.abspath(os.path.dirname(__file__))

AUTH_ROOT_URL = '/api/auth'
AUTH_URL = f'{AUTH_ROOT_URL}/login'
LOGOUT_URL = f'{AUTH_ROOT_URL}/logout'
USER_URL = f'{AUTH_ROOT_URL}/users'
ROLES_URL = f'{AUTH_ROOT_URL}/roles'

EDUCATION_INSTITUTION_ROOT_URL = '/api/education-institution'
GROUPS_URL = f'{EDUCATION_INSTITUTION_ROOT_URL}/groups'
DISCIPLINES_URL = f'{EDUCATION_INSTITUTION_ROOT_URL}/disciplines'

BACKEND_HEALTHCHECK_URL = 'http://0.0.0.0:5000/healthcheck'

TESTS_BASE_URL = '/api/tests'
TESTS_URL = TESTS_BASE_URL
QUESTIONS_URL = f'{TESTS_BASE_URL}/questions'
QUESTION_TYPES_URL = f'{QUESTIONS_URL}/types'
ANSWERS_URL = f'{QUESTIONS_URL}/answers'

ADMIN_USERNAME = TestConfig.ADMIN_USERNAME
ADMIN_PASSWORD = TestConfig.ADMIN_PASSWORD
STUDENT_USERNAME = TestConfig.STUDENT_USERNAME
STUDENT_PASSWORD = TestConfig.STUDENT_PASSWORD

UNIQUE_NAME = (f'unique_name_{unique_name}' for unique_name in range(100_000))
UNIQUE_USERNAME = (f'username_{username}' for username in range(100_000))
UNIQUE_PASSWORD = (f'password_{password}' for password in range(100_000))
UNIQUE_EMAIL = (f'email{email}@yandex.ru' for email in range(100_000))
UNIQUE_GROUP = (str(group) for group in range(1_000, 9_999))
UNIQUE_DESCRIPTION = (f'description_{description}' for description in range(100_000))
UNIQUE_ANSWER = (f'answer_{answer}' for answer in range(100_000))


def assertion_info(url: str, response: Response) -> str:
    try:
        body = response.data.decode()
        msg = 'Response body is empty!'
    except UnicodeDecodeError as e:
        body = response.data
        msg = repr(e)
    return f'Assert from <{url}> | {body or msg}'


def app_client(test_client: FlaskClient):
    def _client(
        method: str,
        url: str,
        expected_code: int = None,
        headers: dict = None,
        query_string: dict = None,
        json: dict = None,
        data: dict = None,
        follow_redirects: bool = False,
    ) -> Response:
        status_codes_via_methods = {
            'GET': 200,
            'POST': 201,
            'PATCH': 200,
            'DELETE': 204,
        }

        r: Response = getattr(test_client, method.lower())(
            url,
            headers=headers,
            query_string=query_string,
            json=json,
            data=data,
            follow_redirects=follow_redirects,
        )

        if expected_code:
            assert r.status_code == expected_code, assertion_info(url, r)
            return r

        assert r.status_code == status_codes_via_methods[method], assertion_info(url, r)

        if method == 'DELETE':
            assert not r.data, assertion_info(url, r)
        elif r.headers['Content-Type'] == 'text/html; charset=utf-8':
            assert r.get_data(as_text=True), assertion_info(url, r)
        elif r.headers['Content-Type'] == 'text/plain; version=0.0.4; charset=utf-8':
            assert r.get_data(as_text=True), assertion_info(url, r)
        else:
            assert r.get_json(), assertion_info(url, r)

        return r

    return _client


def service_check(healthcheck_url: str, total_attempts: int = 10):
    for attempt in range(total_attempts):
        print(f'Initialization <{healthcheck_url}> attempt ({attempt}/{total_attempts})!')
        try:
            r = requests.get(healthcheck_url)
            r.raise_for_status()
            break
        except requests.ConnectionError as e:
            print(f'Connection error for <{healthcheck_url}> - {repr(e)}!')
            time.sleep(1)
        except requests.exceptions.HTTPError as e:
            print(f'HTTP error for <{healthcheck_url}> - {e.response.status_code}!')
            time.sleep(1)
    else:
        sys.exit()


@pytest.fixture(scope='session')
def fx_run_containers():
    # Run database container.
    subprocess.run(
        ['make', f'--directory={BASE_DIR_TESTS}/..', 'tests_start'], stdout=subprocess.PIPE
    ).stdout.decode('utf-8')

    service_check(BACKEND_HEALTHCHECK_URL)

    yield

    # Stop database container.
    subprocess.run(
        ['make', f'--directory={BASE_DIR_TESTS}/../..', 'stop'], stdout=subprocess.PIPE
    ).stdout.decode('utf-8')


@pytest.fixture(scope='session')
def fx_app(fx_run_containers):
    # Init app for testing.
    app = create_app(TestConfig)
    return app


@pytest.fixture
def fx_test_client(fx_app):
    # Init app for testing.
    app_context = fx_app.app_context()
    app_context.push()

    with fx_app.test_client() as test_client:
        yield test_client

    # Stop app for testing.
    app_context.pop()


@pytest.fixture
def fx_test_hub_client(fx_test_client) -> Callable[..., Response]:
    return app_client(fx_test_client)


@pytest.fixture
def fx_make_header_basic():
    def _make_header(username: str, password: str) -> dict:
        username_password = f'{username}:{password}'
        token_username_password = (
            f"Basic {base64.b64encode(username_password.encode('UTF-8')).decode()}"
        )
        return {'Authorization': token_username_password}

    return _make_header


@pytest.fixture
def fx_make_header_bearer():
    def _make_header(token) -> dict:
        return {'Authorization': f'Bearer {token}'}

    return _make_header


@pytest.fixture
def fx_admin_header(fx_test_hub_client, fx_make_header_basic, fx_make_header_bearer):
    tokens = fx_test_hub_client(
        'GET', AUTH_URL, headers=fx_make_header_basic(ADMIN_USERNAME, ADMIN_PASSWORD)
    ).json
    return fx_make_header_bearer(tokens['access_token'])


@pytest.fixture
def fx_student_header(fx_test_hub_client, fx_make_header_basic, fx_make_header_bearer):
    tokens = fx_test_hub_client(
        'GET', AUTH_URL, headers=fx_make_header_basic(STUDENT_USERNAME, STUDENT_PASSWORD)
    ).json
    return fx_make_header_bearer(tokens['access_token'])


@pytest.fixture
def fx_users_non_deletion(fx_test_hub_client, fx_admin_header):
    def _create_user(username: str, password: str, email: str, group_id: str, role_id: str):
        user_payload = {
            'username': username,
            'password': password,
            'email': email,
            'group_id': group_id,
            'role_id': role_id,
        }
        new_user = fx_test_hub_client('POST', USER_URL, headers=fx_admin_header, json=user_payload)
        created_user = fx_test_hub_client(
            'GET', USER_URL, headers=fx_admin_header, query_string={'id': new_user.json['id']}
        )
        return created_user.json['items'][0]

    return _create_user


@pytest.fixture
def fx_users(fx_test_hub_client, fx_users_non_deletion, fx_admin_header, fx_roles, fx_groups):
    users_ids = []

    def _add_created_user_in_list(
        username: str = None,
        password: str = None,
        email: str = None,
        group_id: str = None,
        role_id: str = None,
    ):
        payload = {
            'username': username or next(UNIQUE_USERNAME),
            'password': password or next(UNIQUE_PASSWORD),
            'email': email or next(UNIQUE_EMAIL),
            'group_id': group_id or fx_groups()['id'],
            'role_id': role_id or fx_roles()['id'],
        }
        new_user = fx_users_non_deletion(**payload)
        users_ids.append(new_user['id'])
        return new_user

    yield _add_created_user_in_list

    for user_id in users_ids:
        fx_test_hub_client('DELETE', USER_URL, headers=fx_admin_header, json={'id': user_id})
        user = fx_test_hub_client(
            'GET', USER_URL, headers=fx_admin_header, query_string={'id': user_id}
        )
        assert not user.json['items']


@pytest.fixture
def fx_roles(fx_test_hub_client, fx_admin_header):
    def _get_role(role_name: str = 'student'):
        role = fx_test_hub_client(
            'GET', ROLES_URL, headers=fx_admin_header, query_string={'unique_name': role_name}
        )
        return role.json['items'][0]

    return _get_role


@pytest.fixture
def fx_groups_non_deletion(fx_test_hub_client, fx_admin_header):
    def _create_group(unique_name: str = None):
        new_group = fx_test_hub_client(
            'POST',
            GROUPS_URL,
            headers=fx_admin_header,
            json={'unique_name': unique_name or next(UNIQUE_GROUP)},
        )
        created_group = fx_test_hub_client(
            'GET', GROUPS_URL, headers=fx_admin_header, query_string={'id': new_group.json['id']}
        )
        return created_group.json['items'][0]

    return _create_group


@pytest.fixture
def fx_groups(fx_test_hub_client, fx_groups_non_deletion, fx_admin_header):
    groups_ids = []

    def _add_created_group_in_list(unique_name: str = None):
        payload = {'unique_name': unique_name or next(UNIQUE_GROUP)}
        new_group = fx_groups_non_deletion(**payload)
        groups_ids.append(new_group['id'])
        return new_group

    yield _add_created_group_in_list

    for group_id in groups_ids:
        fx_test_hub_client('DELETE', GROUPS_URL, headers=fx_admin_header, json={'id': group_id})
        group = fx_test_hub_client(
            'GET', GROUPS_URL, headers=fx_admin_header, query_string={'id': group_id}
        )
        assert not group.json['items']


@pytest.fixture
def fx_disciplines_non_deletion(fx_test_hub_client, fx_admin_header):
    def _create_discipline(unique_name: str = None):
        new_discipline = fx_test_hub_client(
            'POST',
            DISCIPLINES_URL,
            headers=fx_admin_header,
            json={
                'unique_name': unique_name or next(UNIQUE_NAME),
            },
        )
        created_discipline = fx_test_hub_client(
            'GET',
            DISCIPLINES_URL,
            headers=fx_admin_header,
            query_string={'id': new_discipline.json['id']},
        )
        return created_discipline.json['items'][0]

    return _create_discipline


@pytest.fixture
def fx_disciplines(fx_test_hub_client, fx_disciplines_non_deletion, fx_admin_header):
    disciplines_ids = []

    def _add_created_discipline_in_list(unique_name: str = None):
        payload = {'unique_name': unique_name or next(UNIQUE_NAME)}
        new_discipline = fx_disciplines_non_deletion(**payload)
        disciplines_ids.append(new_discipline['id'])
        return new_discipline

    yield _add_created_discipline_in_list

    for discipline_id in disciplines_ids:
        fx_test_hub_client(
            'DELETE', DISCIPLINES_URL, headers=fx_admin_header, json={'id': discipline_id}
        )
        discipline = fx_test_hub_client(
            'GET', DISCIPLINES_URL, headers=fx_admin_header, query_string={'id': discipline_id}
        )
        assert not discipline.json['items']


@pytest.fixture
def fx_tests_non_deletion(fx_test_hub_client, fx_admin_header):
    def _create_test(**kwargs):
        new_test = fx_test_hub_client('POST', TESTS_URL, headers=fx_admin_header, json={**kwargs})
        created_test = fx_test_hub_client(
            'GET',
            TESTS_URL,
            headers=fx_admin_header,
            query_string={'id': new_test.json['id']},
        )
        return created_test.json['items'][0]

    return _create_test


@pytest.fixture
def fx_tests(fx_test_hub_client, fx_tests_non_deletion, fx_disciplines, fx_groups, fx_admin_header):
    tests_ids = []

    def _add_created_test_in_list(
        unique_name: str = None,
        group_id: str = None,
        discipline_id: str = None,
        with_question: bool = False,
        with_answer: bool = False,
    ):
        payload = {
            'unique_name': unique_name or next(UNIQUE_NAME),
            'group_id': group_id or fx_groups()['id'],
            'discipline_id': discipline_id or fx_disciplines()['id'],
        }
        new_test = fx_tests_non_deletion(**payload)
        tests_ids.append(new_test['id'])
        return new_test

    yield _add_created_test_in_list

    for test_id in tests_ids:
        fx_test_hub_client('DELETE', TESTS_URL, headers=fx_admin_header, json={'id': test_id})
        test = fx_test_hub_client(
            'GET', TESTS_URL, headers=fx_admin_header, query_string={'id': test_id}
        )
        assert not test.json['items']


@pytest.fixture
def fx_get_question_type(fx_test_hub_client, fx_admin_header):
    def _get_type(_id: str = None, unique_name: str = 'one'):
        query = {'id': _id} if _id else {'unique_name': unique_name}
        created_test = fx_test_hub_client(
            'GET', QUESTION_TYPES_URL, headers=fx_admin_header, query_string=query
        )
        return created_test.json['items'][0]

    return _get_type


@pytest.fixture
def fx_questions_non_deletion(fx_test_hub_client, fx_admin_header):
    def _create_question(**kwargs):
        new_question = fx_test_hub_client(
            'POST', QUESTIONS_URL, headers=fx_admin_header, json={**kwargs}
        )
        created_question = fx_test_hub_client(
            'GET',
            QUESTIONS_URL,
            headers=fx_admin_header,
            query_string={'id': new_question.json['id']},
        )
        return created_question.json['items'][0]

    return _create_question


@pytest.fixture
def fx_questions(
    fx_test_hub_client, fx_questions_non_deletion, fx_get_question_type, fx_tests, fx_admin_header
):
    questions_ids = []

    def _add_created_question_in_list(
        unique_name: str = None,
        test_id: str = None,
        type_id: str = None,
        with_answer: bool = False,
    ):
        payload = {
            'unique_name': unique_name or next(UNIQUE_NAME),
            'test_id': test_id or fx_tests()['id'],
            'type_id': type_id or fx_get_question_type()['id'],
        }
        new_question = fx_questions_non_deletion(**payload)
        questions_ids.append(new_question['id'])
        return new_question

    yield _add_created_question_in_list

    for question_id in questions_ids:
        fx_test_hub_client(
            'DELETE', QUESTIONS_URL, headers=fx_admin_header, json={'id': question_id}
        )
        question = fx_test_hub_client(
            'GET', QUESTIONS_URL, headers=fx_admin_header, query_string={'id': question_id}
        )
        assert not question.json['items']


@pytest.fixture
def fx_answers_non_deletion(fx_test_hub_client, fx_admin_header):
    def _create_answer(**kwargs):
        new_answer = fx_test_hub_client(
            'POST', ANSWERS_URL, headers=fx_admin_header, json={**kwargs}
        )
        created_answer = fx_test_hub_client(
            'GET',
            ANSWERS_URL,
            headers=fx_admin_header,
            query_string={'id': new_answer.json['id']},
        )
        return created_answer.json['items'][0]

    return _create_answer


@pytest.fixture
def fx_answers(fx_test_hub_client, fx_answers_non_deletion, fx_questions, fx_admin_header):
    answers_ids = []

    def _add_created_answer_in_list(
        unique_name: str = None,
        question_id: str = None,
        is_correct: bool = False,
        answer: str = None,
    ):
        payload = {
            'unique_name': unique_name or next(UNIQUE_ANSWER),
            'is_correct': is_correct,
            'question_id': question_id or fx_questions()['id'],
        }
        new_answer = fx_answers_non_deletion(**payload)
        answers_ids.append(new_answer['id'])
        return new_answer

    yield _add_created_answer_in_list

    for answer_id in answers_ids:
        fx_test_hub_client('DELETE', ANSWERS_URL, headers=fx_admin_header, json={'id': answer_id})
        answer = fx_test_hub_client(
            'GET', ANSWERS_URL, headers=fx_admin_header, query_string={'id': answer_id}
        )
        assert not answer.json['items']
