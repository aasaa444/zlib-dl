#!/usr/bin/env python3
"""zlib_dl.py — Z-Library mirror probe / search / download with PoW-gate handling.

Subcommands:
  probe                                   find a reachable mirror and verify access
  search <query> [--ext E] [--lang L] [--limit N]
  download <book_path_or_url> [--out DIR]
  verify <file>

Credentials (environment variables):
  ZLIB_REMIX_USERID / ZLIB_REMIX_USERKEY   logged-in cookies (10 downloads/day)
  ZLIB_COOKIE                              full cookie string, takes precedence
  ZLIB_MIRROR                              pin mirror base URL, skips discovery

Without credentials, search and probe work as guest, but `download` refuses
(the anonymous quota is 1/day and burns even on failure); pass --guest to
override deliberately.

Standard library only. Discovered mirrors are cached at ~/.zlib_dl_mirror.
"""
import argparse
import hashlib
import http.cookiejar
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
AWESOME_README = "https://api.github.com/repos/dongyubin/Awesome-Zlibrary/readme"
CACHE_FILE = os.path.join(os.path.expanduser("~"), ".zlib_dl_mirror")
FETCH_TRIES = 6

OPENER, JAR = None, None


def opener():
    global OPENER, JAR
    if OPENER is None:
        JAR = http.cookiejar.CookieJar()
        OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(JAR))
        OPENER.addheaders = [("User-Agent", UA),
                             ("Accept-Language", "zh-CN,zh;q=0.9,en;q=0.8")]
    return OPENER, JAR


def set_cookie(host, name, value):
    _, jar = opener()
    jar.set_cookie(http.cookiejar.Cookie(
        0, name, value, None, False, host, False, False, "/",
        False, False, None, False, None, None, {}))


def apply_user_cookies(host):
    cookie = os.environ.get("ZLIB_COOKIE", "").strip()
    if cookie:
        for pair in cookie.split(";"):
            key, _, val = pair.strip().partition("=")
            if key:
                set_cookie(host, key, val)
        return
    uid = os.environ.get("ZLIB_REMIX_USERID", "").strip()
    key = os.environ.get("ZLIB_REMIX_USERKEY", "").strip()
    if uid and key:
        set_cookie(host, "remix_userid", uid)
        set_cookie(host, "remix_userkey", key)


def logged_in():
    cookie = os.environ.get("ZLIB_COOKIE", "").strip()
    if cookie:
        return True
    return bool(os.environ.get("ZLIB_REMIX_USERID", "").strip()
                and os.environ.get("ZLIB_REMIX_USERKEY", "").strip())


def solve_pow(challenge):
    """JS gate: find i so sha1(challenge+i)[n1]==0xB0 and [n1+1]==0x0B,
    where n1 = int(challenge[0], 16)."""
    n1 = int(challenge[0], 16)
    prefix = challenge.encode()
    i = 0
    while True:
        d = hashlib.sha1(prefix + str(i).encode()).digest()
        if d[n1] == 0xB0 and d[n1 + 1] == 0x0B:
            return i
        i += 1


def fetch(url, data=None, tries=FETCH_TRIES):
    """GET with automatic 503 PoW-gate solving. Returns (headers, body, final_url)."""
    op, _ = opener()
    last_err = "unreachable"
    for _ in range(tries):
        req = urllib.request.Request(url, data=data)
        try:
            r = op.open(req, timeout=90)
            return r.headers, r.read(), r.geturl()
        except urllib.error.HTTPError as e:
            body = e.read()
            if e.code == 503 and b"Checking your browser" in body:
                m = re.search(rb"'([0-9A-F]{40})'", body)
                if m:
                    chal = m.group(1).decode()
                    token = chal + str(solve_pow(chal))
                    host = urllib.parse.urlparse(url).hostname
                    set_cookie(host, "c_token", token)
                    set_cookie(host, "c_time", "0.42")
                last_err = "503 gate"
                continue
            raise RuntimeError(f"HTTP {e.code} for {url}: {body[:200]!r}") from e
        except urllib.error.URLError as e:
            last_err = str(e.reason)
    raise RuntimeError(f"gave up on {url} after {tries} attempts (last: {last_err})")


def discover_mirrors():
    """Parse China-reachable (check-marked) domains from the Awesome-Zlibrary README."""
    req = urllib.request.Request(AWESOME_README,
                                 headers={"Accept": "application/vnd.github.raw"})
    with urllib.request.urlopen(req, timeout=30) as r:
        text = r.read().decode("utf-8", "replace")
    urls = []
    for line in text.splitlines():
        if "\u2705" not in line or "~~" in line:  # ✅ rows only, skip struck-through
            continue
        for m in re.findall(r"https?://[^\)\|\s\]]+", line):
            u = m.rstrip("/）)]，")
            if u not in urls:
                urls.append(u)
    return urls


def resolve_base(url, hops=5):
    """Follow redirects (intl.su -> rotating backend) and return scheme://host."""
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k):
            return None
    op = urllib.request.build_opener(NoRedirect)
    cur = url
    for _ in range(hops):
        req = urllib.request.Request(cur, headers={"User-Agent": UA})
        try:
            op.open(req, timeout=20)
            break
        except urllib.error.HTTPError as e:
            loc = e.headers.get("Location") if e.headers else None
            if e.code in (301, 302, 303, 307, 308) and loc:
                cur = urllib.parse.urljoin(cur, loc)
                continue
            break  # 503 gate or other: this host is the backend
    p = urllib.parse.urlparse(cur)
    return f"{p.scheme}://{p.netloc}"


def check_base(base):
    """One gated request to confirm the mirror works end to end."""
    apply_user_cookies(urllib.parse.urlparse(base).hostname)
    fetch(base + "/")
    return True


def get_base(cli_mirror=None):
    base = cli_mirror or os.environ.get("ZLIB_MIRROR", "").strip()
    if base:
        apply_user_cookies(urllib.parse.urlparse(base).hostname)
        return base
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            base = f.read().strip()
        if base:
            apply_user_cookies(urllib.parse.urlparse(base).hostname)
            return base
    except OSError:
        pass
    print("[*] discovering mirrors from Awesome-Zlibrary ...", file=sys.stderr)
    for url in discover_mirrors():
        try:
            candidate = resolve_base(url)
        except urllib.error.URLError as e:
            print(f"[--] {url}: unreachable ({e.reason})", file=sys.stderr)
            continue
        try:
            check_base(candidate)
        except Exception as e:
            print(f"[--] {candidate}: {e}", file=sys.stderr)
            continue
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(candidate)
        print(f"[OK] {candidate}", file=sys.stderr)
        return candidate
    sys.exit("no reachable mirror found; set ZLIB_MIRROR or see references/protocol.md")


# ---------------------------------------------------------------- subcommands

def cmd_probe(_args):
    for url in discover_mirrors():
        try:
            base = resolve_base(url)
        except urllib.error.URLError as e:
            print(f"[--] {url}: unreachable ({e.reason})")
            continue
        try:
            check_base(base)
        except Exception as e:
            print(f"[--] {base}: {e}")
            continue
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(base)
        state = "logged-in" if logged_in() else "GUEST (1 download/day)"
        print(f"[OK] {base}  cookies: {state}  cached -> {CACHE_FILE}")
        return
    sys.exit("no reachable mirror found; set ZLIB_MIRROR or see references/protocol.md")


# search results are <z-bookcard> web components; attributes span multiple lines
BOOKCARD = re.compile(r'<z-bookcard\b([^>]*)>', re.S)


def attr(attrs, name):
    m = re.search(name + r'="([^"]*)"', attrs)
    return m.group(1) if m else ""


def cmd_search(args):
    base = get_base(args.mirror)
    _, body, _ = fetch(base + "/s/" + urllib.parse.quote(args.query))
    html = body.decode("utf-8", "replace")
    rows, seen = [], set()
    for m in BOOKCARD.finditer(html):
        attrs = m.group(1)
        path = attr(attrs, "href")
        if not path.startswith("/book/") or path in seen:
            continue
        seen.add(path)
        rows.append({
            "path": path, "dl": attr(attrs, "download"),
            "publisher": attr(attrs, "publisher"), "language": attr(attrs, "language"),
            "year": attr(attrs, "year"), "ext": attr(attrs, "extension"),
            "size": attr(attrs, "filesize"), "rating": attr(attrs, "rating"),
        })
    if args.ext:
        rows = [r for r in rows if r["ext"].lower() == args.ext.lower()]
    if args.lang:
        rows = [r for r in rows if args.lang.lower() in r["language"].lower()]
    if not rows:
        print("no results" + (f" for ext={args.ext}" if args.ext else ""))
        return
    print(f"{len(rows)} result(s):")
    for i, r in enumerate(rows[: args.limit], 1):
        slug = urllib.parse.unquote(r["path"].rsplit("/", 1)[-1]).replace(".html", "")
        print(f"{i:>3}. [{r['ext'].upper():<4}] {r['size']:>10}  {r['language']:<8} "
              f"{r['year']:<4} rating={r['rating'] or '-':<3} {slug[:56]}")
        print(f"     dl: {r['dl'] or '(none)'}    {r['path']}")


def content_ext(ctype):
    return {"application/pdf": ".pdf",
            "application/epub+zip": ".epub"}.get(ctype.split(";")[0].strip().lower())


def verify_bytes(body, name):
    if not body:
        return False, "empty file"
    low = name.lower()
    if body[:5] == b"%PDF-" or low.endswith(".pdf"):
        ok = body[:5] == b"%PDF-" and b"%%EOF" in body[-2048:]
        return ok, f"pdf header={body[:8]!r} tail_eof={b'%%EOF' in body[-2048:]}"
    if body[:4] == b"PK\x03\x04":
        return True, "epub/zip header"
    if len(body) > 68 and body[60:68] == b"BOOKMOBI":
        return True, "mobi/azw3 header"
    return len(body) > 1024, "unknown type (size check only)"


GUEST_BLOCKED = """refusing to download in guest mode: the anonymous quota is 1 download/day
and is consumed even if the transfer later fails.

If the user pasted their cookie to you, configure it yourself and retry:
set ZLIB_REMIX_USERID / ZLIB_REMIX_USERKEY (export for this session,
setx on Windows to persist), then run `probe` and expect "logged-in".

Manual setup for the user:

  1. Log in at any Z-Library mirror in your browser
  2. DevTools > Application > Cookies > copy `remix_userid` and `remix_userkey`
  3. Windows (persistent):  setx ZLIB_REMIX_USERID <id>
                            setx ZLIB_REMIX_USERKEY <key>   (open a new terminal)
     bash:                  export ZLIB_REMIX_USERID=<id> ZLIB_REMIX_USERKEY=<key>
  4. Confirm with: zlib_dl.py probe   (should print "cookies: logged-in")

To burn the 1/day anonymous download deliberately, re-run with --guest."""


def cmd_download(args):
    # quota gate BEFORE any network activity: guests get 1 download/day and the
    # attempt is burned even on failure, so refuse and teach instead
    if not args.guest and not logged_in():
        sys.exit(GUEST_BLOCKED)
    base = get_base(args.mirror)
    target = args.target
    if target.startswith("http"):
        target = urllib.parse.urlparse(target).path
    if target.startswith("/dl/"):
        dl_url = target  # token straight from search output (z-bookcard download attr)
    elif target.startswith("/book/"):
        _, body, _ = fetch(base + target)
        html = body.decode("utf-8", "replace")
        m = (re.search(r'class="[^"]*dlButton[^"]*"[^>]*href="(/dl/[^"]+)"', html)
             or re.search(r'href="(/dl/[^"]+)"[^>]*class="[^"]*dlButton', html))
        if not m:
            sys.exit('book page carries no server-rendered download button (SPA). '
                     'Run search and pass the `dl:` token of the wanted row, '
                     'e.g. download "/dl/xxxxxxxx"')
        dl_url = m.group(1)
    else:
        sys.exit("target must be a /dl/ token (from search) or a /book/... path/URL")
    # the /dl/ request IS the quota-consuming call: issue it exactly once
    headers, body, _ = fetch(base + dl_url)
    ctype = headers.get("Content-Type", "")
    if "html" in ctype.lower():
        state = "logged-in" if logged_in() else "GUEST"
        sys.exit("download rejected: server returned a web page instead of a file "
                 f"(daily quota exhausted or session invalid; mode={state}). "
                 "Do not retry immediately — quota is per day.")
    if target.startswith("/book/"):
        fname = urllib.parse.unquote(target.rsplit("/", 1)[-1]).replace(".html", "")
    else:
        fname = args.name or target.rsplit("/", 1)[-1]
    fname = re.sub(r'[\\/:*?"<>|]+', "_", fname)[:80]
    ext = content_ext(ctype)
    if ext and not fname.lower().endswith(ext):
        fname += ext
    os.makedirs(args.out, exist_ok=True)
    out = os.path.join(args.out, fname)
    with open(out, "wb") as f:
        f.write(body)
    ok, note = verify_bytes(body, out)
    print(f"saved: {out}")
    print(f"size : {len(body)} bytes  type={ctype}")
    print(f"check: {'OK' if ok else 'FAILED'} ({note})")
    sys.exit(0 if ok else 2)


def cmd_verify(args):
    with open(args.file, "rb") as f:
        body = f.read()
    ok, note = verify_bytes(body, args.file)
    print(f"size : {len(body)} bytes")
    print(f"check: {'OK' if ok else 'FAILED'} ({note})")
    sys.exit(0 if ok else 2)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("probe", help="find and verify a reachable mirror")
    p = sub.add_parser("search", help="search books (free, no quota)")
    p.add_argument("query")
    p.add_argument("--ext", help="filter by extension, e.g. pdf")
    p.add_argument("--lang", help="filter by language substring, e.g. 中文 or english")
    p.add_argument("--limit", type=int, default=15)
    p.add_argument("--mirror", help="mirror base URL (default: auto)")
    p.set_defaults(func=cmd_search)
    p = sub.add_parser("download", help="download one book (consumes daily quota)")
    p.add_argument("target", help="/dl/ token from search output, or /book/... path/URL")
    p.add_argument("--out", default=".", help="output directory")
    p.add_argument("--name", help="file name for /dl/ targets (default: token id)")
    p.add_argument("--guest", action="store_true",
                   help="allow downloading without credentials (burns the 1/day anonymous quota)")
    p.add_argument("--mirror", help="mirror base URL (default: auto)")
    p.set_defaults(func=cmd_download)
    p = sub.add_parser("verify", help="check a downloaded file's integrity")
    p.add_argument("file")
    p.set_defaults(func=cmd_verify)
    args = ap.parse_args()
    if args.cmd == "probe":
        cmd_probe(args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
