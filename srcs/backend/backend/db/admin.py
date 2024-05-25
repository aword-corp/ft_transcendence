from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField

from db.models import User, UserTwoFactorAuthData
from db.utils import verify_username, verify_password, verify_date


class CustomAuthenticationForm(forms.Form):
    username = forms.CharField(label="Username/Email", widget=forms.TextInput)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)


class Custom2faAuthenticationForm(forms.Form):
    username = forms.CharField(label="Username/Email", widget=forms.TextInput)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    otp = forms.CharField(label="2FA validation code", widget=forms.TextInput)

    def clean_otp(self):
        print(self.data)
        self.two_factor_auth_data = UserTwoFactorAuthData.objects.filter(
            user=User.get_user(
                self.cleaned_data.get("username"), self.cleaned_data.get("password")
            )
        ).first()

        if self.two_factor_auth_data is None:
            raise ValidationError("2FA not set up.")

        otp = self.cleaned_data.get("otp")

        otp = "".join(filter(str.isdigit, otp))

        if not self.two_factor_auth_data.validate_otp(otp):
            raise ValidationError("Invalid 2FA code.")

        return otp


class UserCreationForm(forms.ModelForm):
    email = forms.EmailField(label="Email", widget=forms.EmailInput)
    username = forms.CharField(label="Username", widget=forms.TextInput)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)
    password_confirmation = forms.CharField(
        label="Password confirmation", widget=forms.PasswordInput
    )
    birth_date = forms.DateField(
        label="Birth date", widget=forms.DateInput(attrs={"type": "date"})
    )
    country_code = CountryField().formfield(label="Country")
    # region = forms.TypedChoiceField(label="Region", choices=User.Region)
    # language = forms.TypedChoiceField(label="Language", choices=User.Language.choices)

    class Meta:
        model = User
        fields = [
            "email",
            "username",
            "password",
            "password_confirmation",
            "birth_date",
            "country_code",
            "region",
            "language",
        ]

    def clean_username(self):
        return verify_username(self.cleaned_data.get("username"))

    def clean_password_confirmation(self):
        password = self.cleaned_data.get("password")
        password_confirmation = self.cleaned_data.get("password_confirmation")
        if password and password_confirmation and password != password_confirmation:
            raise ValidationError("Passwords don't match")
        return verify_password(password, self.cleaned_data.get("username"))

    def clean_birth_date(self):
        return verify_date(self.cleaned_data.get("birth_date"))

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
