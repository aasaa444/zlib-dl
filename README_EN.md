<div align="center">

# zlib-dl

An Agent Skill to search and download ebooks from Z-Library, built for censored networks

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Dependencies](https://img.shields.io/badge/dependencies-stdlib%20only-brightgreen)

English | [简体中文](./README.md)

</div>

---

## What it looks like

```text
$ python scripts/zlib_dl.py search "信号与噪声" --ext pdf --limit 3
21 result(s):
  1. [PDF ]   21.72 MB  Chinese  2013 rating=0.0 信号与噪声大数据时代预测的科学与艺术
     dl: /dl/gmePQdPbXa    /book/K5npJPpmzV/信号与噪声大数据时代预测的科学与艺术.html
  2. [PDF ]    6.55 MB  Chinese  2013 rating=5.0 信号与噪声大数据时代预测的科学与艺术
     dl: /dl/xXoZRN3Ln6    /book/r9bbapM79B/信号与噪声大数据时代预测的科学与艺术.html
  3. [PDF ]    8.36 MB  Chinese  2013 rating=0.0 信号与噪声大数据时代预测的科学与艺术
     dl: /dl/wXbyJdOJnY    /book/nz2wNpmNqb/信号与噪声大数据时代预测的科学与艺术.html
```

Pick a `dl:` token, run one command, and the script saves the file and checks its integrity.

## The problems it handles

Getting a book off Z-Library from a censored network means dealing with a few obstacles. The main domains are DNS-poisoned, so both nslookup and DoH resolve to fake IPs. Mirror domains rotate every few weeks, so hardcoding them never survives. The site sits behind a SHA-1 proof-of-work gate before the application layer even answers. And downloads are scarce: 1 per day for guests, 10 per day for a free account.

| Obstacle | How it is handled |
|---|---|
| Unreachable mirrors | `probe` reads the latest working mirrors from the [Awesome-Zlibrary](https://github.com/dongyubin/Awesome-Zlibrary) GitHub repo (via `api.github.com`), follows redirects to the real backend, and caches the result in `~/.zlib_dl_mirror` |
| SHA-1 PoW gate | Parses the obfuscated challenge page, solves the proof of work locally (~65k hash attempts, milliseconds), writes back the `c_token`/`c_time` cookies and retries automatically |
| Site redesigns | The result entries once switched from `<a>` tags to `<z-bookcard>` components overnight. [references/protocol.md](references/protocol.md) documents both parsers and the debugging playbook |
| Wasted quota | Without credentials, `download` refuses to run and prints setup instructions (zero network requests); with credentials, each download sends exactly one request and stops on any HTML response instead of retrying blindly |

## Install

Either hand the repo URL to your agent and have it clone the folder into its skill discovery directory, or run `npx skills add <repo-url>`.

Requires Python 3.10+. The script uses only the standard library.

## Setup

Log in to any Z-Library mirror, open browser DevTools, and copy `remix_userid` and `remix_userkey` from the cookies:

```powershell
setx ZLIB_REMIX_USERID <numeric-id>
setx ZLIB_REMIX_USERKEY <userkey>
```

On bash use `export` and put it in `.bashrc`. Two optional variables: `ZLIB_COOKIE` (a full cookie string, takes precedence) and `ZLIB_MIRROR` (pin a mirror). Credentials only travel through environment variables — they are never written to files or logs.

Without credentials, `probe` and `search` still work as guest, and `download` refuses to run while printing the instructions above. To spend the single guest download on purpose, pass `--guest`.

## Usage

```bash
python scripts/zlib_dl.py probe                                  # find and verify a mirror (free)
python scripts/zlib_dl.py search "book title" --ext pdf          # search (free)
python scripts/zlib_dl.py download "/dl/<token>" --name book     # download (consumes quota)
python scripts/zlib_dl.py verify book.pdf                        # integrity check
```

Download tokens come from the `dl:` line in search output. Each `download` sends exactly one request; an HTML response means the quota is gone or the session expired, and the script stops and reports instead of retrying. Saved files are verified automatically: PDF needs a `%PDF` header plus a trailing `%%EOF`, epub needs `PK\x03\x04`, mobi/azw3 needs `BOOKMOBI` at offset 60.

## Quota and data boundaries

| Identity | Downloads per day |
|---|---|
| Guest | 1, burned even on failure |
| Free account | 10 |

`probe` and `search` cost nothing. The script talks to exactly two parties: GitHub (the mirror list) and the Z-Library mirror; your search terms pass through both.

## Compatibility

Tested end to end on an unproxied Windows 10 connection inside mainland China: mirror discovery, gate solving, search, download, integrity checks. The Linux/macOS code paths are identical but untested. Mirror domains are maintained by a third-party repo and rotating is normal; if the cache goes stale, delete `~/.zlib_dl_mirror` and run `probe` again.

## Disclaimer

This project is for personal study and technical research only. Follow the laws of your jurisdiction, respect authors' rights, and buy books when you can. Not affiliated with Z-Library, no warranty for third-party availability, and please keep request rates reasonable.

## License

[MIT](./LICENSE) © aasaa444
