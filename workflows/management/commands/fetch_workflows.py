from django.core.management.base import BaseCommand
from django.utils import timezone
from workflows.models import Workflow
from workflows.collectors import collect_youtube_for_country, collect_forum, collect_trends

class Command(BaseCommand):
    help = "Fetch workflows from YouTube, Forum, and Google Trends for US + IN"

    def handle(self, *args, **options):
        self.stdout.write("🚀 Starting workflow collection...")

        all_items = []

        for country in ["US", "IN"]:
            yt = collect_youtube_for_country(country)
            fr = collect_forum(country)
            tr = collect_trends(country)

            all_items += yt + fr + tr

        for item in all_items:
            Workflow.objects.update_or_create(
                workflow=item["workflow"],
                platform=item["platform"],
                country=item["country"],
                defaults={
                    "source_url": item["source_url"],
                    "popularity_metrics": item["metrics"],
                    "popularity_score": item["score"],
                    "last_seen": timezone.now(),
                }
            )

        self.stdout.write(self.style.SUCCESS(f"✔ Stored {len(all_items)} workflows"))
