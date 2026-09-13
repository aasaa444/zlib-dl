<div align="center">

# 📥 zlib-dl

[简体中文](#简体中文) | [English](#english)

从 Z-Library 搜索并下载电子书的 Agent Skill

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Dependencies](https://img.shields.io/badge/dependencies-stdlib%20only-brightgreen)

</div>

## 简体中文

**本项目仅供个人学习、研究与技术演示。请遵守所在地区法律法规，尊重版权，仅用于你有合法权限访问的资源、公版或开放许可文档、以及你本人拥有或获授权的内容。作者不承担相关法律责任，使用风险自负。**

### 为什么写这个工具

国内网络从 Z 站拿书，域名被污染、镜像常轮换、站点有 SHA1 反爬质询，这些脚本都能自己扛。真正难的是配额：游客一天 1 次，免费账号一天 10 次，下载失败照样扣。所以整个 skill 只守一条原则——搜书免费，下载克制：默认 PDF，下前确认，下后校验，绝不盲目重试。

### 特性

- **镜像自动发现** — 从 GitHub 的 [Awesome-Zlibrary](https://github.com/dongyubin/Awesome-Zlibrary) 仓库读最新可用镜像，跟随重定向锁定真实后端，缓存到 `~/.zlib_dl_mirror`
- **质询本地破解** — 解析质询页的混淆 JS，本地穷举 SHA1 工作量证明（约 6.5 万次尝试，毫秒级），503 反复出现自动重试
- **配额硬闸** — 无凭据时 `download` 直接拒绝并打印配置指引，零网络请求；`--guest` 显式放行
- **一次一请求** — 每次下载恰好发一次请求，服务端返回网页（配额用尽或会话失效）就停下报告
- **下载即校验** — PDF 验 `%PDF` 头加 `%%EOF` 尾，epub 验 `PK\x03\x04`，mobi/azw3 验偏移 60 处的 `BOOKMOBI`
- **零依赖** — 仅 Python 标准库，3.10+ 即可

### 安装

```bash
npx skills add https://github.com/aasaa444/zlib-dl
```

或把仓库克隆到 Agent 的技能发现目录，再配好 cookie（见下）。

### 配置

登录任意 Z 站镜像，浏览器 F12 打开开发者工具，在应用/存储里找到 Cookie，复制 `remix_userid` 和 `remix_userkey` 两个值：

```powershell
setx ZLIB_REMIX_USERID <数字id>
setx ZLIB_REMIX_USERKEY <userkey>
```

bash 用 `export` 并写进 `.bashrc`。跑一次 `probe`，看到 `cookies: logged-in` 即配置完成。凭据只走环境变量，不落文件、不进日志。

### 使用

**作为 Agent Skill（推荐）**，配好 cookie 后直接说：

> 用 zlib-dl 帮我下载《信号与噪声》的 pdf

Agent 会自己探测镜像、搜书、把可用版本列出来让你挑，确认后才下载。

**手动 CLI**：

```bash
python scripts/zlib_dl.py probe                                 # 发现并验证镜像（免费）
python scripts/zlib_dl.py search "书名" --ext pdf --lang 中文   # 搜书（免费）
python scripts/zlib_dl.py download "/dl/<令牌>" --name 书名     # 下载（消耗配额）
python scripts/zlib_dl.py verify 书名.pdf                       # 完整性校验
```

**实际输出**：

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

没配 cookie 就下载，配额闸会拦住：

```text
$ python scripts/zlib_dl.py download "/dl/gmePQdPbXa" --name test
refusing to download in guest mode: the anonymous quota is 1 download/day
and is consumed even if the transfer later fails. Configure your Z-Library
account instead (recommended):
  ...
```

### 工作流程

```text
"帮我下载《信号与噪声》pdf"
        ↓
probe：GitHub 镜像表 → 可达后端
        ↓
search：版本按 格式 / 大小 / 评分 列出，附 /dl/ 令牌
        ↓
你确认要哪一条（默认 PDF）
        ↓
download：GET /dl/<令牌>，恰好一次请求
        ↓
verify：魔数 + EOF ✅
```

### 配额与数据边界

| 身份 | 每日下载 | 说明 |
|---|---|---|
| 游客 | 1 次 | 失败也占额，`--guest` 显式放行 |
| 免费注册账号 | 10 次 | 推荐，两个 cookie 即登录态 |

- `probe` 和 `search` 免费，随便跑
- 脚本只与两方通信：GitHub（读镜像表）和 Z 站镜像，搜索词会经过这两方
- 凭据只走环境变量（`ZLIB_REMIX_USERID` / `ZLIB_REMIX_USERKEY`，另有整串 `ZLIB_COOKIE` 和固定镜像 `ZLIB_MIRROR` 可选），不落文件、不进日志
- 兼容范围：国内裸网络（无代理、Windows 10）全流程实测；Linux/macOS 代码路径相同，未实测

### 贡献与许可

欢迎 Issue 和 PR，两条底线：仅用标准库，配额纪律的默认行为不被削弱。[MIT](./LICENSE) © aasaa444

---

<div align="center">

## English

</div>

**For personal study, research, and technical demonstration only. Follow your local laws, respect copyright, and use it only with resources you are legally allowed to access, public-domain or openly licensed documents, or content you own. No liability, use at your own risk.**

### Why this exists

From a censored network, poisoned domains, rotating mirrors, and the site's SHA-1 anti-bot gate are all things the script handles on its own. The hard part is quota: 1 download a day for guests, 10 for a free account, burned even on failure. So the whole skill follows one rule — searching is free, downloading is restrained: PDF by default, confirm before spending, verify after, never retry blindly.

### Features

- **Automatic mirror discovery** — reads the latest working mirrors from the [Awesome-Zlibrary](https://github.com/dongyubin/Awesome-Zlibrary) repo, follows redirects to the real backend, caches in `~/.zlib_dl_mirror`
- **Local gate solving** — parses the obfuscated challenge page and brute-forces the SHA-1 proof of work locally (~65k attempts, milliseconds); repeated 503s are retried automatically
- **Quota gate** — without credentials, `download` refuses and prints setup instructions with zero network requests; `--guest` overrides explicitly
- **One request per download** — an HTML response means quota gone or session invalid, and the script stops instead of retrying
- **Instant integrity checks** — `%PDF` header plus `%%EOF` tail, `PK\x03\x04` for epub, `BOOKMOBI` at offset 60 for mobi/azw3
- **Zero dependencies** — Python standard library only, 3.10+

### Install

```bash
npx skills add https://github.com/aasaa444/zlib-dl
```

Or clone the repo into your agent's skill discovery directory and set the cookies (below).

### Setup

Log in to any Z-Library mirror, open browser DevTools (F12), find the cookies, and copy `remix_userid` and `remix_userkey`:

```powershell
setx ZLIB_REMIX_USERID <numeric-id>
setx ZLIB_REMIX_USERKEY <userkey>
```

On bash, `export` them and add to `.bashrc`. Run `probe` once — `cookies: logged-in` means you are set. Credentials only travel through environment variables, never files or logs.

### Usage

**As an agent skill (recommended)**, with cookies configured, just say:

> Use zlib-dl to download the PDF of "The Signal and the Noise"

The agent probes a mirror, searches, lists the editions for you to pick, and only then downloads.

**Manual CLI**:

```bash
python scripts/zlib_dl.py probe                                 # find and verify a mirror (free)
python scripts/zlib_dl.py search "title" --ext pdf              # search (free)
python scripts/zlib_dl.py download "/dl/<token>" --name book    # download (uses quota)
python scripts/zlib_dl.py verify book.pdf                       # integrity check
```

**Real output**:

```text
$ python scripts/zlib_dl.py search "信号与噪声" --ext pdf --limit 3
21 result(s):
  1. [PDF ]   21.72 MB  Chinese  2013 rating=0.0 信号与噪声大数据时代预测的科学与艺术
     dl: /dl/gmePQdPbXa    /book/K5npJPpmzV/信号与噪声大数据时代预测的科学与艺术.html
  2. [PDF ]    6.55 MB  Chinese  2013 rating=5.0 信号与噪声大数据时代预测的科学与艺术
     dl: /dl/xXoZRN3Ln6    /book/r9bbapM79B/信号与噪声大数据时代预测的科学与艺术.html
```

Without credentials the quota gate blocks the download and prints instructions instead of burning the guest attempt.

### Workflow

```text
"download this book"
        ↓
probe: GitHub mirror list → reachable backend
        ↓
search: editions with format / size / rating + /dl/ tokens
        ↓
you confirm which one (PDF by default)
        ↓
download: GET /dl/<token>, exactly one request
        ↓
verify: magic bytes + EOF ✅
```

### Quota, data & privacy

| Identity | Downloads/day | Notes |
|---|---|---|
| Guest | 1 | burned even on failure; `--guest` to override |
| Free account | 10 | recommended — two cookies give you login |

- `probe` and `search` are free, run them as much as you like
- The script talks to exactly two parties: GitHub (the mirror list) and the Z-Library mirror; search terms pass through both
- Credentials only travel through environment variables (`ZLIB_REMIX_USERID` / `ZLIB_REMIX_USERKEY`, plus optional `ZLIB_COOKIE` and `ZLIB_MIRROR`) — never files, never logs
- Compatibility: fully tested end to end on an unproxied Windows 10 connection in mainland China; Linux/macOS code paths are identical but untested

### Contributing & license

Issues and PRs welcome. Two baselines: standard library only, and the default quota-discipline behavior intact. [MIT](./LICENSE) © aasaa444
