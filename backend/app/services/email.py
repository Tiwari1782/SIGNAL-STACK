import os, smtplib, ssl, logging
from email.message import EmailMessage

log = logging.getLogger(__name__)

def send_brief(to: str, subject: str, html: str):
    user = os.environ.get("GMAIL_USER", "").strip()
    pwd = os.environ.get("GMAIL_APP_PASSWORD", "").strip().replace(" ", "")

    if not user or not pwd:
        raise ValueError(
            "GMAIL_USER or GMAIL_APP_PASSWORD is not configured in .env. "
            "Please provide a valid Gmail address and 16-character App Password."
        )

    msg = EmailMessage()
    msg["From"] = f"Signal Stack <{user}>"
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content("Open this email in an HTML-capable client to view your executive brief.")
    msg.add_alternative(html, subtype="html")

    last_error = None

    # Strategy 1: Try Port 465 (Direct SSL)
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx, timeout=12) as s:
            s.ehlo()
            s.login(user, pwd)
            s.send_message(msg)
            log.info("Email delivered successfully via port 465 to %s", to)
            return
    except smtplib.SMTPAuthenticationError as e:
        raise ValueError(
            f"Gmail Authentication Failed (535 Bad Credentials). "
            f"Please verify GMAIL_USER ('{user}') and that your 16-character App Password "
            f"was generated at https://myaccount.google.com/apppasswords with 2-Step Verification enabled."
        ) from e
    except smtplib.SMTPServerDisconnected as e:
        last_error = e
        log.warning("Port 465 disconnected, attempting fallback to port 587 (STARTTLS)...")
    except Exception as e:
        last_error = e
        log.warning("Port 465 failed (%s), attempting fallback to port 587...", e)

    # Strategy 2: Fallback to Port 587 (STARTTLS)
    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP("smtp.gmail.com", 587, timeout=12) as s:
            s.ehlo()
            s.starttls(context=ctx)
            s.ehlo()
            s.login(user, pwd)
            s.send_message(msg)
            log.info("Email delivered successfully via port 587 to %s", to)
            return
    except smtplib.SMTPAuthenticationError as e:
        raise ValueError(
            f"Gmail Authentication Failed (535 Bad Credentials). "
            f"Please verify GMAIL_USER ('{user}') and that your 16-character App Password "
            f"was generated at https://myaccount.google.com/apppasswords with 2-Step Verification enabled."
        ) from e
    except smtplib.SMTPServerDisconnected as e:
        # Gmail drops socket on invalid credentials instead of sending 535 in certain SSL negotiations
        raise ValueError(
            f"Gmail connection closed during authentication. This usually indicates Google rejected "
            f"the credentials for '{user}'. Please regenerate a fresh 16-character App Password at "
            f"https://myaccount.google.com/apppasswords and update GMAIL_APP_PASSWORD in your .env."
        ) from e
    except Exception as e:
        raise RuntimeError(f"Email delivery failed across both SMTP ports (465 and 587): {e}") from e
