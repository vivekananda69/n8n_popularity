from django.core.management.base import BaseCommand
from workflows.collectors import collect_youtube_for_country, collect_forum, collect_trends, upsert_workflows

class Command(BaseCommand):
    help = "Fetch n8n workflows from YouTube, Forum, and Google Trends"

    def handle(self, *args, **options):
        all_items = []
        for country in ["US", "IN"]:
            print("Collecting YouTube for", country)
            yt = collect_youtube_for_country(country, max_per_kw=8)
            print("Collected", len(yt), "youtube items")
            all_items += yt
            print("Collecting Forum for", country)
            fr = collect_forum(country)
            print("Collected", len(fr), "forum items")
            all_items += fr
            print("Collecting Trends for", country)
            tr = collect_trends(country)
            print("Collected", len(tr), "trends items")
            all_items += tr
        print("Upserting into DB..")
        upsert_workflows(all_items)
        print("Done. Total items:", len(all_items))
