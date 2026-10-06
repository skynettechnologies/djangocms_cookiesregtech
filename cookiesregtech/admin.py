"""The CookiesRegTech admin page: connect, pending, connected screens.

Self-contained: registering the app in INSTALLED_APPS adds a
"CookiesRegTech settings" entry to the Django admin whose page is the
guided three-screen flow (no extra urls.py include needed).
"""

from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import reverse

from . import DEFAULT_SERVER
from .api import post as api_post
from .api import unexpected_reply
from .models import Settings

DOMAIN_PATTERN = r"^[a-z0-9]{10,40}$"

CATEGORY_LABELS = {
    "ESSENTIAL": "Essential",
    "FUNCTIONALITY": "Functionality",
    "ANALYTICS": "Analytics",
    "ADS": "Ads",
    "UNCATEGORISED": "Uncategorised",
}


@admin.register(Settings)
class SettingsAdmin(admin.ModelAdmin):
    """Routes the model's admin pages to the guided settings screen."""

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        return redirect(reverse("admin:cookiesregtech_settings_page"))

    def get_urls(self):
        from django.urls import path

        return [
            path(
                "page/",
                self.admin_site.admin_view(self.settings_page),
                name="cookiesregtech_settings_page",
            ),
        ] + super().get_urls()

    # ------------------------------------------------------------- the page

    def settings_page(self, request):
        settings = Settings.load()

        if request.method == "POST":
            response = self.handle_action(request, settings)

            if response is not None:
                return response

        state = "connect"
        overview = None

        if settings.secret and settings.domain_id:
            state = "connected"
            result = api_post(settings.server_url, "/api/plugin/overview", {"secret": settings.secret})

            if result.get("_status") == 200:
                overview = result

                for cookie in overview.get("cookies", []):
                    cookie["category_label"] = CATEGORY_LABELS.get(cookie.get("category"), cookie.get("category"))
        elif settings.pending_token:
            state = "pending"

        context = {
            **self.admin_site.each_context(request),
            "title": "CookiesRegTech",
            "settings": settings,
            "state": state,
            "overview": overview,
            "admin_email": getattr(request.user, "email", "") or "",
            "cookies_open": bool(overview) and len(overview.get("cookies", [])) <= 12,
        }

        return render(request, "cookiesregtech/settings.html", context)

    def handle_action(self, request, settings):
        import re

        action = request.POST.get("crt_action", "")
        back = redirect(reverse("admin:cookiesregtech_settings_page"))

        if action == "connect":
            email = (request.POST.get("email") or "").strip()
            consent = bool(request.POST.get("consent"))

            if "@" not in email or not consent:
                messages.error(request, "Enter a valid email address and accept the terms to continue.")

                return back

            hostname = request.get_host().split(":")[0]
            result = api_post(settings.server_url, "/api/plugin/provision", {
                "email": email,
                "hostname": hostname,
                "platform": "djangocms",
                "consent": True,
            })

            if result.get("status") == "connected":
                settings.domain_id = result["domainId"]
                settings.secret = result["secret"]
                settings.email = result.get("email", email)
                settings.pending_token = ""
                settings.banner_enabled = True
                settings.save()
                messages.success(request, "The free account is ready and the consent banner is live on the site. A sign-in link was emailed to %s." % email)
            elif result.get("status") == "confirmation_sent":
                settings.pending_token = result["requestToken"]
                settings.email = email
                settings.save()
                messages.success(request, 'That email already has an account. We sent it a confirmation link. Click the link, then press "Check status" here.')
            else:
                messages.error(request, result.get("error") or unexpected_reply(result))

            return back

        if action == "check":
            result = api_post(settings.server_url, "/api/plugin/status", {"requestToken": settings.pending_token})

            if result.get("status") == "connected":
                settings.domain_id = result["domainId"]
                settings.secret = result["secret"]
                settings.pending_token = ""
                settings.banner_enabled = True
                settings.save()
                messages.success(request, "Connected. The consent banner is live on this site.")
            elif result.get("status") == "pending":
                messages.warning(request, "Not confirmed yet. Click the link in the email first.")
            else:
                settings.pending_token = ""
                settings.save()
                messages.error(request, result.get("error") or "The request expired. Start again.")

            return back

        if action == "reset":
            settings.pending_token = ""
            settings.save()

            return back

        if action == "save":
            enabled = bool(request.POST.get("banner_enabled"))
            settings.banner_enabled = enabled
            settings.save()
            messages.success(request, "Cookie consent banner is enabled." if enabled else "Cookie consent banner is disabled.")

            return back

        if action in ("dashboard", "upgrade"):
            payload = {"secret": settings.secret}

            if action == "upgrade":
                payload["intent"] = "upgrade"

            result = api_post(settings.server_url, "/api/plugin/login-link", payload)

            if result.get("url"):
                return redirect(result["url"])

            messages.error(request, result.get("error") or "Could not create a sign-in link. Try again.")

            return back

        if action == "disconnect":
            if settings.secret:
                api_post(settings.server_url, "/api/plugin/disconnect", {"secret": settings.secret})

            settings.domain_id = ""
            settings.secret = ""
            settings.pending_token = ""
            settings.email = ""
            settings.save()
            messages.success(request, "Disconnected. The banner is off. The CookiesRegTech account and its data are unchanged.")

            return back

        return None
