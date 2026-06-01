import hashlib

from rest_framework.throttling import SimpleRateThrottle


class LoginUserIpThrottle(SimpleRateThrottle):
    scope = "login_user_ip"

    def get_cache_key(self, request, view):
        identifier = (
            request.data.get("username")
            or request.data.get("email")
            or request.data.get("identifier")
            or ""
        )
        normalized_identifier = str(identifier).strip().lower()
        ident = self.get_ident(request)

        # Hash the account identifier so cache keys do not store raw emails.
        account_hash = hashlib.sha256(normalized_identifier.encode()).hexdigest()
        return self.cache_format % {
            "scope": self.scope,
            "ident": f"{ident}:{account_hash}",
        }
