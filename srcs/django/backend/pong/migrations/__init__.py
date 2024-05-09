import os
from django.contrib.auth import get_user_model


UserModel = get_user_model()
UserModel.objects.create_superuser(
    os.getenv("POSTGRES_USER"), "admin@oc.drf", os.getenv("POSTGRES_PASSWORD")
)
