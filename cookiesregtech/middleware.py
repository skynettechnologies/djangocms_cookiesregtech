"""Injects the consent bootstrap right after <head> on rendered pages."""

import re

from .models import Settings

HEAD_RE = re.compile(rb"<head([^>]*)>", re.IGNORECASE)
DOMAIN_RE = re.compile(r"^[a-z0-9]{10,40}$", re.IGNORECASE)


class BannerInjectionMiddleware:
    """Add to MIDDLEWARE. Skips the admin, non-HTML, and streaming responses."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.path.startswith("/admin"):
            return response
        if getattr(response, "streaming", False):
            return response
        if "text/html" not in response.get("Content-Type", ""):
            return response

        settings = Settings.load()

        if not settings.banner_enabled:
            return response

        domain_id = (settings.domain_id or "").strip()

        if not domain_id or not DOMAIN_RE.match(domain_id):
            return response

        src = "%s/embed/boot/%s.js" % (settings.server_url, domain_id)
        tag = ('<script src="%s"></script>' % src).encode("utf-8")
        # First occurrence only: the bootstrap must be the first script in head.
        response.content = HEAD_RE.sub(lambda match: match.group(0) + tag, response.content, count=1)

        if response.has_header("Content-Length"):
            response["Content-Length"] = str(len(response.content))

        return response
