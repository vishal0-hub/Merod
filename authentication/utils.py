from importlib import import_module

from django.conf import settings


def normalize_email(value: str) -> str:
    return value.strip().lower()


def get_session_key(request):
    return request.data.get('session_key') or request.COOKIES.get(settings.SESSION_COOKIE_NAME)


def get_session_store(session_key):
    session_engine = import_module(settings.SESSION_ENGINE)
    return session_engine.SessionStore(session_key=session_key)


def get_user_id_from_session(session_key):
    session_data = get_session_store(session_key).load()
    return session_data.get('_auth_user_id')
