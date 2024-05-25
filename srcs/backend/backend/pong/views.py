from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from db.models import User, Matchmaking

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def MatchmakingView(request):
    user: User = request.user
    
    if request.method == "POST":
        if user.status.label in ["Playing", "Spectating"]:
            return Response({"detail": "You cannot join a queue while playing or spectating."}, status=status.HTTP_401_UNAUTHORIZED)
        queue, created = Matchmaking.objects.get_or_create(id=0)
        if user.matchmaking_set.contains(queue):
            return Response({"detail": "You are already in a queue."}, status=status.HTTP_401_UNAUTHORIZED)
        queue.users.add(user)
        return Response(
            {"users": queue.users.all()},
            status=status.HTTP_200_OK,
        )
    elif request.method == "GET":
        queue, created = Matchmaking.objects.get_or_create(id=0)
        
        return Response(
            {"users": queue.users.all()},
            status=status.HTTP_200_OK,
        )
