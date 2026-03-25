import os
import urllib.request
import urllib.error
import json
from dotenv import load_dotenv

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
EMAIL_FROM     = os.getenv("EMAIL_FROM", "PINIT <onboarding@resend.dev>")


def _send(to_email: str, subject: str, html: str) -> bool:
    """Core send — uses Resend API over HTTPS. Works on Render free tier permanently."""
    try:
        payload = json.dumps({
            "from"   : EMAIL_FROM,
            "to"     : [to_email],
            "subject": subject,
            "html"   : html
        }).encode("utf-8")

        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data    = payload,
            headers = {
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type" : "application/json"
            },
            method = "POST"
        )

        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print(f"✅ Email sent to {to_email} | id: {result.get('id')}")
            return True

    except urllib.error.HTTPError as e:
        print(f"❌ Resend error (HTTP {e.code}): {e.read().decode()}")
        return False
    except Exception as e:
        print(f"❌ Email send error: {e}")
        return False


def send_otp_email(to_email: str, otp_code: str, username: str) -> bool:
    """Send OTP verification email"""
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
        <div style="background: #1a1a2e; padding: 30px; border-radius: 12px;">
            <h2 style="color: #667eea; margin: 0 0 10px;">PINIT</h2>
            <p style="color: #ccc; font-size: 14px;">Image Verification Platform</p>
        </div>
        <div style="padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 12px 12px;">
            <h3>Hi {username},</h3>
            <p>Your verification code is:</p>
            <div style="background: #f7fafc; border: 2px solid #667eea;
                        border-radius: 8px; padding: 20px; text-align: center;
                        font-size: 36px; font-weight: bold; letter-spacing: 8px;
                        color: #667eea; margin: 20px 0;">
                {otp_code}
            </div>
            <p style="color: #666; font-size: 13px;">
                This code expires in <strong>10 minutes</strong>.<br>
                If you did not request this, ignore this email.
            </p>
        </div>
    </body>
    </html>
    """
    return _send(to_email, "PINIT — Your Verification Code", html)


def send_new_device_email(to_email: str, username: str, device_name: str) -> bool:
    """Notify user when a new device is registered"""
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
        <div style="background: #1a1a2e; padding: 30px; border-radius: 12px;">
            <h2 style="color: #667eea;">PINIT</h2>
        </div>
        <div style="padding: 30px; border: 1px solid #e2e8f0;">
            <h3>Hi {username},</h3>
            <p>A new device was registered to your account:</p>
            <div style="background: #f7fafc; padding: 15px; border-radius: 8px;
                        border-left: 4px solid #667eea;">
                <strong>Device:</strong> {device_name}
            </div>
            <p style="color: #666; font-size: 13px; margin-top: 20px;">
                If this was not you, contact support immediately.
            </p>
        </div>
    </body>
    </html>
    """
    return _send(to_email, "PINIT — New Device Registered", html)


def send_username_email(to_email: str, username: str) -> bool:
    """Send username reminder email"""
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
        <div style="background: #1a1a2e; padding: 30px; border-radius: 12px;">
            <h2 style="color: #667eea; margin: 0 0 10px;">PINIT</h2>
            <p style="color: #ccc; font-size: 14px;">Image Verification Platform</p>
        </div>
        <div style="padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 12px 12px;">
            <h3>Hi there,</h3>
            <p>You requested your username. Here it is:</p>
            <div style="background: #f7fafc; border: 2px solid #667eea;
                        border-radius: 8px; padding: 20px; text-align: center;
                        font-size: 28px; font-weight: bold; letter-spacing: 4px;
                        color: #667eea; margin: 20px 0;">
                {username}
            </div>
            <p style="color: #666; font-size: 13px;">
                You can use this username to log in to your account.<br>
                If you did not request this, please ignore this email.
            </p>
        </div>
    </body>
    </html>
    """
    return _send(to_email, "PINIT — Your Username", html)


def send_forgot_password_email(to_email: str, otp_code: str, username: str) -> bool:
    """Send password reset OTP email"""
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 500px; margin: 0 auto;">
        <div style="background: #1a1a2e; padding: 30px; border-radius: 12px;">
            <h2 style="color: #667eea; margin: 0 0 10px;">PINIT</h2>
            <p style="color: #ccc; font-size: 14px;">Image Verification Platform</p>
        </div>
        <div style="padding: 30px; border: 1px solid #e2e8f0; border-radius: 0 0 12px 12px;">
            <h3>Hi {username},</h3>
            <p>We received a request to reset your password. Use this code:</p>
            <div style="background: #fff5f5; border: 2px solid #e53e3e;
                        border-radius: 8px; padding: 20px; text-align: center;
                        font-size: 36px; font-weight: bold; letter-spacing: 8px;
                        color: #e53e3e; margin: 20px 0;">
                {otp_code}
            </div>
            <p style="color: #666; font-size: 13px;">
                This code expires in <strong>10 minutes</strong>.<br>
                If you did not request a password reset, ignore this email.
            </p>
        </div>
    </body>
    </html>
    """
    return _send(to_email, "PINIT — Password Reset Code", html)