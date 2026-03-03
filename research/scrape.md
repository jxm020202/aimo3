# Scraping Kaggle discussions and content with the Kaggle CLI and API key

## Executive summary

Kaggle has an official, supported “data access” surface area (competitions, datasets, notebooks/kernels, models, and notebook outputs) exposed via the **official `kaggle` CLI/Python package**, the **`kagglehub` Python library**, and the underlying **`kagglesdk`** bindings that target Kaggle’s “external-facing endpoints.” citeturn20search8turn17search10turn21view0turn21view1 This official API surface **does not include** a first-class, documented API for **discussion threads and comments** (i.e., forums/discussions), and it also does not provide comprehensive **user profile** retrieval (bio, badges, followers, etc.) in the public CLI/API. citeturn18view3turn12search21

For discussion content specifically, the most “official” alternative is to use Kaggle’s **Meta Kaggle** dataset (site metadata) which includes forum/discussion message data (as HTML) and is reportedly updated daily; this often eliminates the need for scraping Kaggle’s production web UI. citeturn12search21turn12search0turn12search11

If you still need data **not exposed** by the official API (e.g., live discussion pages, dynamic UI-only metadata), “fallback scraping” becomes a web automation problem: dealing with JavaScript rendering, authenticated sessions, and rate limiting. Practically, this tends to be **less reliable** and higher-maintenance than the API, and may violate Kaggle’s terms—so treat it as a last resort. citeturn23search4turn23search16turn24view0

## Officially supported ways to access Kaggle content

### What the official CLI/API covers

The current official tooling stack is best thought of as four “service families,” reflected in the `kaggle` package source:

- **Competitions**: list competitions, list competition data files, download competition files (bulk or per-file), submit, get leaderboard (view/download). citeturn18view0turn15view0turn24view0  
- **Datasets**: list datasets (filters include `user` and `mine`), list dataset files, download, create/version/update metadata/delete (subject to permissions and dataset rules). citeturn18view1turn15view0  
- **Notebooks (Kernels)**: list kernels, list kernel files, pull/get kernel, push/save kernel, download kernel outputs, get run/session status, delete kernels. citeturn18view2turn16view1  
- **Models** (not requested, but relevant for completeness because it’s first-class in the official toolchain): list/get/create/update/delete models, plus model instances/versions and downloads. citeturn19view2turn16view0  

Kaggle also maintains an official Python helper library **`kagglehub`** which focuses on downloading (and sometimes uploading) **datasets, models, and notebook outputs**, with behaviour tailored for running inside Kaggle notebooks (shared cache/attachments) vs locally (download to local cache). citeturn21view0

At the lowest layer, **`kagglesdk`** is published as an automatically generated set of Python bindings for Kaggle’s “external-facing endpoints,” and it is the dependency the modern Kaggle tooling is converging towards. citeturn21view1turn21view2

### What is *not* officially exposed (and why it matters for scraping)

- **Discussions / discussion comments**: there is no documented discussion API in the official CLI/API; the common workaround is Meta Kaggle. citeturn12search21turn18view3  
- **User profiles**: the official API can *filter* content by `user` (e.g., list datasets or kernels by a user), but it does not provide a general “get profile details” client method in the public CLI/API surface. citeturn18view1turn18view2turn18view3  

### Capability matrix for your requested surfaces

| Surface | Official CLI / Python (`kaggle`) | `kagglehub` | Direct HTTP to `/api/v1/...` (legacy-style) | Web UI scraping (HTML/JS) |
|---|---|---|---|---|
| Discussions & comments | Not first-class; use Meta Kaggle dataset | Not supported | Not documented | Possible but brittle; likely ToS-sensitive |
| Datasets | List/files/download/create/version/update metadata/delete | Download (common), plus cache helpers | Common pattern historically | Rarely needed |
| Notebooks (kernels) | List/pull/push/status/output/download | Download notebook outputs | Some endpoints exist | Sometimes needed for UI-only metadata |
| Competitions | List/files/download/submit/leaderboard | Not primary focus | Some endpoints exist | Sometimes needed for UI-only pages |
| User profiles | Indirect (filter content by user) | Not supported | Not documented | Possible but ToS/privacy-sensitive |

The remainder of this report focuses on (a) how to authenticate and use the official tools effectively, and then (b) what fallback scraping looks like when you truly need it.

## Authentication setup with Kaggle CLI, API token, and legacy API key

Kaggle’s tooling now recognises multiple authentication modes:

- **API token** (newer): provided in the Kaggle settings UI, usable via environment variable or token file. citeturn21view0turn20search19  
- **Legacy API credentials** (`kaggle.json` with username + key), still supported. citeturn21view0turn20search16  
- **OAuth login flow** via `kaggle auth login` (supported by the CLI code-path; helpful if Kaggle migrates fully to OAuth). citeturn15view0turn15view3  

### Step-by-step setup (recommended order)

**Step one: install and sanity-check the CLI**

```sh
python -m pip install -U kaggle
kaggle --help
```

The `kaggle` package is the official CLI, and its published “key features” include competitions, datasets, models/model variations, and kernels/notebooks. citeturn17search10turn20search8

**Step two: choose an authentication method**

**Option A: API token (preferred for newer flows)**  
`kagglehub` documents the API token approach clearly, and the same options are aligned with modern Kaggle tooling:

- Put token in environment: `KAGGLE_API_TOKEN=...`
- Or store token in `~/.kaggle/access_token` citeturn21view0turn20search19  

Example:

```sh
export KAGGLE_API_TOKEN="paste_token_here"
```

**Option B: legacy API key file (`kaggle.json`)**  
Download from Kaggle settings under “Legacy API Credentials,” then store at `~/.kaggle/kaggle.json`. citeturn21view0turn20search16  

File permissions matter on Linux/macOS:

```sh
mkdir -p ~/.kaggle
chmod 700 ~/.kaggle
chmod 600 ~/.kaggle/kaggle.json
```

**Option C: OAuth login (`kaggle auth login`)**  
The CLI code explicitly supports OAuth as an authentication method and instructs users to run `kaggle auth login` when OAuth is enabled/required. citeturn15view0turn15view3  

```sh
kaggle auth login
```

### Where credentials are stored and discovered

The official `kaggle` package uses `~/.kaggle` for backwards compatibility, and on Linux can fall back to the XDG config directory if `~/.kaggle` does not exist; this behaviour is in the CLI source. citeturn15view3  
This matters operationally because “it works on my machine” errors often reduce to “the credentials file is not in the path the tool is reading.” citeturn21view0turn20search0

## Practical code patterns

This section provides copy/paste-able examples across: CLI usage, Python usage (official client), direct REST-style HTTP usage (where applicable), and robust retry/pagination strategies.

### Using `kaggle` CLI commands (shell)

The CLI documentation (and code) covers listing + downloading and includes pagination parameters for list-style operations. For competitions, the underlying method supports both `page` and token-based pagination (`page_token`, `page_size`) and prints `next_page_token` when present. citeturn18view0turn15view0

**Competitions**

```sh
# List competitions (search + pagination)
kaggle competitions list --search "titanic" --page-size 20

# List competition data files (useful before downloading)
kaggle competitions files <competition-slug>

# Download all competition data files (often the heaviest endpoint—expect rate limits)
kaggle competitions download -c <competition-slug> -p ./data

# Submit to a competition
kaggle competitions submit -c <competition-slug> -f submission.csv -m "first try"

# Download leaderboard
kaggle competitions leaderboard -c <competition-slug> --download -p ./leaderboards
```

Be aware that heavy “download all data files” operations can trigger HTTP 429/RESOURCE_EXHAUSTED rate limiting, and this seems to affect the download service more than list endpoints. citeturn24view0

**Datasets**

```sh
# Search datasets
kaggle datasets list --search "housing prices" --sort-by votes

# List files in a dataset
kaggle datasets files <owner>/<dataset-slug>

# Download dataset (zip)
kaggle datasets download -d <owner>/<dataset-slug> -p ./datasets --unzip
```

**Notebooks (kernels)**

```sh
# List kernels for a user; kernel-type can be notebook or script
kaggle kernels list --user <username> --kernel-type notebook --sort-by voteCount

# Pull (download) a kernel to a folder
kaggle kernels pull <username>/<kernel-slug> -p ./kernels

# Download kernel output files
kaggle kernels output <username>/<kernel-slug> -p ./kernel_outputs
```

Kernels listing enforces `page_size <= 100` in the official client code, which is a practical hint when designing pagination loops. citeturn18view2

### Using the official Python client (`kaggle` package)

The modern `kaggle` package’s `KaggleApi` class supports: competitions list and pagination tokens, dataset list with per-user filtering and other filters, and kernels list with rich query options. citeturn18view0turn18view1turn18view2

```python
from kaggle.api.kaggle_api_extended import KaggleApi

api = KaggleApi()
api.authenticate()

# Competitions: list with token pagination (preferred when available)
page_token = None
all_refs = []
for _ in range(10):  # safety bound
    resp = api.competitions_list(page_size=20, page_token=page_token)
    if not resp or not resp.competitions:
        break
    all_refs.extend([c.ref for c in resp.competitions])
    page_token = resp.next_page_token
    if not page_token:
        break

print("Fetched competitions:", len(all_refs))

# Datasets: filter by user and search term
datasets = api.dataset_list(search="meta-kaggle", user="kaggle")
print("Datasets found:", len(datasets or []))

# Kernels: list by user (notebooks only) with safe page size
kernels = api.kernels_list(user="someuser", kernel_type="notebook", page_size=50)
print("Kernels:", len(kernels or []))
```

### Robust retries and resumable downloads

The official `kaggle` client includes explicit retry logic:

- A generic `with_retry()` wrapper uses exponential backoff with jitter for retriable transport errors. citeturn15view0  
- `download_file()` streams in chunks, supports resume via `Range` headers (when the server supports `Accept-Ranges: bytes`), and uses a retry loop with exponential backoff (capped) on connection/timeouts while preserving authentication headers. citeturn15view0  

In practice, you typically do not need to reimplement this logic if you use the official client for downloads. But if you build your own (e.g., direct REST calls or scraping), mirror these semantics.

### Calling Kaggle’s REST-style `/api/v1/...` endpoints (where applicable)

Kaggle historically exposed REST-style endpoints under `https://www.kaggle.com/api/v1/...` that many users call with HTTP Basic auth using `username:key`. This is evidenced by official repository issues that include `curl https://www.kaggle.com/api/v1/... -u *****:*****`. citeturn16view0turn16view2turn16view1

Examples seen in the wild (and useful for experimentation / internal tools):

- `POST /api/v1/kernels/push` (kernel upload/push) citeturn16view1  
- `GET /api/v1/competitions/data/download/<competition>/<file>` (download a specific competition file) citeturn16view2  
- `GET /api/v1/models/<owner>/<model>/get` and related model endpoints citeturn16view0  

A minimal Python pattern for Basic Auth requests:

```python
import os
import requests
from requests.auth import HTTPBasicAuth

BASE = "https://www.kaggle.com/api/v1"
user = os.environ["KAGGLE_USERNAME"]
key = os.environ["KAGGLE_KEY"]

r = requests.get(
    f"{BASE}/models/tensorflow/ssd-mobilenet-v1/get",
    auth=HTTPBasicAuth(user, key),
    timeout=30,
)
r.raise_for_status()
data = r.json()
print(data["ref"], data.get("publishTime"))
```

Notes:

- These endpoints and parameters are **not as well documented** as the official CLI surface; treat them as “best effort” and expect breaking changes. citeturn16view0turn18view0turn24view0  
- Some failure modes appear as HTTP 404 (e.g., downloading files with nested paths or mismatched URL patterns), which is highlighted in Kaggle’s own issue tracker. citeturn16view2turn16view3  

## Fallback approaches for non-API surfaces

This section covers discussions/comments and other “UI-only” data. It starts with the most official option (Meta Kaggle), then describes web scraping when Meta Kaggle is insufficient.

### Preferred approach for discussions: use the Meta Kaggle dataset

Multiple sources point to Meta Kaggle as the sanctioned way to access forum/discussion message content at scale: the dataset contains Kaggle metadata and includes **forum message HTML**, reportedly updated daily. citeturn12search21turn12search0turn12search11

This is usually the most stable way to obtain:

- discussion thread/message bodies (HTML),
- timestamps/IDs,
- relationships between topics and messages,
- and some user metadata (depending on Meta Kaggle schema/version). citeturn12search0turn12search11  

A practical workflow:

1. Use official dataset download (`kaggle datasets download`) for `meta-kaggle`.
2. Load the relevant CSV/SQLite tables locally.
3. Parse `ForumMessages` (or similarly named tables) and extract text/media links from the stored HTML.

### Web scraping discussions when you truly need *live* pages

Kaggle’s modern discussion pages are often JavaScript-rendered, which is why “open the URL and parse HTML” frequently yields little or no content in non-browser clients. (In fact, even simple retrieval can fail to surface text without a JS runtime.) citeturn23search16turn14search42

When forced to scrape, you generally have four escalating tiers:

#### Direct HTTP + HTML parsing (static pages only)

Use this only if the content is server-rendered or embedded in the HTML as JSON.

```python
import requests
from bs4 import BeautifulSoup

url = "https://www.kaggle.com/discussions/general/587644"
html = requests.get(url, timeout=30).text
soup = BeautifulSoup(html, "html.parser")

# Example: extract outbound links (media, references)
links = [a["href"] for a in soup.select("a[href]")]
print("found links:", len(links))
```

#### Direct HTTP + authenticated session cookies

If a page requires login, you need a session cookie jar. A safe approach is **not** to automate username/password login (that tends to violate ToS and triggers anti-bot), but instead:

- log in manually in a browser,
- export cookies for `kaggle.com`,
- reuse them in `requests.Session()` for permitted personal automation.

This is the typical pattern for “session cookies + CSRF token” flows:

```python
import requests

sess = requests.Session()
sess.headers.update({"User-Agent": "research-bot/1.0 (contact: you@example.com)"})

# Load cookies (Netscape cookie file or JSON) from a manual login export
# sess.cookies.update(...)

# Fetch a page to obtain CSRF token (often in HTML meta tags or a cookie)
r = sess.get("https://www.kaggle.com/", timeout=30)
r.raise_for_status()

# token = extract_csrf(r.text or sess.cookies)
# then:
# sess.headers.update({"X-CSRF-Token": token})
```

Because Kaggle’s published terms and community discussions repeatedly raise concerns about scraping/crawling and automation, treat this as a last resort and validate against the Terms of Use before proceeding. citeturn23search4turn23search16

#### Headless browser automation for JavaScript-rendered content (Playwright/Selenium)

A headless browser is the most reliable way to get the same DOM the user sees, at the cost of complexity and lower throughput.

Typical workflow:

- open page,
- wait for network to settle and/or a selector that indicates the messages loaded,
- extract structured data from the DOM (or from JSON embedded in script tags),
- optionally intercept network requests to find an internal JSON endpoint (do not rely on it long-term).

Illustrative Playwright snippet:

```python
from playwright.sync_api import sync_playwright

url = "https://www.kaggle.com/discussions/general/587644"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Optional: load cookies saved from a manual login
    # page.context.add_cookies([...])

    page.goto(url, wait_until="networkidle")
    page.wait_for_timeout(1000)

    # Example extraction: all visible text
    text = page.inner_text("body")
    print(text[:2000])

    browser.close()
```

### Downloading attachments and media (including from discussions)

**For official content downloads**, prefer the CLI/API methods (datasets/competition files/kernel outputs), because they integrate retries and resume. citeturn15view0turn20search8

**For media embedded in HTML (e.g., discussion posts)**:

1. parse message HTML for `<img src>`, `<a href>` etc.,
2. normalise URLs,
3. download with streaming and timeouts.

```python
import os
import requests
from urllib.parse import urlparse

def download(url: str, out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    name = os.path.basename(urlparse(url).path) or "file.bin"
    path = os.path.join(out_dir, name)
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                if chunk:
                    f.write(chunk)
    return path
```

If you’re extracting media links from Meta Kaggle forum HTML, you can run this downloader over the extracted URLs without touching the live discussion UI. citeturn12search21turn15view0

## Legal, ethical, and operational best practices

### Kaggle rules, limitations, and ethical posture

Kaggle’s Terms of Use and community conversations strongly suggest that automated access like crawling/scraping and certain forms of automation can be restricted or prohibited, and people asking about automation often do so specifically because they believe scraping/crawling is prohibited. citeturn23search4turn23search16  
Additionally, Kaggle’s Community Guidelines explicitly apply to “all user communication” on Kaggle, including discussions and notebooks—so if your goal is to re-host, republish, or transform user-generated content, you need to consider community expectations and rules around responsible use. citeturn23search0

Given the Australia/Perth context, privacy risk is not theoretical: Australia’s OAIC guidance explicitly calls out “data scraping” as a collection activity that triggers privacy obligations (APP 3/APP 6 considerations) in some scenarios—especially if personal data is involved. citeturn14search27

### Rate limits, throttling, and caching

Official Kaggle infrastructure does rate-limit certain high-cost endpoints. A current example is aggressive 429 rate limiting on competition data file downloads (while list endpoints remain unaffected). citeturn24view0  
Best practices:

- throttle proactively (client-side sleeps, token bucket),
- cache aggressively (ETags/Last-Modified where available; SQLite cache for parsed results),
- checkpoint progress (page tokens, “last seen ID,” downloaded-file manifests),
- prefer bulk downloads via the official API that supports resume/range requests. citeturn15view0turn24view0

### Obstacles you should expect and mitigation strategies

**Dynamic/JS pages**: discussion UI and some profile pages are likely JS-rendered; mitigation is Meta Kaggle dataset first, then headless browser if absolutely needed. citeturn12search21turn23search16  

**Anti-automation signals**: production systems commonly deploy bot detection and CAPTCHAs; Kaggle’s infrastructure references reCAPTCHA in security headers in observed API responses, which is a practical hint that automated UI scraping will be fragile. citeturn16view3  
Mitigation: don’t fight it—reduce automation scope, use the API/Meta Kaggle, and respect blocks.

**API instability in edge cases**: nested paths and endpoint shape changes can cause 404s in download URLs (competition file paths, dataset edge cases). citeturn16view2turn16view3  
Mitigation: always “list files first” and use returned file names verbatim; add fallbacks; store server-returned URLs where possible.

**Credential drift / dependency mismatch**: `kaggle` now depends on `kagglesdk`, and mismatches can cause import errors if versions drift (seen in a 2026 issue). citeturn20search0turn21view1  
Mitigation: pin versions; use `pip install -U kaggle kagglesdk`; run smoke tests in CI.

**User profile completeness**: user profiles aren’t a first-class API object; mitigation is (a) filter/search by user in official endpoints, (b) use Meta Kaggle where possible, (c) avoid scraping profile pages unless clearly permitted. citeturn18view1turn18view2turn12search21

## Comparison of approaches

| Method | Ease | Reliability | Auth required | Rate limits | Data completeness | Code complexity |
|---|---|---|---|---|---|---|
| Official CLI (`kaggle`) | High (batteries included) | High for supported surfaces | Yes for most operations | Moderate; downloads can be heavily limited | High for competitions/datasets/kernels; low for discussions/profiles | Low |
| Official Python client (`kaggle.api.KaggleApi`) | High | High for supported surfaces | Yes | Moderate; can hit 429 on heavy downloads | Same as CLI | Low–Medium |
| `kagglehub` (Python) | High for downloads | High for downloads | Sometimes (token) | Similar to official endpoints | Focused on datasets/models/notebook outputs, not discussions | Low |
| Direct HTTP to `/api/v1/...` | Medium | Medium (less documented; can break) | Usually yes (Basic auth or token) | High variability | Medium–High for specific endpoints; still weak for discussions | Medium |
| HTML scraping (requests + parser) | Medium | Low on JS pages | Sometimes | High variability | Potentially high but brittle | Medium–High |
| Headless browser automation | Low–Medium | Medium (but slow) | Often | High variability | Highest for UI-only data, but expensive | High |

The most robust overall strategy for “scraping Kaggle discussions” is typically: **Meta Kaggle dataset first**, then minimal incremental scraping only for gaps you cannot fill, and only if permitted by Kaggle’s rules and the content’s licensing/privacy posture. citeturn12search21turn23search4turn14search27