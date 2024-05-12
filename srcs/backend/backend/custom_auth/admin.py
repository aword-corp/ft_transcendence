from django import forms
from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError
from django_countries.fields import CountryField

from db.models import User
from utils import verify_username, verify_password


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
        return verify_username(self.cleaned_data.get("username"))

    def clean_password_confirmation(self):
        password = self.cleaned_data.get("password")
        password_confirmation = self.cleaned_data.get("password_confirmation")
        if password and password_confirmation and password != password_confirmation:
            raise ValidationError("Passwords don't match")
        return verify_password(password, self.cleaned_data.get("username"))

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
