---
name: zlib-dl
description: 从 Z-Library（Z站，z-lib / 1lib 镜像）搜索并下载电子书（pdf/epub/mobi/azw3）。自动完成国内网络下的镜像发现（GitHub Awesome-Zlibrary 仓库）、反爬质询破解、账号 cookie 登录（环境变量 ZLIB_REMIX_USERID / ZLIB_REMIX_USERKEY）与文件完整性校验。当用户想下载某本书的电子版、提到 Z站 / z-lib / zlibrary / 电子书 pdf 下载、或给出 z-lib、1lib 链接时使用；下载失败、配额问题、换格式重下也用它。普通文件下载、在线阅读、正版商店购买这类和 Z-Library 无关的请求不要触发本 skill。
---

# zlib-dl — Z-Library 电子书下载

用带登录态的脚本从 Z-Library 镜像下载电子书。核心稀缺资源是**每日下载配额**（游客 1 次/天，免费账号 10 次/天），全流程围绕配额纪律设计：探测和搜书免费，只有 `download` 消耗配额。

## 凭据（环境变量）

| 变量 | 必要性 | 说明 |
|---|---|---|
| `ZLIB_REMIX_USERID` | 登录必需 | 账号数字 id（对应 cookie `remix_userid`） |
| `ZLIB_REMIX_USERKEY` | 登录必需 | 会话密钥（对应 cookie `remix_userkey`） |
| `ZLIB_COOKIE` | 可选 | 整串 cookie，设置时优先于上面两项 |
| `ZLIB_MIRROR` | 可选 | 固定镜像地址（跳过自动发现） |

cookie 值只从环境变量读取：不写入文件、命令行参数或输出。Windows 持久化用 `setx`，bash 用 `export`（示例见 references/protocol.md）。

**用户把 cookie 值直接发给你时，替他们配置**：当前会话先 `export`（Windows 的 Git Bash 同理），再用 `setx` 持久化并提示新终端生效，然后跑 `probe` 验证输出 `cookies: logged-in`。不要把值复述回对话。

**凭据硬闸**：未配置凭据时脚本拒绝执行 `download` 并打印配置指引（不发任何网络请求），显式加 `--guest` 才放行——游客每天只有 1 次下载且失败同样占额，这个闸保证配额不会被不知情地烧掉。guest 放行前仍要先向用户确认目标格式。

## 流程

### 1. 探测镜像（免费）

```bash
python <skill_dir>/scripts/zlib_dl.py probe
```

从 GitHub 仓库 `dongyubin/Awesome-Zlibrary` 的 README（走 `api.github.com`，`raw.githubusercontent.com` 在国内时通时断）解析标记国内可达 ✅ 的域名，跟随重定向得到实际后端，再解一次反爬质询确认通路。镜像域名会轮换，永远以 probe 结果为准。

完成判据：输出至少一个 `[OK]` 镜像。探测结果会缓存到 `~/.zlib_dl_mirror`，后续命令自动复用。

### 2. 搜书（免费）

```bash
python <skill_dir>/scripts/zlib_dl.py search "信号与噪声" [--ext pdf] [--lang 中文] [--limit 15]
```

列出每条结果的格式 / 大小 / 语言 / 年份 / 书名路径。同一本书的每个格式是一条独立结果。

### 3. 确认版本（配额纪律）

把候选清单交给用户，确认要哪一条再下载；用户没有点名格式时默认 PDF。每个 `download` 调用消耗一次配额，同一本书换格式重下 = 再扣一次。

### 4. 下载并校验

```bash
python <skill_dir>/scripts/zlib_dl.py download "/dl/<令牌>" --name "<书名>" --out <目录>
```

target 用 search 输出里的 `dl:` 令牌（搜索结果的 z-bookcard 组件自带新鲜令牌，直接用即可）；也接受 `/book/...` 路径，但书页是 SPA、可能没有服务端渲染的下载按钮，脚本此时会提示改用令牌。请求返回 HTML 说明配额用尽或会话失效——停下来报告，不要反复重试。保存后自动校验完整性：PDF 要求 `%PDF` 头且尾部含 `%%EOF`，epub 要求 `PK\x03\x04`，mobi/azw3 要求偏移 60 处为 `BOOKMOBI`。校验失败即文件损坏，报告实际字节数与类型。

## 故障排查

probe 全挂、503 反复出现、下载总是返回网页等情况，按 [references/protocol.md](references/protocol.md) 处理——内含 DNS 污染诊断、质询协议细节、配额规则与已知的失败模式（域名轮换、令牌过期、缓存失效）。
