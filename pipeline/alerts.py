"""
Alerting: turn ingestion_runs into things a human should look at, and get
those things in front of a human.

Three checks run after every single scrape attempt:
  - fetch/parse failure         -> the run itself already carries this
  - zero rows on a run that succeeded technically but found nothing
  - staleness: does the source's own report_date match "today" in IST

Then notify_admin() ships whatever's new. It always logs; it emails
and/or posts to Slack too if the relevant environment variables are set.
Nothing throws if they aren't -- an unconfigured channel just means
"logged only," which is a safe default for a first deploy.
"""
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

import pytz
import requests

from models import Alert, IngestionRun

IST = pytz.timezone("Asia/Kolkata")


def today_ist():
    return datetime.now(IST).date()


def check_and_raise_alerts(session, run: IngestionRun, staleness_tolerance_days: int = 0) -> list[Alert]:
    """Run all checks for one ingestion run and persist any alerts. Returns
    the list of new Alert rows (also already added to the session)."""
    raised = []

    def raise_(alert_type, severity, message):
        a = Alert(run_id=run.id, terminal_code=run.terminal_code,
                   alert_type=alert_type, severity=severity, message=message)
        session.add(a)
        raised.append(a)

    if run.status == "failed":
        alert_type = "FETCH_FAILURE" if run.error_type == "network" else "PARSE_FAILURE"
        raise_(alert_type, "critical",
               f"{run.terminal_code}: run failed ({run.error_type}): {run.error_message}")

    elif run.status == "success":
        if run.rows_found == 0:
            raise_("ZERO_ROWS", "warning",
                   f"{run.terminal_code}: fetch and parse succeeded but found 0 rows -- "
                   f"either genuinely no vessels expected, or the layout drifted enough "
                   f"that our header labels no longer match anything. Worth a human glance.")

        if run.report_date is None:
            raise_("STALE_DATA", "warning",
                   f"{run.terminal_code}: could not determine the report's own date -- "
                   f"cannot confirm this is today's data.")
        else:
            today = today_ist()
            age_days = (today - run.report_date).days
            if age_days > staleness_tolerance_days:
                raise_("STALE_DATA", "critical",
                       f"{run.terminal_code}: source report is dated {run.report_date.isoformat()}, "
                       f"which is {age_days} day(s) behind today ({today.isoformat()}) IST. "
                       f"The site may not have published today's update yet, or we're pulling a cached copy.")

    session.commit()
    return raised


def notify_admin(alerts: list[Alert], context: str = "") -> None:
    """Always logs. Also emails and/or Slacks if configured via env vars:
      ADMIN_ALERT_EMAIL_TO, ADMIN_ALERT_SMTP_HOST/PORT/USER/PASSWORD
      ADMIN_ALERT_SLACK_WEBHOOK_URL
    Never raises -- a broken notification channel shouldn't take down the
    pipeline run that's trying to report a problem.
    """
    if not alerts:
        return

    lines = [f"[{a.severity.upper()}] {a.alert_type} -- {a.message}" for a in alerts]
    body = (context + "\n\n" if context else "") + "\n".join(lines)
    print("=" * 70)
    print("VESSEL SCHEDULE PIPELINE ALERT" + (f" ({context})" if context else ""))
    print("=" * 70)
    print(body)
    print("=" * 70)

    slack_url = os.environ.get("ADMIN_ALERT_SLACK_WEBHOOK_URL")
    if slack_url:
        try:
            requests.post(slack_url, json={"text": body}, timeout=10)
        except requests.RequestException as e:
            print(f"(Slack notification failed: {e})")

    email_to = os.environ.get("ADMIN_ALERT_EMAIL_TO")
    smtp_host = os.environ.get("ADMIN_ALERT_SMTP_HOST")
    if email_to and smtp_host:
        try:
            msg = MIMEText(body)
            msg["Subject"] = f"Vessel schedule pipeline alert ({len(alerts)})"
            msg["From"] = os.environ.get("ADMIN_ALERT_SMTP_USER", "vessel-schedule-bot@localhost")
            msg["To"] = email_to
            with smtplib.SMTP(smtp_host, int(os.environ.get("ADMIN_ALERT_SMTP_PORT", "587"))) as server:
                server.starttls()
                user = os.environ.get("ADMIN_ALERT_SMTP_USER")
                password = os.environ.get("ADMIN_ALERT_SMTP_PASSWORD")
                if user and password:
                    server.login(user, password)
                server.sendmail(msg["From"], [email_to], msg.as_string())
        except Exception as e:
            print(f"(Email notification failed: {e})")
