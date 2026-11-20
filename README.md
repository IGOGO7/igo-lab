# IGO · 认知与系统演化实验室 —— 站点源码

个人交易认知 / 市场微观结构 / 复杂系统推演的可视化站点。
线上地址：<http://43.139.206.163>（腾讯云 Ubuntu 24.04，nginx 静态托管）

---

## 这个站是怎么构成的

每个页面都是**单文件 HTML**（CSS/JS 全内联，Tailwind 也内联，不依赖外网 CDN）。
好处是国内访问快、不怕 CDN 被墙；代价是单文件 400~520KB。

```
src/X.src.html   ──tools/build_all.py──▶   dist/X.html   ──tools/deploy.py──▶   服务器 dist/  ──▶  nginx
   ↑ 你只需要改这里                            构建产物（线上真实文件）              SFTP 直传
```

## 目录

```
src/    8 个源文件（要改网页就改这里）
dist/   构建产物 = 线上文件（不要手改，改了会被下次构建覆盖）
tools/  build_all.py（构建） deploy.py（上传）
```

## 页面清单

| 源文件 | 产物 | 线上路径 |
|---|---|---|
| src/cognition.src.html | cognition.html | /cognition.html |
| src/portal.src.html | index.html？ | / |
| src/strategy.src.html | strategy.html | /strategy.html |
| src/theory-cinema.src.html | theory-cinema.html | /theory-cinema.html |
| src/theory-tree.src.html | theory-tree.html | /theory-tree.html |
| src/2b-forms.src.html | 2b-forms.html | /2b-forms.html |
| src/igo-2b.src.html | igo-2b.html | /igo-2b.html |
| src/xau-sessions.src.html | xau-sessions.html | /xau-sessions.html |
| （无源文件） | theory-doc.html | /theory-doc.html | 手写遗留页，改动只能直接改 dist |

> 注：`portal.src.html` 与 `index.html` 的对应关系以实际构建产物为准；`theory-doc.html`
> 目前没有 `.src.html` 源，属历史遗留。

## 改网页的流程

1. 改 `src/X.src.html`
2. 构建：`python tools/build_all.py X`（或 `python tools/build_all.py` 全量）
3. 本地浏览器打开 `dist/X.html` 看一眼（可选）
4. 上线：`python tools/deploy.py X.html`（或 `python tools/deploy.py` 全量）
5. 刷新 <http://43.139.206.163/X.html> 验证

`deploy.py` 会把服务器上**将被覆盖的旧文件**先备份到
`/opt/projects/finnhub-monitor/_deploy_backup_<时间戳>/`，传完还会比对字节数。

## 环境须知（重要）

- **github.com 在本机与服务器都不通**（TCP 443 超时），只有 `api.github.com` 通。
  所以：`git push` 必须挂代理（`http://127.0.0.1:10810`），服务器上**不要**用 `git pull` 部署。
  部署统一走 `tools/deploy.py`（SFTP），已验证可用。
- 服务器站点根目录：`/opt/projects/finnhub-monitor/dist`
- 服务器上历史备份很多（`dist_nav_*`、`_backup_*`、`dist_old*`），共约 60MB，可择机清理。
- `node_modules` 147MB、React 旧源码 `src_react/`（原 `src/`）与当前静态页无构建关系，
  不要试图用 `vite build` 重建这些页面——它们不是 React 产物。
- 凭据放在**仓库外**：`../ssh_cred.json`（或环境变量 `IGO_SSH_HOST/USER/PASS`）。**不要提交进来。**

## 一次性的仓库初始化（已完成则跳过）

```bash
git init
git add .
git commit -m "chore: 站点源码入库（8 页源文件 + 构建与部署脚本）"
```
