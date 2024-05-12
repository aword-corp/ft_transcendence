from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField, AuthenticationForm
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField

from db.models import User
from .utils import verify_username, verify_password, verify_date


REGION_CHOICES = [
    ("eu-we", "Europe West"),
    ("eu-ea", "Europe East"),
    ("eu-no", "Europe North"),
    ("na-we", "North America West"),
    ("na-ce", "North America Central"),
    ("na-ea", "North America East"),
    ("ce-am", "Central America"),
    ("so-am", "South America"),
    ("no-af", "North Africa"),
    ("so-af", "South Africa"),
    ("mi-ea", "Middle East"),
    ("as-cn", "China"),
    ("as-in", "India"),
    ("as-sg", "Singapore"),
    ("as-kr", "Korea"),
    ("as-jp", "Japan"),
    ("oc-pa", "Oceania"),
]

LANGUAGE_CHOICES = [
    ("FR-FR", "French"),
    ("EN-US", "English"),
    ("CH-ZH", "Chinese"),
]


class CustomAuthenticationForm(forms.ModelForm):
    username = forms.CharField(label="Username/Email", widget=forms.TextInput)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = [
            "username",
            "password",
        ]

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
    region = forms.ChoiceField(label="Region", choices=REGION_CHOICES)
    language = forms.ChoiceField(label="Language", choices=LANGUAGE_CHOICES)

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
