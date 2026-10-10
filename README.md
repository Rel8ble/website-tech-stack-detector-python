# Website tech stack detector in Python: find the CMS, ecommerce platform, frameworks, CDN and email tools of any list of domains (Wappalyzer / BuiltWith alternative API)

A short tutorial for running a **bulk website technology lookup** from Python with the [Website Tech Stack Detector](https://apify.com/rel8ble/website-tech-stack-detector) actor on Apify. Give it a list of domains and get one row per site: CMS, ecommerce platform, JavaScript frameworks, analytics, tag managers, payment processors, CDN, hosting, web server, plus the email provider (MX), the email senders authorised in SPF (Klaviyo, SendGrid, Mailgun, HubSpot...), the DNS provider and the TLS certificate. Every technology comes with a confidence score and the evidence that matched. No Wappalyzer or BuiltWith subscription, no browser extension. Useful for lead generation, CRM enrichment, competitor research and market sizing.

> Disclosure: I built this actor; it's a paid tool on Apify ($3.00 per 1,000 websites). The code in this repo is MIT-licensed.

## How it works

Each site gets one plain HTTP request (no headless browser), DNS lookups (MX, TXT, NS, SOA, CNAME, A, PTR) and one TLS handshake. Headers, cookies, meta tags, script URLs, HTML and DNS records are matched against 7,600+ technology fingerprints (the open Wappalyzer rule set). In a real test run, 45 of 46 domains were analyzed in 25 seconds; the one failure was a domain that doesn't exist, returned as a free error row.

## Quick start (Python)

```bash
pip install apify-client
```

```python
from apify_client import ApifyClient

client = ApifyClient("<YOUR_APIFY_TOKEN>")

run = client.actor("rel8ble/website-tech-stack-detector").call(run_input={
    "urls": ["allbirds.com", "minimalistbaker.com", "nextjs.org", "https://www.hubspot.com"],
    "includeDns": True,        # email provider, SPF senders, DNS provider, TLS
    "includeEvidence": False,  # smaller output; True shows what matched
    "minConfidence": 50,       # drop weak single-signal guesses
})

for site in client.dataset(run["defaultDatasetId"]).iterate_items():
    print(site["domain"], site["cms"], site["ecommerce"], site["cdn"], site["emailProvider"])
```

[`example.py`](example.py) is the runnable version, built for sales prospecting: it reads domains from a text file (or the command line), writes one row per site to `tech_stack.csv`, prints the platform share across the list, and lists the sites that match a target stack (default: Shopify stores, with the email senders each one uses).

```bash
pip install -r requirements.txt
export APIFY_TOKEN=<YOUR_APIFY_TOKEN>
python example.py domains.txt             # one domain per line
python example.py allbirds.com gymshark.com bombas.com
TARGET=WordPress python example.py domains.txt
```

## Quick start (Node.js)

```js
import { ApifyClient } from 'apify-client';

const client = new ApifyClient({ token: '<YOUR_APIFY_TOKEN>' });
const run = await client.actor('rel8ble/website-tech-stack-detector').call({
    urls: ['stripe.com', 'notion.com'], includeEvidence: false,
});
const { items } = await client.dataset(run.defaultDatasetId).listItems();
console.log(items.map((s) => `${s.domain}: ${s.technologyNames.join(', ')}`));
```

## Input

| Field | Default | What it does |
|---|---|---|
| `urls` | - | Domains or URLs: `shopify.com`, `www.example.com`, `https://example.com/pricing` |
| `includeDns` | true | MX, TXT/SPF, NS, CNAME, A/PTR and TLS lookups (email provider, senders, DNS provider, hosting hints) |
| `includeEvidence` | true | Lists what matched for every technology (header, script URL, cookie, meta tag, DNS record) |
| `minConfidence` | 0 | Drop technologies below this confidence (0-100) |
| `includeFailed` | true | Save a free row with the error for sites that could not be loaded |
| `maxConcurrency` | 20 | Sites analyzed in parallel (1-100) |
| `proxyConfiguration` | off | Turn on Apify Proxy (RESIDENTIAL) only if many rows come back `blocked: true` |

## Output sample (real row, run of 24 Sep 2026)

One website = one item. This is `chubbiesshorts.com`, with empty summary columns left out and the `technologies` array cut to 2 of 20 entries:

```json
{
  "inputUrl": "chubbiesshorts.com",
  "url": "https://www.chubbiesshorts.com/",
  "domain": "chubbiesshorts.com",
  "statusCode": 200,
  "blocked": false,
  "technologyCount": 20,
  "technologyNames": ["Cloudflare", "HSTS", "HTTP/3", "Let's Encrypt", "Open Graph", "Priority Hints", "Swiper", "UPS", "Shopify"],
  "dnsTechnologies": ["Anthropic", "Apple iCloud Mail", "Atlassian Cloud", "Cloudflare DNS", "Figma", "Mailgun", "Meta", "Microsoft 365", "Miro", "OpenAI", "Zendesk"],
  "ecommerce": ["Shopify"],
  "javascriptLibraries": ["Swiper"],
  "cdn": ["Cloudflare"],
  "security": ["HSTS", "Let's Encrypt"],
  "hostingProviders": ["Shopify", "Cloudflare"],
  "server": "cloudflare",
  "tlsIssuer": "Let's Encrypt / YE1",
  "tlsExpires": "2026-11-25T21:23:02.000Z",
  "emailProvider": "Microsoft 365",
  "emailSenders": ["Microsoft 365", "Mailgun", "Klaviyo", "Zendesk"],
  "dnsProvider": "Cloudflare",
  "ipAddresses": ["23.227.38.74"],
  "reverseDns": ["shops.myshopify.com"],
  "mxRecords": ["chubbiesshorts-com.mail.protection.outlook.com"],
  "technologies": [
    {
      "name": "Cloudflare",
      "version": null,
      "confidence": 100,
      "categories": ["CDN"],
      "website": "https://www.cloudflare.com",
      "source": "website",
      "evidence": [
        { "type": "headers", "key": "server", "match": "cloudflare" },
        { "type": "dns", "key": "ns", "match": ".cloudflare.com" }
      ]
    },
    {
      "name": "Shopify",
      "version": null,
      "confidence": 50,
      "categories": ["Ecommerce"],
      "website": "https://shopify.com",
      "source": "website",
      "evidence": [
        { "type": "dom", "key": "link[href*='shopify.com'] [href]", "match": "https://cdn.shopify.com/oxygen-v2/.../assets/app-B72nCKlC.css" }
      ]
    }
  ],
  "responseTimeMs": 2492,
  "redirected": true,
  "error": null,
  "scrapedAt": "2026-09-24T05:23:25.766Z"
}
```

`source` is `website` (seen on the page, its headers or cookies) or `dns` (seen only in DNS, e.g. a TXT verification record). The summary columns use `website` matches only; DNS-only tools go to `dnsTechnologies`.

### What the prospect list looks like on that sample

The Shopify stores in the same 46-domain run, as `example.py` prints them:

| Store | Email provider (MX) | Email senders (SPF) | CDN |
|---|---|---|---|
| hismileteeth.com | Google Workspace | Google Workspace, Shopify Email, Mailgun, SendGrid | Cloudflare |
| kyliecosmetics.com | Google Workspace | Proofpoint | Cloudflare, jsDelivr |
| bombas.com | Google Workspace | Google Workspace, Shopify Email, Mailgun | - |
| deathwishcoffee.com | Barracuda | Microsoft 365, Zendesk, HubSpot, SendGrid | Cloudflare |
| chubbiesshorts.com | Microsoft 365 | Microsoft 365, Mailgun, Klaviyo, Zendesk | Cloudflare |
| allbirds.com | Microsoft 365 | Microsoft 365 | Cloudflare |
| gymshark.com | Proofpoint | Proofpoint | Cloudflare |
| brooklinen.com | Mimecast | - | Cloudflare |

Across all 46 domains: WordPress on 9, Shopify on 8, Contentful on 4, WooCommerce on 2; Google Workspace was the email provider for 24 and Microsoft 365 for 6. `g2.com` answered with a bot wall (`blocked: true`) and still returned 22 technologies from headers, DNS and TLS.

## Pricing

Pay per result: **$3.00 per 1,000 websites** analyzed. 10,000 domains cost $30. Sites that fail to load (dead domains, timeouts) are saved but never charged. The Apify free plan's $5 monthly credit covers a list of about 1,600 sites.

## Limits

- **Homepage only** (or the exact URL you pass). A tool that loads only on the checkout or blog page is not seen unless you pass that URL.
- **No JavaScript execution.** Tags loaded inside a Google Tag Manager container can be missed: the actor sees GTM, not always the Google Analytics, Hotjar or Meta Pixel tags inside it. Tags written directly into the page are detected.
- **Bot walls.** Some large sites answer with a challenge page. You still get header, DNS and TLS data with `blocked: true`; a RESIDENTIAL proxy lets more through.
- **Fingerprints are signatures, not certainty.** Use the confidence score and evidence, or `minConfidence: 50` for a strict list.
- Behind a CDN such as Cloudflare the origin host is hidden, so hosting shows the CDN.
- Up to 100 sites in parallel, 120 s page timeout, first 3 MB of HTML analyzed.

## Links

- Actor on the Apify Store: https://apify.com/rel8ble/website-tech-stack-detector
- Apify Python client: https://docs.apify.com/api/client/python
- Fingerprint data: the open [Wappalyzer rule set](https://github.com/enthec/webappanalyzer)

## License

MIT (this example code). The actor itself is a paid Apify tool.
