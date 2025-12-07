from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import JsonResponse, HttpResponseForbidden
from django.conf import settings
from django.core.management import call_command
from threading import Thread
from .models import Workflow
from .serializers import WorkflowSerializer

# ---------------------------------------------------
# LIST WORKFLOWS API
# ---------------------------------------------------
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


# ---------------------------------------------------
# ASYNC BACKGROUND FETCH TRIGGER
# ---------------------------------------------------
def trigger_fetch(request, source, country):
    secret = request.headers.get("X-Trigger-Secret")
    if secret != settings.TRIGGER_SECRET:
        return HttpResponseForbidden("Forbidden")

    def background_job():
        try:
            call_command(f"fetch_{source}", country)
        except Exception as e:
            print("Background fetch error:", e)

    Thread(target=background_job).start()

    return JsonResponse({
        "status": "started",
        "source": source,
        "country": country
    })
