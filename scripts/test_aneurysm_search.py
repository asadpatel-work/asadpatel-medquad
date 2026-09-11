import subprocess

import requests

PROJECT_ID = "capstone-506616"
LOCATION = "global"
ENGINE_ID = "medquad-search-app-v1"

token = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True).strip()
headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json",
    "X-Goog-User-Project": PROJECT_ID,
}

search_url = f"https://discoveryengine.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/collections/default_collection/engines/{ENGINE_ID}/servingConfigs/default_search:search"

payload = {
    "query": "tell me about aneurysms",
    "pageSize": 3,
    "contentSearchSpec": {
        "snippetSpec": {"returnSnippet": True},
        "summarySpec": {"summaryResultCount": 2, "includeCitations": True}
    }
}

resp = requests.post(search_url, headers=headers, json=payload)
print(f"Status Code: {resp.status_code}")
data = resp.json()
print(f"Total Size: {data.get('totalSize')}")
print("Results:")
for r in data.get("results", []):
    print(" - ID:", r.get("id"))
    print("   Title:", r.get("document", {}).get("structData", {}).get("title"))
    print("   RankSignals:", r.get("rankSignals"))
