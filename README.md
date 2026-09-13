<div align="center">

# 📥 zlib-dl

[简体中文](#-简体中文) | [English](#-english)

</div>

> 从 Z-Library（Z站）搜索并下载电子书的 Agent Skill。镜像发现、反爬质询、配额纪律，全部自动化。

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Dependencies](https://img.shields.io/badge/dependencies-stdlib%20only-brightgreen)](scripts/zlib_dl.py)
[![Agent Skill](https://img.shields.io/badge/Agent-Skill-success)](SKILL.md)

---

## ⚠️ 简体中文

**本项目仅供个人学习、研究与技术演示。请严格遵守所在地区法律法规与版权条款，仅用于：**

- ✅ 你有合法权限访问的资源
- ✅ 公版或开放许可的文档（如古登堡计划、arXiv）
- ✅ 你本人拥有或获授权的内容

**作者不鼓励任何形式的版权侵权，不承担相关法律责任，使用风险自负。请尊重知识产权，支持正版！**

---

### ✨ 特性

- 🔍 **镜像自动发现** — 从 GitHub 的 [Awesome-Zlibrary](https://github.com/dongyubin/Awesome-Zlibrary) 仓库读最新可用镜像，跟随重定向锁定真实后端，DNS 污染、域名轮换都不用管
- 🧩 **质询自动破解** — 站点的 SHA1 反爬质询在本地穷举求解（约 6.5 万次尝试，毫秒级），503 反复出现也自动重试
- 🪙 **配额纪律** — 无凭据时拒绝下载并打印配置指引（零网络请求）；凭据齐全时每次下载恰好只发一次请求
- 🥇 **默认 PDF** — 下载后自动校验完整性：PDF 校验 `%PDF` 头 + `%%EOF` 尾，epub 校验 `PK\x03\x04`，mobi/azw3 校验偏移 60 处的 `BOOKMOBI`
- 📦 **零依赖** — 仅用 Python 标准库，装个 3.10+ 就能跑
- 🔄 **改版可跟** — 站点结构变了（结果条目换成 `<z-bookcard>` 组件、书页改 SPA）不用慌，[协议文档](references/protocol.md)记了应对方法

### 🎯 作为 Agent Skill 使用（推荐）

**安装**：克隆到 Agent 的技能发现目录，或一行命令：

```bash
npx skills add https://github.com/aasaa444/zlib-dl
```

手动方式：

```bash
git clone https://github.com/aasaa444/zlib-dl.git ~/.agents/skills/zlib-dl   # 路径按你的宿主调整
```

**使用**：配好 cookie 后，直接对 Agent 说：

```text
用 zlib-dl 帮我下载《信号与噪声》的 pdf
```

Agent 会自动完成：

- ✅ 探测可达镜像（免费）
- ✅ 搜索并列出可用版本和格式（免费）
- ✅ 向你确认要哪一条（配额纪律）
- ✅ 下载并校验文件完整性

### 🔧 配置（一次性）

登录任意 Z 站镜像，从浏览器开发者工具的 cookie 里取 `remix_userid` 和 `remix_userkey`：

```powershell
setx ZLIB_REMIX_USERID <数字id>
setx ZLIB_REMIX_USERKEY <userkey>
```

| 变量 | 必要性 | 说明 |
|---|---|---|
| `ZLIB_REMIX_USERID` | 登录必需 | 账号数字 id（cookie `remix_userid`） |
| `ZLIB_REMIX_USERKEY` | 登录必需 | 会话密钥（cookie `remix_userkey`） |
| `ZLIB_COOKIE` | 可选 | 整串 cookie，优先级更高 |
| `ZLIB_MIRROR` | 可选 | 固定镜像地址，跳过自动发现 |

凭据只走环境变量，不落文件、不进日志。配好后 `probe` 会显示 `cookies: logged-in`。

### 🛠️ 手动命令行

不想走 Agent 也可以直接用：

```bash
python scripts/zlib_dl.py probe                                 # 发现并验证镜像（免费）
python scripts/zlib_dl.py search "书名" --ext pdf --lang 中文   # 搜书（免费）
python scripts/zlib_dl.py download "/dl/<令牌>" --name 书名     # 下载（消耗配额）
python scripts/zlib_dl.py verify 书名.pdf                       # 完整性校验
```

### 📖 实际输出

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

未配 cookie 就想下载？配额闸会拦住你：

```text
$ python scripts/zlib_dl.py download "/dl/gmePQdPbXa" --name test
refusing to download in guest mode: the anonymous quota is 1 download/day
and is consumed even if the transfer later fails. Configure your Z-Library
account instead (recommended):
  1. Log in at any Z-Library mirror in your browser
  2. DevTools > Application > Cookies > copy `remix_userid` and `remix_userkey`
  ...
```

### 🔄 工作流程

```text
"帮我下载《信号与噪声》pdf"
        ↓
1. probe：GitHub 镜像表 → 可达后端（缓存到 ~/.zlib_dl_mirror）
        ↓
2. search：结果按 格式 / 大小 / 年份 / 评分 列出，附 /dl/ 下载令牌
        ↓
3. 你确认要哪一条（默认 PDF，不浪费配额）
        ↓
4. download：GET /dl/<令牌>，恰好一次请求
   - 返回文件流 → 保存
   - 返回网页 → 配额用尽或会话失效，停下报告
        ↓
5. verify：魔数 + EOF 校验 ✅
```

### 📁 项目结构

```text
zlib-dl/
├── SKILL.md                  # Agent 主流程（技能触发后读这个）
├── README.md                 # 本文件
├── LICENSE                   # MIT
├── scripts/
│   └── zlib_dl.py            # probe / search / download / verify 四个子命令
└── references/
    └── protocol.md           # 质询协议逆向、DNS 污染诊断、站点改版应对
```

### 📊 配额与限制

| 身份 | 每日下载 | 说明 |
|---|---|---|
| 游客 | 1 次 | 失败也占额，`--guest` 显式放行 |
| 免费注册账号 | 10 次 | 推荐，两个 cookie 即登录态 |

- `probe` 和 `search` 不消耗配额，随便跑
- 为什么默认 PDF？配额金贵，PDF 一次就够；epub/mobi/azw3 都在搜索结果里，点名即下
- 脚本只与两方通信：GitHub（读镜像表）和 Z-Library 镜像，搜索词会经过这两方
- 兼容范围：国内裸网络（无代理、Windows 10）全流程实测通过；Linux/macOS 代码路径相同，未实测

### 📝 命令参考

| 命令 | 作用 | 配额 |
|---|---|---|
| `probe` | 发现镜像 → 解质询 → 验证通路，缓存到 `~/.zlib_dl_mirror` | 免费 |
| `search <词> [--ext pdf] [--lang 中文] [--limit 15]` | 搜书，输出格式/大小/令牌 | 免费 |
| `download <令牌或书页> [--out 目录] [--name 名字] [--guest]` | 下载单个文件并校验 | 消耗 1 次 |
| `verify <文件>` | 校验已下载文件的完整性 | 免费 |

## 🤝 贡献

欢迎 Issue 和 PR。改动请保持两条底线：仅用标准库、配额纪律的默认行为不被削弱。

## 📄 许可

[MIT](./LICENSE) © aasaa444

---

<div align="center">

# 📥 zlib-dl

## 🌐 English

</div>

> An Agent Skill to search and download ebooks from Z-Library. Mirror discovery, anti-bot gate solving, and quota discipline — all automated.

**This project is for personal study, research, and technical demonstration only. Comply with the laws of your jurisdiction and respect copyright. Use only with:**

- ✅ Resources you have legal access to
- ✅ Public domain or openly licensed documents (e.g., Project Gutenberg, arXiv)
- ✅ Content you own or are authorized to use

**The author does not encourage copyright infringement in any form and assumes no liability. Use at your own risk. Support official releases!**

### ✨ Features

- 🔍 **Automatic mirror discovery** — reads the latest working mirrors from the [Awesome-Zlibrary](https://github.com/dongyubin/Awesome-Zlibrary) GitHub repo and follows redirects to the real backend; DNS poisoning and domain rotation are handled for you
- 🧩 **PoW-gate solving** — the site's SHA-1 proof-of-work challenge is solved locally (~65k hash attempts, milliseconds) and 503s are retried automatically
- 🪙 **Quota discipline** — without credentials, `download` refuses and prints setup instructions (zero network requests); with credentials, each download sends exactly one request
- 🥇 **PDF by default** — integrity checks after every download: `%PDF` header + `%%EOF` tail for PDF, `PK\x03\x04` for epub, `BOOKMOBI` at offset 60 for mobi/azw3
- 📦 **Zero dependencies** — Python standard library only, 3.10+ is all you need
- 🔄 **Redesign-resilient** — when the site changes (results became `<z-bookcard>` components, book pages became SPAs), the [protocol notes](references/protocol.md) document what to do

### 🎯 Use as an Agent Skill (Recommended)

**Install** — clone into your agent's skill discovery directory, or:

```bash
npx skills add https://github.com/aasaa444/zlib-dl
```

**Use** — with cookies configured, just tell your agent:

```text
Use zlib-dl to download the PDF of "The Signal and the Noise"
```

The agent will:

- ✅ Probe a reachable mirror (free)
- ✅ Search and list available editions and formats (free)
- ✅ Confirm which one you want (quota discipline)
- ✅ Download and verify integrity

### 🔧 Setup (one-time)

Log in to any Z-Library mirror, open browser DevTools, and copy `remix_userid` and `remix_userkey` from the cookies into environment variables (see the table above). Credentials only travel through environment variables — never written to files or logs. `probe` should print `cookies: logged-in` when done.

### 🛠️ Manual CLI

```bash
python scripts/zlib_dl.py probe                                 # find and verify a mirror (free)
python scripts/zlib_dl.py search "title" --ext pdf              # search (free)
python scripts/zlib_dl.py download "/dl/<token>" --name book    # download (uses quota)
python scripts/zlib_dl.py verify book.pdf                       # integrity check
```

### 📖 Real output

```text
$ python scripts/zlib_dl.py search "信号与噪声" --ext pdf --limit 3
21 result(s):
  1. [PDF ]   21.72 MB  Chinese  2013 rating=0.0 信号与噪声大数据时代预测的科学与艺术
     dl: /dl/gmePQdPbXa    /book/K5npJPpmzV/信号与噪声大数据时代预测的科学与艺术.html
  2. [PDF ]    6.55 MB  Chinese  2013 rating=5.0 信号与噪声大数据时代预测的科学与艺术
     dl: /dl/xXoZRN3Ln6    /book/r9bbapM79B/信号与噪声大数据时代预测的科学与艺术.html
```

Without credentials, the quota gate blocks downloads and prints instructions instead of burning the guest attempt.

### 🔄 Workflow

```text
"download this book"
        ↓
1. probe: GitHub mirror list → reachable backend (cached in ~/.zlib_dl_mirror)
        ↓
2. search: results with format / size / year / rating + /dl/ tokens
        ↓
3. you confirm which one (PDF by default, quota intact)
        ↓
4. download: GET /dl/<token>, exactly one request
   - file stream → saved
   - web page → quota gone or session invalid, stop and report
        ↓
5. verify: magic bytes + EOF ✅
```

### 📊 Quota and limits

| Identity | Downloads/day | Notes |
|---|---|---|
| Guest | 1 | burned even on failure; `--guest` to override |
| Free account | 10 | recommended — two cookies give you login |

- `probe` and `search` cost nothing
- The script talks to exactly two parties: GitHub (mirror list) and the Z-Library mirror; search terms pass through both
- Compatibility: fully tested end to end on an unproxied Windows 10 connection in mainland China; Linux/macOS paths are identical but untested

### 🤝 Contributing

Issues and PRs welcome. Please keep two baselines: standard library only, and the default quota-discipline behavior intact.

### 📄 License

[MIT](./LICENSE) © aasaa444
