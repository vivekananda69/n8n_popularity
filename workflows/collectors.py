import requests
import time
from django.conf import settings
from pytrends.request import TrendReq

# =====================================================
# 1. YOUTUBE COLLECTOR
# =====================================================

def collect_youtube_for_country(country_code="US", keywords=None, pause=0.3):
    YOUTUBE_API_KEY = settings.YOUTUBE_API_KEY

    if not YOUTUBE_API_KEY:
        print("❌ No YOUTUBE_API_KEY found in settings")
        return []

    if keywords is None:
        keywords = [
            "n8n workflow",
            "n8n automation",
            "n8n google sheets",
            "n8n slack",
            "n8n gmail automation",
            "n8n whatsapp",
            "n8n webhook",
            "n8n notion",
            "n8n airtable",
            "n8n tutorial",
            "n8n agent",
            "n8n ai automation"
        ]

    results = []

    for kw in keywords:
        try:
            search_url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet",
                "q": kw,
                "type": "video",
                "regionCode": country_code,
                "maxResults": 50,
                "key": YOUTUBE_API_KEY,
            }

            r = requests.get(search_url, params=params, timeout=10)
            r.raise_for_status()
            items = r.json().get("items", [])

            video_ids = [it["id"]["videoId"] for it in items if it.get("id", {}).get("videoId")]

            # Fetch stats for videos in chunks
            for i in range(0, len(video_ids), 50):
                chunk = video_ids[i:i+50]

                stats_url = "https://www.googleapis.com/youtube/v3/videos"
                sparams = {
                    "part": "statistics,snippet",
                    "id": ",".join(chunk),
                    "key": YOUTUBE_API_KEY,
                }

                s = requests.get(stats_url, params=sparams, timeout=10)
                s.raise_for_status()

                for item in s.json().get("items", []):
                    title = item["snippet"]["title"]
                    url = f"https://www.youtube.com/watch?v={item['id']}"

                    stats = item.get("statistics", {})
                    views = int(stats.get("viewCount", 0))
                    likes = int(stats.get("likeCount", 0))
                    comments = int(stats.get("commentCount", 0))

                    like_ratio = likes / views if views else 0
                    comment_ratio = comments / views if views else 0

                    score = round((views * 0.6) + (likes * 3) + (comments * 10), 2)

                    results.append({
                        "workflow": title,
                        "source_url": url,
                        "country": country_code,
                        "platform": "YouTube",
                        "metrics": {
                            "views": views,
                            "likes": likes,
                            "comments": comments,
                            "like_to_view_ratio": like_ratio,
                            "comment_to_view_ratio": comment_ratio
                        },
                        "score": score,
                    })

                time.sleep(pause)

        except Exception as e:
            print("YouTube Collector error:", e)
            continue

    return results


# =====================================================
# 2. FORUM COLLECTOR (DISCOURSE API)
# =====================================================

def collect_forum(country="US"):
    BASE = "https://community.n8n.io"
    results = []

    try:
        for page in range(0, 5):  # COLLECT MORE PAGES
            url = f"{BASE}/latest.json?page={page}"
            data = requests.get(url, timeout=10).json()

            topics = data["topic_list"]["topics"]

            for t in topics:
                topic_id = t["id"]
                title = t["title"]
                replies = t.get("reply_count", 0)
                likes = t.get("like_count", 0)
                views = t.get("views", 0)

                # Get contributors count
                try:
                    detail = requests.get(f"{BASE}/t/{topic_id}.json", timeout=10).json()
                    contributors = len(detail["details"]["participants"])
                except:
                    contributors = 1

                score = (replies * 3) + (likes * 2) + (contributors * 5) + (views ** 0.5)

                results.append({
                    "workflow": title,
                    "source_url": f"{BASE}/t/{topic_id}",
                    "platform": "Forum",
                    "country": country,
                    "metrics": {
                        "replies": replies,
                        "likes": likes,
                        "views": views,
                        "contributors": contributors
                    },
                    "score": round(score, 2),
                })

    except Exception as e:
        print("Forum collector error:", e)

    return results


# =====================================================
# 3. GOOGLE TRENDS COLLECTOR
# =====================================================

def collect_trends(country="US"):
    try:
        py = TrendReq()

        keywords = [
            "n8n workflow",
            "n8n automation",
            "n8n slack automation",
            "n8n whatsapp bot",
            "n8n google sheets",
            "n8n gmail automation",
            "n8n ai automation",
            "n8n notion integration"
        ]

        geo = "US" if country == "US" else "IN"
        results = []

        for kw in keywords:
            py.build_payload([kw], geo=geo)
            df = py.interest_over_time()

            if df.empty:
                continue

            interest = int(df[kw].iloc[-1])
            old = int(df[kw].iloc[0])
            change_pct = round(((interest - old) / old * 100), 2) if old else 0

            score = round(interest * (1 + change_pct / 100), 2)

            results.append({
                "workflow": kw,
                "platform": "GoogleTrends",
                "country": country,
                "source_url": "https://trends.google.com",
                "metrics": {
                    "interest": interest,
                    "change_pct": change_pct
                },
                "score": score,
            })

        return results

    except Exception as e:
        print("Google Trends Error:", e)
        return []
