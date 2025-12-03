from django.db import models

class Workflow(models.Model):
    workflow = models.CharField(max_length=512, db_index=True)
    platform = models.CharField(max_length=50, db_index=True)  # YouTube | Forum | GoogleTrends
    country = models.CharField(max_length=10, db_index=True)   # US | IN
    source_url = models.URLField(blank=True, null=True)
    popularity_metrics = models.JSONField()  # store the metrics object
    popularity_score = models.FloatField(default=0, db_index=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("workflow", "platform", "country")

    def __str__(self):
        return f"{self.workflow} ({self.platform}/{self.country})"
