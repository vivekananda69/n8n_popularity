from django.contrib import admin
from django.urls import path
from django.http import JsonResponse
from workflows.views import list_workflows

def health(request):
    return JsonResponse({"status": "ok"}, status=200)

def home(request):
    return JsonResponse({
        "message": "n8n Workflow Popularity API",
        "endpoints": {
            "/api/workflows/": "Get workflows",
            "/health": "Health check"
        }
    })
