from django.shortcuts import render, HttpResponse

# Create your views here.
u = 0
def pong(request):
	global u
	s= f"Hello user {u}"
	u += 1
	return HttpResponse(s)