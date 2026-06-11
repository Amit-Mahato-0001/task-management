import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

GMAIL_SMTP_USER = os.getenv("GMAIL_SMTP_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")

if not GMAIL_SMTP_USER or not GMAIL_APP_PASSWORD:
    raise RuntimeError("GMAIL_SMTP_USER and GMAIL_APP_PASSWORD must be set in environment")


def send_email(to_email: str, subject: str, body: str):
    message = MIMEMultipart()
    message["From"] = GMAIL_SMTP_USER
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_SMTP_USER, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_SMTP_USER, to_email, message.as_string())


def send_task_created_email(assignee_email: str, task_title: str, creator_email: str):
    subject = f"New Task Assigned: {task_title}"
    body = f"<p>A new task <strong>{task_title}</strong> has been assigned to you by {creator_email}.</p>"
    send_email(assignee_email, subject, body)


def send_task_completed_email(assignee_email: str, task_title: str):
    subject = f"Task Completed: {task_title}"
    body = f"<p>The task <strong>{task_title}</strong> has been marked as completed.</p>"
    send_email(assignee_email, subject, body)
