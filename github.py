import requests
from collections import defaultdict, Counter
from datetime import datetime
import pytz
from secrets import GITHUB_TOKEN  # Ensure you have a secrets.py file with your GitHub token

# -------------------------------
# Configuration
# -------------------------------
GITHUB_USERNAME = "Naman-1608"  # Replace with your GitHub username


HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}"
}

BASE_URL = "https://api.github.com"


# -------------------------------
# Helper Functions
# -------------------------------

def get_repositories(username):
    repos = []
    page = 1
    while True:
        url = f"{BASE_URL}/users/{username}/repos?per_page=100&page={page}"
        response = requests.get(url, headers=HEADERS)
        data = response.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def get_language_stats(repos):
    language_totals = defaultdict(int)
    for repo in repos:
        if not repo["fork"]:
            lang_url = repo["languages_url"]
            lang_data = requests.get(lang_url, headers=HEADERS).json()
            for lang, bytes_count in lang_data.items():
                language_totals[lang] += bytes_count
    total = sum(language_totals.values())
    language_percentages = {lang: round((count / total) * 100, 2) for lang, count in language_totals.items()}
    return language_percentages

def get_commit_times(repos, username):
    time_of_day_counter = Counter()
    day_of_week_counter = Counter()
    for repo in repos:
        if repo["fork"]:
            continue
        commits_url = f"{BASE_URL}/repos/{username}/{repo['name']}/commits?author={username}&per_page=100"
        commits = requests.get(commits_url, headers=HEADERS).json()
        if isinstance(commits, dict) and commits.get("message"):
            continue  # Skip error messages
        for commit in commits:
            try:
                commit_date = commit["commit"]["author"]["date"]
                dt = datetime.strptime(commit_date, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
                local_time = dt.astimezone()  # convert to local time
                hour = local_time.hour
                weekday = local_time.strftime("%A")
                
                if 5 <= hour < 12:
                    time_of_day_counter["Morning"] += 1
                elif 12 <= hour < 17:
                    time_of_day_counter["Daytime"] += 1
                elif 17 <= hour < 21:
                    time_of_day_counter["Evening"] += 1
                else:
                    time_of_day_counter["Night"] += 1
                
                day_of_week_counter[weekday] += 1
            except Exception:
                continue
    return time_of_day_counter, day_of_week_counter

def get_total_contributions(username):
    query = """
    query ($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
          }
        }
      }
    }
    """
    json_data = {
        "query": query,
        "variables": {"login": username}
    }
    response = requests.post("https://api.github.com/graphql", json=json_data, headers=HEADERS)
    return response.json()["data"]["user"]["contributionsCollection"]["contributionCalendar"]["totalContributions"]

# -------------------------------
# Main Script
# -------------------------------

def main():
    print(f"📊 Fetching GitHub data for {GITHUB_USERNAME}...")
    
    repos = get_repositories(GITHUB_USERNAME)
    public_repos = [r for r in repos if not r['private']]
    private_repos = [r for r in repos if r['private']]

    print(f"\n> 📜 Public Repositories: {len(public_repos)}")
    print(f"> 🔒 Private Repositories: {len(private_repos)}")

    contributions = get_total_contributions(GITHUB_USERNAME)
    print(f"> 🏆 Contributions in 2025: {contributions}")

    langs = get_language_stats(public_repos)
    print("\n💬 Programming Languages Breakdown:")
    for lang, pct in sorted(langs.items(), key=lambda x: x[1], reverse=True):
        print(f"- {lang}: {pct}%")

    time_of_day, day_of_week = get_commit_times(public_repos, GITHUB_USERNAME)
    print("\n🌞 Time of Day Commit Distribution:")
    for period in ["Morning", "Daytime", "Evening", "Night"]:
        print(f"- {period}: {time_of_day.get(period, 0)} commits")

    print("\n📅 Commit Activity by Day:")
    for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
        print(f"- {day}: {day_of_week.get(day, 0)} commits")

    print("\n💻 Operating System: Windows (set manually)")
    print("🔥 Editor: Data not available via GitHub API (consider Wakatime)")
    print("📦 Storage Used: Not exposed via GitHub API")

if __name__ == "__main__":
    main()
