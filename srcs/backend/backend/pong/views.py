from django.shortcuts import render
from db.models import Count, GlobalChat


# Create your views here.
def pong(request):
    # context = {
    #     "message": message,
    # }
    return render(request, "pong/index.html", context)
