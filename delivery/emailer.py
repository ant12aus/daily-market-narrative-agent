from __future__ import annotations
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText




def send_email(smtp_user: str, app_password: str, recipients: list[str], subject: str, html: str, text: str | None = None):
msg = MIMEMultipart('alternative')
msg['Subject'] = subject
msg['From'] = smtp_user
msg['To'] = ", ".join(recipients)


part1 = MIMEText(text or "", 'plain')
part2 = MIMEText(html, 'html')


if text:
msg.attach(part1)
msg.attach(part2)


with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
server.login(smtp_user, app_password)
server.sendmail(smtp_user, recipients, msg.as_string())