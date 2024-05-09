from django.shortcuts import render, HttpResponse
from django.template import loader
from pong.models import Count, Chat

# Create your views here.
def home(request):
	count_obj, created = Count.objects.get_or_create(id=1)
	count_obj.save()
	messages = Chat.objects.all
	message = {
		"title": "Bonjour !",
		"body": "Bienvenue sur ce site !"
	}
	context = {
		"message": message,
		"counter": count_obj.clicks,
		"message_list": messages
	}
	return render(request, "home/index.html", context)