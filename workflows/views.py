from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Workflow
from .serializers import WorkflowSerializer
from django.db.models import Q

@api_view(["GET"])
def list_workflows(request):
    platform = request.GET.get("platform")
    country = request.GET.get("country")
    limit = int(request.GET.get("limit", 100))
    q = Workflow.objects.all()
    if platform:
        q = q.filter(platform__iexact=platform)
    if country:
        q = q.filter(country__iexact=country)
    q = q.order_by("-popularity_score")[:min(limit, 1000)]
    ser = WorkflowSerializer(q, many=True)
    return Response(ser.data)
