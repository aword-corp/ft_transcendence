from django.shortcuts import render, HttpResponse
from django.template import loader

# Create your views here.
def home(request):
	message = {
		"title": "Bonjour !",
		"body": "Bienvenue sur ce site !"
	}
	context = {
		"message": message
	}
	return render(request, "home/index.html", context)