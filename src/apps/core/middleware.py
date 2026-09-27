from django.shortcuts import redirect


class AdminIsolationMiddleware:
    """Keep application administrators inside their dedicated management area."""

    blocked_prefixes = (
        '/projects/',
        '/requirements/',
        '/test-plans/',
        '/test-cases/',
        '/executions/',
        '/defects/',
        '/incidents/',
        '/traceability/',
        '/reports/',
        '/notifications/',
        '/audit/',
        '/phases/',
        '/drafts/',
        '/admin/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if getattr(user, 'is_authenticated', False) and getattr(user, 'role', None) == 'ADMIN':
            if request.path.startswith(self.blocked_prefixes):
                return redirect('users:admin-dashboard')
        return self.get_response(request)
