import logging

from app.config import Settings

logger = logging.getLogger("doctor_letter.sms")


class SmsDeliveryError(Exception):
    pass


def send_login_code(settings: Settings, mobile_e164: str, code: str) -> None:
    if settings.otp_dev_mode and not settings.is_production:
        logger.info("OTP dev mode: code for %s is %s", mobile_e164[-4:], code)
        return

    if not settings.twilio_account_sid or not settings.twilio_auth_token or not settings.twilio_phone_number:
        raise SmsDeliveryError("SMS is not configured. Set Twilio credentials in the environment.")

    try:
        from twilio.rest import Client
    except ImportError as exc:
        raise SmsDeliveryError("Twilio library is not installed.") from exc

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    message = f"Your Doctor Letter sign-in code is {code}. It expires in {settings.otp_ttl_minutes} minutes."
    try:
        client.messages.create(body=message, from_=settings.twilio_phone_number, to=mobile_e164)
    except Exception as exc:
        raise SmsDeliveryError("Could not send the verification text.") from exc
