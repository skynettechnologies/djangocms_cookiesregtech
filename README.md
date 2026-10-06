CookiesRegTech shows an accessible cookie consent banner on the website, blocks known trackers until the visitor agrees, signals Google Consent Mode before analytics run, and keeps a consent log that can be exported as proof.

This plugin connects the Django CMS (or any Django) site to a CookiesRegTech account and installs the consent script in the correct position (before analytics and tag managers) automatically — the step most manual installations get wrong.

**Free plan included.** A free account gives a working banner, consent logging, manual cookie scans, layout and color customisation, and 5,000 recorded pageviews per month. Paid plans add scheduled full-site scans, geo-targeted banners, custom CSS, and higher limits — upgrades happen in the CookiesRegTech dashboard, never inside this plugin.

**Features**

* One-click connect: enter an email on the settings page — a free account is created and the banner goes live, no copy-pasting required
* Opt-in (GDPR-style) and opt-out (US-style) consent templates, with geo-targeting on paid plans
* Automatic blocking of known advertising and analytics trackers until consent
* Google Consent Mode v2 signals set before Google tags execute
* Cookie scanner that discovers and categorises the cookies the site sets, with the detected list shown right on the settings page
* Signed-in jumps from Django admin straight into the consent dashboard
* Consent log with export, as required for GDPR accountability
* Accessible by design: WCAG 2.2 AA contrast, keyboard support, 44px targets

## Installation

1. Install the package:

   ```
   pip install djangocms-cookiesregtech
   ```

2. Add the app and the middleware to `settings.py`:

   ```python
   INSTALLED_APPS = [
       # ...
       "cookiesregtech",
   ]

   MIDDLEWARE = [
       # ...
       "cookiesregtech.middleware.BannerInjectionMiddleware",
   ]
   ```

3. Run the migration and collect the static files:

   ```
   python manage.py migrate cookiesregtech
   python manage.py collectstatic
   ```

4. Open Django admin, click "CookiesRegTech settings", enter an account email, accept the terms, and click "Connect website".
5. New email: a free account is created instantly and the banner is live. Existing account: click the confirmation link that arrives by email, then press "Check status".
6. Use "Open dashboard" on the settings page to customise the banner, run cookie scans, and view the consent log.

## Frequently Asked Questions

### Is a CookiesRegTech account required?

Yes — a free account, created directly from the settings page. The banner configuration, cookie scanning, and consent log live in the dashboard at www.cookiesregtech.com.

### Does the plugin slow the site down?

No. It adds a single ~1KB loader script that never blocks page rendering; the banner itself loads asynchronously.

### The analytics code is pasted directly into the base template's head — is it still blocked?

The middleware injects the consent script immediately after the opening `<head>` tag of every rendered HTML page, so it runs before any analytics or tag manager code placed inside the head. Pages that are not HTML, streaming responses, and the Django admin are skipped. Google tags are additionally governed by Consent Mode either way.

### Where are the banner text, colors, or languages changed?

In the CookiesRegTech dashboard — changes publish to the site instantly, no plugin update needed.

### What data does the plugin send?

On connect: the account email and the site hostname, to create/link the account. Afterwards the settings page reads the connection status and detected cookie list from the CookiesRegTech API. Visitor consent choices are recorded by the banner script per the CookiesRegTech privacy policy (https://www.cookiesregtech.com/privacy-policy).

