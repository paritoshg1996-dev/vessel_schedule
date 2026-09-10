"""
Bakes frontend/data.json into frontend/index_template.html as a fallback,
producing frontend/index.html.

The page always tries `fetch('./data.json')` first -- so when index.html
and data.json are hosted together (GitHub Pages, Netlify, any static
host) and run_pipeline.py refreshes data.json on a schedule, the page
shows live data automatically with no rebuild needed.

This bake step exists only so the file also looks right if someone opens
index.html directly from disk (or downloads a single file), where a
browser's local file:// restrictions block fetch(). Re-run this after
any run_pipeline.py run if you want that offline copy current too.
"""
import json

with open("frontend/data.json") as f:
    data = json.load(f)

with open("frontend/index_template.html") as f:
    template = f.read()

output = template.replace("__EMBEDDED_DATA__", json.dumps(data, separators=(",", ":")))

with open("frontend/index.html", "w") as f:
    f.write(output)

print(f"Wrote frontend/index.html ({len(output):,} bytes) with {len(data['vessels'])} vessel rows embedded.")
