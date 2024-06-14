import string
from django.utils import timezone
from rest_framework.serializers import ValidationError

ALLOWED_SYMBOLS_USERNAME = "_-."
ALLOWED_CHARS_USERNAME = string.ascii_letters + string.digits
LENGTH_MIN_USERNAME = 3
LENGTH_MAX_USERNAME = 32
ALNUM_MIN_USERNAME = 1


def verify_username(username):
    chars = symbols = 0
    for char in username:
        if char not in ALLOWED_CHARS_USERNAME and char not in ALLOWED_SYMBOLS_USERNAME:
            raise ValidationError("Forbidden chars in username")
        chars += char in ALLOWED_CHARS_USERNAME
        symbols += char in ALLOWED_SYMBOLS_USERNAME
    if symbols and chars < ALNUM_MIN_USERNAME:
        raise ValidationError(
            f"At least {ALNUM_MIN_USERNAME} letter or {ALNUM_MIN_USERNAME} digit is required when symbols are present"
        )
    length = symbols + chars
    if length < LENGTH_MIN_USERNAME or length > LENGTH_MAX_USERNAME:
        raise ValidationError(
            f"Length of username must be between {LENGTH_MIN_USERNAME} and {LENGTH_MAX_USERNAME}"
        )
    return username


MAX_REPEAT = 3
LENGTH_MIN_PASSWORD = 6
LENGTH_MAX_PASSWORD = 64
ALNUM_MIN_PASSWORD = 1


def check_repeating_chars(sequence, max_repeat):
    prev_value = ord(sequence[0].lower())
    curr_repeat = 1
    for char in sequence[1:]:
        if (prev_value - 1 <= ord(char.lower()) <= prev_value + 1) and (
            char.isalnum() and chr(prev_value).isalnum
        ):
            curr_repeat += 1
        else:
            curr_repeat = 1
        prev_value = ord(char)
        if curr_repeat == max_repeat:
            return True
    return False


def verify_password(password):
    uppers = lowers = symbols = digits = 0
    for char in password:
        uppers += char.isupper()
        lowers += char.islower()
        symbols += not char.isalnum()
        digits += char.isdigit()

    length = uppers + lowers + symbols + digits
    if length < LENGTH_MIN_PASSWORD or length > LENGTH_MAX_PASSWORD:
        raise ValidationError(
            f"Length of password must be between {LENGTH_MIN_PASSWORD} and {LENGTH_MAX_PASSWORD}"
        )
    if any(count < ALNUM_MIN_PASSWORD for count in (length, uppers, lowers, symbols)):
        raise ValidationError(
            f"At least {ALNUM_MIN_PASSWORD} upper letter, {ALNUM_MIN_PASSWORD} lower letter, {ALNUM_MIN_PASSWORD} digit, {ALNUM_MIN_PASSWORD} symbol are required"
        )
    if check_repeating_chars(password, MAX_REPEAT):
        raise ValidationError(
            f"There must be not more a sequence of {MAX_REPEAT} following or repeating characters"
        )
    return password


MIN_AGE_REGISTER = 13
MIN_YEAR_BIRTH = 1900


def verify_date(date):
    if not date:
        raise ValidationError("Birth date cannot be blank.")

    if date > timezone.now().date():
        raise ValidationError("Birth date cannot be in the future.")
    if date.year < MIN_YEAR_BIRTH:
        raise ValidationError(f"Birth date cannot be before {MIN_YEAR_BIRTH}.")
    age = (
        timezone.now().date().year
        - date.year
        - (
            (timezone.now().date().month, timezone.now().date().day)
            < (date.month, date.day)
        )
    )
    if age < MIN_AGE_REGISTER:
        raise ValidationError(
            f"You must be at least {MIN_AGE_REGISTER} years old to register."
        )
    return date
