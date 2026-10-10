"""Tech stack prospecting with the Website Tech Stack Detector actor on Apify.

1. Reads domains from a text file (one per line) or from the command line.
2. Detects each site's stack and writes one row per site to tech_stack.csv.
3. Prints the platform share across the list, then the sites that run TARGET
   (default: Shopify) with their email provider and email senders.

Usage:
    pip install -r requirements.txt
    set APIFY_TOKEN=...   (or export APIFY_TOKEN=... on macOS/Linux)
    python example.py domains.txt
    python example.py allbirds.com gymshark.com bombas.com
"""
import csv
import os
import sys
from collections import Counter

from apify_client import ApifyClient

TOKEN = os.environ.get("APIFY_TOKEN", "<YOUR_APIFY_TOKEN>")
TARGET = os.environ.get("TARGET", "Shopify")

args = sys.argv[1:] or ["allbirds.com", "gymshark.com", "minimalistbaker.com", "nextjs.org"]
if len(args) == 1 and os.path.isfile(args[0]):
    with open(args[0], encoding="utf-8") as f:
        domains = [line.strip() for line in f if line.strip() and not line.startswith("#")]
else:
    domains = args

client = ApifyClient(TOKEN)
run = client.actor("rel8ble/website-tech-stack-detector").call(run_input={
    "urls": domains,
    "includeDns": True,        # email provider, SPF senders, DNS provider, TLS
    "includeEvidence": False,  # keep the output small; the CSV only needs names
    "minConfidence": 50,       # drop weak single-signal guesses
})
sites = list(client.dataset(run["defaultDatasetId"]).iterate_items())

LIST_COLS = ["cms", "ecommerce", "javascriptFrameworks", "analytics", "tagManagers",
             "marketingAutomation", "paymentProcessors", "cdn", "emailSenders", "dnsTechnologies"]
TEXT_COLS = ["emailProvider", "dnsProvider", "server", "tlsExpires", "blocked", "error"]


def join(site, col):
    return ", ".join(site.get(col) or [])


with open("tech_stack.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["domain"] + LIST_COLS + TEXT_COLS)
    for s in sites:
        w.writerow([s.get("domain")] + [join(s, c) for c in LIST_COLS] + [s.get(c) for c in TEXT_COLS])

ok = [s for s in sites if not s.get("error")]
print(f"Saved {len(sites)} rows to tech_stack.csv ({len(ok)} analyzed, {len(sites) - len(ok)} failed and free)\n")

platforms = Counter(name for s in ok for name in (s.get("cms") or []) + (s.get("ecommerce") or []))
print("Platform share:")
for name, n in platforms.most_common(10):
    print(f"  {name:<28}{n:>4}  {n / len(ok):.0%}")

hits = [s for s in ok if TARGET in (s.get("technologyNames") or [])]
print(f"\nSites running {TARGET}: {len(hits)}")
for s in hits:
    print(f"  {s['domain']:<28}{s.get('emailProvider') or '-':<20}{join(s, 'emailSenders') or '-'}")

blocked = [s["domain"] for s in ok if s.get("blocked")]
if blocked:
    print(f"\nBehind a bot wall (headers, DNS and TLS only): {', '.join(blocked)}")
