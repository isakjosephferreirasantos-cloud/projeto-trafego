from functools import wraps

from flask import abort, redirect, request, url_for
from flask_login import current_user


def cargos_permitidos(*cargos):
    permitidos = frozenset(cargos)

    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for("auth.login", next=request.url))
            if current_user.cargo not in permitidos:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator
