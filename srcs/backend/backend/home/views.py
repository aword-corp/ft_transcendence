from django.shortcuts import render
from db.models import Count, GlobalChat


# Create your views here.
def home(request):
    count_obj, created = Count.objects.get_or_create(id=1)
    if created:
        count_obj.save()
    messages = []
    if request.user.is_authenticated:
        messages = GlobalChat.objects.all
    message = {"title": "Bonjour !", "body": "Bienvenue sur ce site !"}
    context = {
        "message": message,
        "counter": count_obj.clicks,
        "message_list": messages,
        "auth": request.user.is_authenticated,
    }
    return render(request, "home/index.html", context)
