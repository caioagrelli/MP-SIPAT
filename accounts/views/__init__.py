from functools import wraps
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required


def management_required(view_func):
    """Permite apenas superusuários, staff ou membros do grupo Gerencia."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        user = request.user
        if (
            user.is_superuser
            or user.is_staff
            or user.groups.filter(name='Gerencia').exists()
        ):
            return view_func(request, *args, **kwargs)
        raise PermissionDenied
    return wrapper
