# zlib-dl 协议细节与故障排查

主流程见 SKILL.md；本文件是排障时才需要读的细节层。

## 镜像发现

- 数据源：GitHub 仓库 `dongyubin/Awesome-Zlibrary` 的 README，维护者持续更新各域名「国内是否能访问」标注。
- 抓取走 `https://api.github.com/repos/dongyubin/Awesome-Zlibrary/readme` + 头 `Accept: application/vnd.github.raw`。`raw.githubusercontent.com` 在国内网络时通时断，`api.github.com` 稳定。
- 解析规则：取含 ✅ 的表格行（排除 `~~` 划线删除的行），提取 `https?://…`，跟随 302 得到真实后端（如 `intl.su → zh.laoshihao.ru`）。**后端域名会轮换**，任何硬编码的 laoshihao/1lib 域名都可能过期；缓存文件 `~/.zlib_dl_mirror` 失效时删除重跑 probe 即可。

## DNS 污染诊断

镜像全部连不上（HTTP 000 / 超时）时，先判断是不是 DNS 污染：

1. 本地解析：`nslookup <域名>`；
2. 国内 DoH：`https://dns.alidns.com/resolve?name=<域名>&type=A`。

两者都返回 Facebook 段（173.252.x.x、31.13.x.x 等）或明显无关的 IP，即为污染。此时换域名（重跑 probe），不要尝试直连 IP——SNI 层同样会被阻断。

## 反爬质询（PoW gate）

站点在应用层之前挡了一道「Checking your browser」：HTTP 503 + 混淆 JS。协议已完整逆向：

1. 页面脚本里有一个 3 元素轮转数组（旋转 376 次，376 mod 3 = 1，即左旋一位），解出三个字符串：
   - `challenge`：40 位大写十六进制，每次响应都不同；
   - `c_token`：结果 cookie 名；
   - `array`：SHA1 实现的字节输出方法名。
2. 校验规则：`n1 = parseInt(challenge[0], 16)`（挑战串第一个十六进制字符转数字，0–15，**逐次变化，不可硬编码**）；求最小 `i` 使 `sha1(challenge + str(i))` 的第 `n1` 字节 == `0xB0` 且第 `n1+1` 字节 == `0x0B`（期望尝试 ~65k 次，毫秒级）。
3. 写 cookie 后重发同一请求：`c_token = challenge + i`、`c_time = 任意小数秒`（脚本会检查它存在）。**两个都要**，只发 c_token 会永远 503。
4. 质询会反复出现（大约每次会话多个请求各挡一次），fetch 封装必须带自动 solve→retry 循环（脚本默认 6 次）。503 质询不消耗下载配额——它发生在应用逻辑之前，重试是安全的。

## 配额规则

| 身份 | 每日下载 | 说明 |
|---|---|---|
| 游客 | 1 次 | 失败也占额；换格式重下再扣 |
| 免费注册账号 | 10 次 | `remix_userid` + `remix_userkey` 两个 cookie 即登录态 |

`/dl/<token>` 的两种 200 响应用 Content-Type 区分：

- `application/pdf` / `application/epub+zip` 等 → 真文件，读流保存；
- `text/html`（"Downloading …" SPA 外壳）→ 配额用尽或会话无效。**停止并报告**，不要重试。

下载令牌的来源：搜索结果页的 `<z-bookcard download="/dl/…">` 组件属性（2026-09 起；更早的版本是 `<a download=…>`）。站点改版后书页为 SPA、不再服务端渲染下载按钮，因此 **search 输出的令牌就是下载凭证**，`download "/dl/令牌"` 直接用。令牌绑定会话且可能过期——隔天的令牌失效时重新 search 一次（免费）即可。

## 凭据设置

Windows（持久）：

```powershell
setx ZLIB_REMIX_USERID <数字id>
setx ZLIB_REMIX_USERKEY <userkey>
```

bash（当前会话）：

```bash
export ZLIB_REMIX_USERID=<数字id>
export ZLIB_REMIX_USERKEY=<userkey>
```

登录 Z 站后从浏览器开发者工具的 cookie 里取 `remix_userid` / `remix_userkey`。值只进环境变量：不写入文件、不打印到日志。会话失效（下载总是返回 HTML）时重新取一次 cookie 即可。

脚本在凭据缺失时直接拒绝 `download`（不发网络请求、不占游客配额），打印上面的配置指引；`--guest` 参数是唯一的显式放行通道。

## 已知坑速查

| 症状 | 原因 | 处理 |
|---|---|---|
| probe 全部 unreachable | DNS 污染 / 后端轮换 | 按「DNS 污染诊断」确认；删除 `~/.zlib_dl_mirror` 重跑 probe |
| 每次请求都 503 | c_time cookie 缺失，或 n1 算错 | 检查是否同时写了 c_token 和 c_time；n1 取挑战串首字符 |
| 下载拿到 HTML | 配额用尽 / 未登录 / 令牌过期 | 见「配额规则」；令牌必须从书页现取 |
| 搜索结果为空 | 查询词编码或过滤条件太严 | 脚本已做 URL 编码；去掉 --ext/--lang 再试 |
| GitHub README 拉不到 | api.github.com 偶发不通 | 重试；或手动设 ZLIB_MIRROR |
| Python 依赖 | 无 | 脚本仅用标准库（hashlib/urllib 等），无需安装 |
