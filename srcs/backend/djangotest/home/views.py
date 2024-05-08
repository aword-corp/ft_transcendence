from django.shortcuts import render, HttpResponse

# Create your views here.
def home(request):
	return HttpResponse("Bonjour c'est la page d'accueil ici")