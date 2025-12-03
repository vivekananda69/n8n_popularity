import os
import time
import requests
import math
from pytrends.request import TrendReq
from django.utils import timezone
from .models import Workflow
from django.db import transaction
from django.conf import settings

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")  # from .env

# --- Utilities: scoring functions ---
def youtube_score(views, likes, comments):
    if views <= 0:
        return 0
    like_ratio = likes / views if views else 0
    comment_ratio = comments / views if views else 0
    # simple but effective: reward engagement ratios & sqrt of views
    return (math.sqrt(views) * (1 + 3*like_ratio + 5*comment_ratio))

def forum_score(replies, likes, contributors, views):
    base = replies * 3 + likes * 2 + contributors * 5
    return base + math.sqrt(max(views,0))

def trends_score(interest, change_pct):
    # interest 0-100
    return interest * (1 + change_pct/100)

# --- YouTube collector ---
def collect_youtube_for_country(country_code="US", keywords=None, max_per_kw=10, pause=0.4):
    if keywords is None:
        keywords = [
            "n8n workflow", "n8n automation", "n8n google sheets", "n8n slack",
            "n8n gmail", "n8n whatsapp", "n8n notion", "n8n airtable"
        ]
    results = []
    for kw in keywords:
        # search
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": kw,
            "type": "video",
            "maxResults": max_per_kw,
            "regionCode": country_code,
            "key": YOUTUBE_API_KEY
        }
        r = requests.get(url, params=params)
        r.raise_for_status()
        items = r.json().get("items", [])
        video_ids = [it["id"]["videoId"] for it in items if "videoId" in it.get("id", {})]
        # fetch stats in batch
        if not video_ids:
            time.sleep(pause)
            continue
        stats_url = "https://www.googleapis.com/youtube/v3/videos"
        sparams = {"part": "statistics,snippet", "id": ",".join(video_ids), "key": YOUTUBE_API_KEY}
        s = requests.get(stats_url, params=sparams)
        s.raise_for_status()
        for item in s.json().get("items", []):
            vid = item["id"]
            title = item["snippet"]["title"]
            stats = item.get("statistics", {})
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0) or 0)
            comments = int(stats.get("commentCount", 0) or 0)
            metrics = {
                "views": views,
                "likes": likes,
                "comments": comments,
                "like_to_view_ratio": likes / views if views else 0,
                "comment_to_view_ratio": comments / views if views else 0,
                "keyword": kw
            }
            score = youtube_score(views, likes, comments)
            results.append({
                "workflow": title,
                "platform": "YouTube",
                "country": country_code,
                "source_url": f"https://www.youtube.com/watch?v={vid}",
                "metrics": metrics,
                "score": score
            })
        time.sleep(pause)
    return results

# --- Discourse (n8n community) collector ---
def collect_forum(country_code="US", limit=80):
    base = "https://community.n8n.io"
    # pull latest topics
    url = f"{base}/latest.json"
    r = requests.get(url)
    r.raise_for_status()
    topics = r.json().get("topic_list", {}).get("topics", [])[:limit]
    results = []
    for t in topics:
        tid = t.get("id")
        title = t.get("title")
        views = t.get("views", 0)
        replies = t.get("reply_count", 0)
        likes = t.get("like_count", 0)
        # fetch details for contributors
        detail_url = f"{base}/t/{tid}.json"
        dr = requests.get(detail_url)
        if dr.status_code == 200:
            details = dr.json()
            # participants list -> contributors
            contributors = len(details.get("details", {}).get("participants", []))
        else:
            contributors = 1
        metrics = {"views": views, "replies": replies, "likes": likes, "contributors": contributors}
        score = forum_score(replies, likes, contributors, views)
        results.append({
            "workflow": title,
            "platform": "Forum",
            "country": country_code,
            "source_url": f"{base}/t/{tid}",
            "metrics": metrics,
            "score": score
        })
    return results

# --- Google Trends collector ---
def collect_trends(country_code="US", keywords=None):
    if keywords is None:
        keywords = [
            "n8n slack integration", "n8n google sheets", "n8n gmail automation",
            "n8n whatsapp", "n8n airtable", "n8n notion"
        ]
    geo = "US" if country_code == "US" else "IN"
    tr = TrendReq(hl="en-US", tz=0)
    results = []
    for kw in keywords:
        try:
            tr.build_payload([kw], geo=geo, timeframe="today 3-m")
            df = tr.interest_over_time()
            if df.empty:
                continue
            interest = int(df[kw].iloc[-1])
            # compute change percent vs 30 days earlier
            n = min(len(df), 30)
            old = int(df[kw].iloc[-n]) if n>1 else interest
            change_pct = ((interest - old) / old * 100) if old else 0
            metrics = {"interest": interest, "change_pct": change_pct}
            score = trends_score(interest, change_pct)
            results.append({
                "workflow": kw,
                "platform": "GoogleTrends",
                "country": country_code,
                "source_url": "https://trends.google.com",
                "metrics": metrics,
                "score": score
            })
        except Exception:
            continue
    return results

# --- Upsert function ---
@transaction.atomic
def upsert_workflows(items):
    # items: list of dicts with workflow, platform, country, metrics, score, source_url
    for it in items:
        obj, created = Workflow.objects.update_or_create(
            workflow=it["workflow"],
            platform=it["platform"],
            country=it["country"],
            defaults={
                "source_url": it.get("source_url"),
                "popularity_metrics": it.get("metrics"),
                "popularity_score": it.get("score"),
            }
        )
