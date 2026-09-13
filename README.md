<div align="center">

# zlib-dl

从 Z-Library（Z站）搜索并下载电子书的 Agent Skill，为国内网络环境设计

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Dependencies](https://img.shields.io/badge/dependencies-stdlib%20only-brightgreen)

[English](#english) | 简体中文

</div>

---

## 实际效果

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

挑一条 `dl:` 令牌，一条命令下载，脚本自动校验文件完整性。

## 它处理的问题

国内网络下从 Z 站拿书有几道坎。主域名被 DNS 污染，nslookup 和 DoH 都解析到假 IP；镜像域名隔三差五轮换，硬编码必死；站点在应用层之前挡了一道 SHA1 反爬质询；游客每天只能下 1 本，免费账号 10 本，配额金贵。

| 道坎 | 处理方式 |
|---|---|
| 镜像不可达 | `probe` 从 GitHub 仓库 [Awesome-Zlibrary](https://github.com/dongyubin/Awesome-Zlibrary) 读最新可用镜像（走 `api.github.com`），跟随重定向拿到真实后端，缓存到 `~/.zlib_dl_mirror` |
| SHA1 质询 | 解析质询页的混淆 JS，本地穷举工作量证明（约 6.5 万次尝试，毫秒级），写回 `c_token`/`c_time` 两个 cookie 自动重试 |
| 站点改版 | 结果条目一夜之间从 `<a>` 换成 `<z-bookcard>` 组件这种事发生过。[references/protocol.md](references/protocol.md) 记了两代结构的解析方法和排查思路 |
| 配额浪费 | 无凭据时 `download` 拒绝执行并打印配置指引（零网络请求）；凭据齐全时整个下载恰好只发一次请求，服务端返回网页就停下报告 |

## 安装

两种装法，任选其一：

- 把仓库地址交给 Agent，让它克隆进自己的技能发现目录
- 或 `npx skills add <仓库地址>`

要求 Python 3.10+。脚本只用标准库，没有第三方依赖。

## 配置

登录任意 Z 站镜像，从浏览器开发者工具的 cookie 里取 `remix_userid` 和 `remix_userkey`，写进环境变量：

```powershell
setx ZLIB_REMIX_USERID <数字id>
setx ZLIB_REMIX_USERKEY <userkey>
```

bash 用 `export`，写进 `.bashrc` 持久。也支持 `ZLIB_COOKIE`（整串 cookie，优先级更高）和 `ZLIB_MIRROR`（固定镜像地址）。凭据只走环境变量，不落文件、不进日志。

未配置凭据时 `probe` 和 `search` 照常能跑，`download` 会被拒绝并打印上面的配置指引。确要动用游客那次下载，显式加 `--guest`。

## 使用

```bash
python scripts/zlib_dl.py probe                                 # 发现并验证镜像（免费）
python scripts/zlib_dl.py search "书名" --ext pdf --lang 中文   # 搜书（免费）
python scripts/zlib_dl.py download "/dl/<令牌>" --name 书名     # 下载（消耗配额）
python scripts/zlib_dl.py verify 书名.pdf                       # 完整性校验
```

下载令牌来自 search 输出的 `dl:` 行。每次 `download` 恰好发出一次请求，服务端返回网页说明配额用尽或会话失效，脚本会停下报告而不是盲目重试。保存后自动校验：PDF 要 `%PDF` 头加结尾的 `%%EOF`，epub 要 `PK\x03\x04`，mobi/azw3 看偏移 60 处的 `BOOKMOBI`。

## 配额与数据边界

| 身份 | 每日下载 |
|---|---|
| 游客 | 1 次，失败也占额 |
| 免费注册账号 | 10 次 |

`probe` 和 `search` 不消耗配额。脚本只与两方通信：GitHub（读镜像表）和 Z-Library 镜像，搜索词会经过这两方。

## 兼容范围

在国内裸网络（无代理、Windows 10）实测通过：镜像发现、质询破解、搜索、下载、校验全流程。Linux/macOS 代码路径相同，未实测。镜像域名由第三方仓库维护，轮换属正常现象，缓存失效删掉 `~/.zlib_dl_mirror` 重跑 `probe` 即可。

## 免责声明

本项目仅供个人学习与技术研究。请遵守所在地区法律法规，尊重作者版权，支持正版。项目与 Z-Library 官方无任何关联，不对第三方服务的可用性负责，请合理控制请求频率。

## License

[MIT](./LICENSE) © aasaa444

---

<div align="center">

## English

</div>

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
