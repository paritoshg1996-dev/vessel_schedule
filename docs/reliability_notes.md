# Pipeline reliability — deep dive (2026-09-14)

Two consecutive days of "this hasn't refreshed" reports (Mundra's report-date
bug on the 13th, JNPT/Cochin on the 14th) turned out to be three separate,
distinct problems wearing the same symptom. Recorded here so the next
person chasing this exact complaint doesn't have to re-derive it.

## What was actually wrong, each time

1. **A genuine, recurring source-format-change bug.** Adani dropped its
   report's title line on 2026-09-13 (see `scrapers/mundra_adani.py`);
   DP World's CCT report silently switched its date token from
   `12/9/2026` (D/D/YYYY, slashes) to `14-09-26` (DD-MM-YY, dashes) on
   2026-09-14 (see `scrapers/chennai_dpworld.py`) — no other change to
   either report. Both broke the same way: the report-date parser
   returned `None`, which (before the first fix below) meant the run
   silently discarded every real row while still reporting "success".
   **Not a one-off** — two independent sources changed an undocumented
   detail of their own PDF within 24 hours of each other. Treat a
   report-date parser as the single most fragile part of any new
   scraper; give it a fallback where one exists (Adani's now tries its
   own title line, then a bare timestamp salvaged from otherwise-garbled
   text) and prefer a format-tolerant regex (CCT's now accepts either
   date shape it's actually shown) over a single hardcoded pattern.

2. **JNPT itself hadn't published yet.** Checked directly against
   JNPT's own master page (independent of our pipeline) while
   investigating the 09-14 report: it was still serving "Daily Berthing
   Report as on 13-09-2026" at 09:47 IST. Traced the previous day's
   publish time from `frontend/data.json`'s own commit history: the
   13th's report first appeared between 06:55 and 07:40 UTC
   (12:25–13:10 IST) on the 13th — i.e. JNPT's own daily publish time
   isn't fixed, and 09:47 IST simply isn't late enough yet to expect it.
   **This is not a bug** — `STALE_DATA` exists specifically to surface
   this, correctly, as "the site may not have published today's update
   yet" rather than "we're broken". The frustration is real, but it's a
   communication/expectation problem, not a pipeline one; see below.

3. **The GitHub Actions `schedule:` trigger is unreliable, and was
   configured in the one way GitHub's own docs say makes it worse.**
   Pulled real run timestamps via the Actions API
   (`/repos/.../actions/workflows/scrape.yml/runs`): gaps against the
   nominal 3-hour cadence hit 5.3 hours at least once (run #14 at
   2026-09-12T22:54Z, next real run #16 not until 2026-09-13T06:54Z, #15
   in between stuck `queued` for 2.5+ hours before being cancelled).
   GitHub's own scheduled-events documentation states scheduled runs
   "may be delayed during periods of high load," and specifically names
   **the start of every hour** as the worst time to be queued at — which
   is exactly when `cron: '0 */3 * * *'` always fired. Fixed by moving
   to `cron: '13 * * * *'` (hourly, off the top of the hour) —
   see `.github/workflows/scrape.yml`. This doesn't make GitHub's
   scheduler perfectly reliable (nothing can, short of an external
   trigger — see "Not yet done" below), but it both avoids the
   documented worst-case contention window and shrinks the worst-case
   gap between checks regardless.

## Why "the site looks stale" will keep happening sometimes, and that's OK

Between problems 2 and 3: even with hourly checks, there will always be
some window — normally well under an hour, occasionally longer if
GitHub's scheduler is having a bad day — between a source actually
publishing and the site reflecting it. That's inherent to polling a
handful of government/operator sites with no push notification of their
own; it is not the same thing as "broken," and chasing it to zero isn't
a realistic goal. What IS worth fixing (and is on the list below) is
making that distinction legible without someone having to ask.

## Not yet done — real next steps, in priority order

1. **Alerting doesn't reach anyone.** `pipeline/alerts.py` already
   raises exactly the right signal for both problem 1 (schema_drift ->
   PARSE_FAILURE, critical) and problem 2 (STALE_DATA, correctly
   distinguishing "critical" from a same-day tolerance) on every run —
   but `notify_admin()` only prints to the GitHub Actions log unless
   `ADMIN_ALERT_SLACK_WEBHOOK_URL` or `ADMIN_ALERT_EMAIL_TO`+SMTP
   secrets are set. If neither is configured, every failure — including
   the CCT one that sat broken for at least a day before anyone
   noticed — is invisible until someone happens to check the site.
   This is the highest-leverage fix left and the only one still
   pending an answer from whoever owns the repo secrets: which channel
   (Slack webhook is the one-secret option) should `notify_admin` 
   actually reach.
2. **No external trigger backs up GitHub's own scheduler.** A free
   external cron pinger (e.g. cron-job.org) hitting the repo's
   `workflow_dispatch` API on a schedule GitHub doesn't control would
   close the remaining gap from problem 3 entirely, at the cost of one
   more account to hold a token for. Worth it only if the hourly
   schedule change above turns out not to be enough in practice.
3. Consider applying the same "try more than one date format" hardening
   to `scrapers/mict.py` and `scrapers/chennai_psa.py` pre-emptively —
   both are checked here (still fine as of this writing) but come from
   the same two publishers (DP World, and a WordPress-embedded PDF link
   respectively) that already changed an undocumented format once each.
