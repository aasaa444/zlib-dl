<div align="center">

# zlib-dl

从 Z-Library（Z站）搜索并下载电子书的 Agent Skill，为国内网络环境设计

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Dependencies](https://img.shields.io/badge/dependencies-stdlib%20only-brightgreen)

[English](./README_EN.md) | 简体中文

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
