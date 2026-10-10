"""Rebuild activities.json from the owner's VU23562 repos.

Runs inside the GitHub Action (see .github/workflows/update-activities.yml).
It lists every public repo whose name starts with "vu23562", keeps the ones
with GitHub Pages turned on, reads each page title, and writes activities.json.
The file is only rewritten when the list of activities really changes.
"""
import json
import os
import re
import sys
import urllib.request
import urllib.error

PREFIX = "vu23562"
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(HERE, "activities.json")
SETTINGS = os.path.join(HERE, "settings.json")

owner_repo = os.environ.get("GITHUB_REPOSITORY", "teacherfrances/vu23562")
OWNER, SELF = owner_repo.split("/", 1)
TOKEN = os.environ.get("GITHUB_TOKEN", "")


def get(url, api=False):
    req = urllib.request.Request(url, headers={"User-Agent": "vu23562-homepage"})
    if api:
        req.add_header("Accept", "application/vnd.github+json")
        if TOKEN:
            req.add_header("Authorization", "Bearer " + TOKEN)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.status, r.read().decode("utf-8", "replace")


def list_repos():
    repos, page = [], 1
    while True:
        _, body = get(
            "https://api.github.com/users/%s/repos?per_page=100&type=owner&page=%d" % (OWNER, page),
            api=True,
        )
        batch = json.loads(body)
        repos += batch
        if len(batch) < 100:
            return repos
        page += 1


def page_title(html):
    m = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
    if not m:
        return ""
    t = re.sub(r"\s+", " ", m.group(1)).strip()
    return (t.replace("&amp;", "&").replace("&#39;", "'").replace("&rsquo;", "'")
             .replace("&quot;", '"').replace("&lt;", "<").replace("&gt;", ">"))


def find_page(name, branch):
    """Return (url, title). Prefer the site root; else the first root .html file."""
    base = "https://%s.github.io/%s/" % (OWNER.lower(), name)
    try:
        status, html = get(base)
        if status == 200:
            return base, page_title(html)
    except urllib.error.HTTPError:
        pass
    except Exception as e:  # network hiccup: keep the root link
        print("  could not open %s: %s" % (base, e))
        return base, ""
    try:
        _, body = get("https://api.github.com/repos/%s/%s/contents/?ref=%s" % (OWNER, name, branch), api=True)
        htmls = sorted(f["name"] for f in json.loads(body) if f["name"].lower().endswith(".html"))
        for fname in htmls:
            url = base + urllib.request.quote(fname)
            try:
                status, html = get(url)
                if status == 200:
                    return url, page_title(html)
            except Exception:
                continue
    except Exception as e:
        print("  could not list files in %s: %s" % (name, e))
    return None, ""


def kind_of(name):
    n = name.lower()
    for key, kind in (("deck", "deck"), ("jeopardy", "board"), ("board", "board"),
                      ("phone", "phone"), ("escape", "escape"), ("quiz", "quiz"),
                      ("record", "speak"), ("sayit", "speak"), ("pronun", "speak")):
        if key in n:
            return kind
    return "game"


def main():
    settings = {}
    if os.path.exists(SETTINGS):
        with open(SETTINGS, encoding="utf-8") as f:
            settings = json.load(f)
    hide = {h.lower() for h in settings.get("hide", [])}
    titles = settings.get("titles", {})
    lesson_names = dict(settings.get("lessonNames", {}))

    acts = []
    for r in list_repos():
        name = r["name"]
        low = name.lower()
        if not low.startswith(PREFIX) or low == SELF.lower() or low in hide:
            continue
        if r.get("archived") or r.get("private") or not r.get("has_pages"):
            print("skip (no Pages or archived): " + name)
            continue
        url, title = find_page(name, r.get("default_branch", "main"))
        if not url:
            print("skip (no page found): " + name)
            continue
        m = re.search(r"lesson[-_]?(\d+)", low)
        lesson = int(m.group(1)) if m else None
        kind = kind_of(low)
        if kind == "deck" and lesson and str(lesson) not in settings.get("lessonNames", {}):
            lm = re.search(r"lesson\s*\d+\s*:\s*(.+)$", title, re.I)
            if lm:
                lesson_names[str(lesson)] = lm.group(1).strip()
        acts.append({
            "repo": name,
            "url": url,
            "title": titles.get(name) or title or name,
            "lesson": lesson,
            "kind": kind,
            "created": r.get("created_at", "")[:10],
        })
        print("ok: %s -> %s" % (name, url))

    acts.sort(key=lambda a: (a["lesson"] is None, a["lesson"] or 0, a["created"], a["repo"]))
    new = {"owner": OWNER, "lessonNames": dict(sorted(lesson_names.items(), key=lambda kv: int(kv[0]))),
           "activities": acts}

    old = None
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            old = json.load(f)
            old.pop("updated", None)
    if old == new:
        print("No change.")
        return 0
    from datetime import datetime, timezone
    new["updated"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(new, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print("activities.json updated: %d activities" % len(acts))
    embed_fallback(new)
    return 0


def embed_fallback(data):
    """Copy the list into index.html too, so the page still works if activities.json cannot load."""
    page = os.path.join(HERE, "index.html")
    if not os.path.exists(page):
        return
    with open(page, encoding="utf-8") as f:
        html = f.read()
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    new_html, n = re.subn(
        r'(<script id="fallback" type="application/json">)(.*?)(</script>)',
        lambda m: m.group(1) + blob + m.group(3), html, count=1, flags=re.S)
    if n and new_html != html:
        with open(page, "w", encoding="utf-8") as f:
            f.write(new_html)
        print("index.html backup list updated")


if __name__ == "__main__":
    sys.exit(main())
