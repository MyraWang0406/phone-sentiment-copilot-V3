import requests

PROXIES = {
    "http": "http://127.0.0.1:7890",
    "https": "http://127.0.0.1:7890",
}

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0.0.0 Safari/537.36"
    )
}

r = requests.get(
    "https://www.reddit.com/",
    headers=headers,
    proxies=PROXIES,
    timeout=15,
)
print("status:", r.status_code)
print(r.text[:200])
