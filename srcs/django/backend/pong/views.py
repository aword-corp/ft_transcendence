from pong.models import Count
from django.shortcuts import render


def pong(request):
    count_obj, created = Count.objects.get_or_create(id=1)
    count_obj.save()
    message = {"title": "Bonjour !", "body": f"Hello user {count_obj.clicks}"}
    return render(
        request,
        "home/index.html",
        {"message": message, "counter": count_obj.clicks},
    )
