from django.shortcuts import redirect


class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    EXEMPT_PREFIXES = ('/access/trocar-senha/', '/login/', '/logout/', '/admin/', '/static/', '/media/', '/oidc/')

    def __call__(self, request):
        if request.user.is_authenticated:
            exempt = any(request.path.startswith(p) for p in self.EXEMPT_PREFIXES)
            if not exempt:
                try:
                    if request.user.profile.must_change_password:
                        return redirect('/access/trocar-senha/')
                except Exception:
                    pass
        return self.get_response(request)
