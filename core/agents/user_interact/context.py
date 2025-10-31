import contextvars

_owner_id_ctx = contextvars.ContextVar("owner_id", default=None)


def set_owner_id(owner_id: str):
    _owner_id_ctx.set(owner_id)


def get_owner_id():
    return _owner_id_ctx.get()
