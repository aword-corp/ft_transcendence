from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField

from db.models import User
import string


MAX_REPEAT = 3


class UserCreationForm(forms.ModelForm):
    username = forms.CharField(label="Username", widget=forms.TextInput)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    password_confirmation = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput
    )
    country_code = CountryField().formfield()

    class Meta:
        model = User
        fields = [
            "email",
            "region",
            "language",
            "birth_date",
        ]

    def clean_username(self):
        username = self.cleaned_data.get("username")
        allowed_symbols = "_-."
        allowed_chars = string.ascii_letters + string.digits
        chars = symbols = 0
        for char in username:
            if char not in allowed_chars and char not in allowed_symbols:
                raise ValidationError("Forbidden chars in username")
            chars += char in allowed_chars
            symbols += char in allowed_symbols
        if symbols and not chars:
            raise ValidationError("At least one letter or digit is required")
        if symbols + chars < 3 or symbols + chars > 32:
            raise ValidationError("Length of username must be between 3 and 32")
        return username

    def clean_password_confirmation(self):
        password = self.cleaned_data.get("password")
        password_confirmation = self.cleaned_data.get("password_confirmation")
        if password and password_confirmation and password != password_confirmation:
            raise ValidationError("Passwords don't match")
        uppers = lowers = symbols = digits = 0
        for char in password:
            uppers += char.isupper()
            lowers += char.islower()
            symbols += not char.isalnum()
            digits += char.isdigit()

        length = uppers + lowers + symbols + digits
        if length < 6 or length > 64:
            raise ValidationError("Length of password must be between 6 and 64")
        if any(count == 0 for count in (length, uppers, lowers, symbols)):
            raise ValidationError(
                "At least one upper letter, one lower letter, one digit, one symbol are required"
            )
        if self.cleaned_data.get("username") in password:
            raise ValidationError("Username must no be part of the password")
        prev_value = ord(password[0].lower())
        curr_repeat = 1
        for char in password[1:]:
            if (prev_value - 1 <= ord(char.lower()) <= prev_value + 1) and (
                char.isalnum() and chr(prev_value).isalnum
            ):
                curr_repeat += 1
            else:
                curr_repeat = 1
            prev_value = ord(char)
            if curr_repeat == MAX_REPEAT:
                raise ValidationError(
                    "There must be not more a sequence of 3 following or repeating characters"
                )
        return password_confirmation

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = [
            "username",
            "password",
            "email",
            "region",
            "country_code",
            "language",
            "birth_date",
        ]


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    list_display = [
        "username",
        "password",
        "email",
        "region",
        "country_code",
        "language",
        "birth_date",
    ]
    list_filter = ["region", "country_code"]
    fieldsets = [
        (None, {"fields": ["email", "password"]}),
        # ("Personal info", {"fields": ["date_of_birth"]}),
        # ("Permissions", {"fields": ["is_admin"]}),
    ]
    add_fieldsets = [
        (
            None,
            {
                "classes": ["wide"],
                "fields": [
                    "username",
                    "email",
                    "region",
                    "country_code",
                    "birth_date",
                    "language",
                    "password",
                    "password_confirmation",
                ],
            },
        ),
    ]
    search_fields = ["email"]
    ordering = ["email"]
    filter_horizontal = []


admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
