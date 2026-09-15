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

## Update 2026-09-15: the hourly fix didn't actually fix it

Two more "the site hasn't refreshed" reports came in for JNPT, Mundra
and Chennai the day after the hourly-cron change above shipped. Pulled
the real run history via the Actions API rather than assuming the fix
had worked (or guessing at a new cause) -- every run in that window
still shows `conclusion: success`, and the latest run at the time
(`run_status` in `frontend/data.json`) shows **zero** per-terminal
failures across all 11 terminal codes. So nothing was actually broken
at the scraper level, again -- same shape as the original incident.

What was actually happening: the gaps between real, executed runs
never came down to ~1 hour after the hourly-cron change deployed.
Measured directly:

```
run #23  gap = 8.33h   (the very first run after the fix landed)
run #24  gap = 5.95h
run #25  gap = 3.87h
run #26  gap = 2.95h
```

Over the ~20 hours after the fix deployed, only 4 runs actually fired
-- roughly 75-80% of the hourly ticks GitHub was supposed to trigger
never happened at all, silently, with no error and no record that a
tick was ever supposed to fire. This is a materially bigger problem
than "delayed during high load" (the thing the original fix targeted):
it's GitHub's `schedule:` trigger dropping the large majority of ticks
outright, confirmed live while investigating (last real run 5+ hours
before the check, despite the "hourly" schedule).

This explains why JNPT/Mundra/Chennai specifically, and not Cochin:
those three all depend on a source that publishes one report per day at
an inconsistent time (JNPT's own history: sometimes not until 12:30-
13:00 IST) -- so when the real check cadence silently reverts to
multi-hour, they're the ones caught mid-morning still showing
yesterday's report. Cochin's IGTPL source is a live rolling webpage
with no daily-publish lag, so it's far less exposed to this.

**Decision**: rather than keep chasing a shorter interval against a
scheduler that drops most ticks regardless of frequency, the schedule
is now a fixed, deliberately-chosen 4x/day -- 2am, 6am, noon, 6pm IST
(see `.github/workflows/scrape.yml`'s own comment for the exact UTC
cron and why each of those IST times lands on a UTC half-hour for
free). This is an explicitly accepted cadence, not a workaround --
the same silent-skip risk still applies to whichever ticks are
scheduled, so an occasional missed check within that 6-hour-ish window
is expected, not a new bug to chase.

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
2. **No external trigger backs up GitHub's own scheduler.** Confirmed
   2026-09-15 (see the update above) that this is no longer a "worth it
   only if" -- the hourly schedule change WAS tried and did NOT close
   the gap; GitHub's own `schedule:` trigger silently drops the large
   majority of ticks regardless of interval. A free external cron
   pinger (e.g. cron-job.org) hitting this repo's `workflow_dispatch`
   API on a schedule GitHub doesn't control is the only way to get an
   actual guarantee ("this definitely ran at this exact time") rather
   than a best-effort one -- at the cost of a repo-scoped GitHub token
   held in that external service, which is why this hasn't been done
   without the repo owner setting it up directly. Current 4x/day
   schedule is a deliberate choice to accept best-effort at a coarser,
   explicitly-tolerated cadence instead, not a claim that this gap is
   closed.
3. Consider applying the same "try more than one date format" hardening
   to `scrapers/mict.py` and `scrapers/chennai_psa.py` pre-emptively —
   both are checked here (still fine as of this writing) but come from
   the same two publishers (DP World, and a WordPress-embedded PDF link
   respectively) that already changed an undocumented format once each.
