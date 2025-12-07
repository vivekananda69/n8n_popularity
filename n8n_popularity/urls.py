from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from workflows.views import list_workflows, trigger_fetch

def home(request):
    return JsonResponse({"message": "API running"})

urlpatterns = [
    path("", home),
    path("admin/", admin.site.urls),
    path("api/workflows/", list_workflows),
    path("trigger/<str:source>/<str:country>/", trigger_fetch),
]
