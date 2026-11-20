# -*- coding: utf-8 -*-
"""deploy.py — 把本地 dist/ 上传到服务器站点目录（SFTP，不依赖 github.com）

用法：
    python tools/deploy.py                 # 全量同步 dist/ -> 服务器
    python tools/deploy.py cognition.html  # 只传指定文件（可多个）
    python tools/deploy.py --dry           # 只看差异，不传

安全设计：
- 上传前把服务器上将被覆盖的文件备份到 _deploy_backup_<时间戳>/
- 凭据从仓库外读取（../ssh_cred.json 或环境变量），永不入库
"""
import os, sys, json, time, stat

try:
    import paramiko
except ImportError:
    sys.exit("缺少 paramiko：pip install paramiko")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_DIST = os.path.join(REPO, "dist")

CANDIDATES = [
    os.path.join(REPO, "..", "ssh_cred.json"),
    os.path.expanduser("~/.igo/ssh_cred.json"),
]


def load_cred():
    if os.environ.get("IGO_SSH_HOST"):
        return {"host": os.environ["IGO_SSH_HOST"],
                "username": os.environ.get("IGO_SSH_USER", "root"),
                "password": os.environ.get("IGO_SSH_PASS", "")}
    for p in CANDIDATES:
        if os.path.exists(p):
            return json.load(open(p, encoding="utf-8"))
    sys.exit("找不到 ssh_cred.json（应在仓库上一级目录）或 IGO_SSH_* 环境变量")


def walk(local_root):
    for root, _dirs, files in os.walk(local_root):
        for f in files:
            lp = os.path.join(root, f)
            rel = os.path.relpath(lp, local_root).replace("\\", "/")
            yield lp, rel


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dry = "--dry" in sys.argv

    cred = load_cred()
    remote_dist = cred.get("remote_dist") or "/opt/projects/finnhub-monitor/dist"

    wanted = set(args) if args else None
    items = [(lp, rel) for lp, rel in walk(LOCAL_DIST)
             if wanted is None or rel in wanted or os.path.basename(rel) in wanted]
    if not items:
        sys.exit("没有匹配到要上传的文件")

    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(cred["host"], username=cred["username"], password=cred["password"],
              timeout=25, look_for_keys=False, allow_agent=False)
    sftp = c.open_sftp()

    ts = time.strftime("%Y%m%d-%H%M%S")
    backup = os.path.join(os.path.dirname(remote_dist), "_deploy_backup_" + ts)

    def ensure(remote_dir):
        parts, cur = remote_dir.strip("/").split("/"), ""
        for p in parts:
            cur += "/" + p
            try:
                sftp.stat(cur)
            except IOError:
                sftp.mkdir(cur)

    def rdir(remote_dir):
        ensure(remote_dir)
        try:
            for a in sftp.listdir_attr(remote_dir):
                if not stat.S_ISDIR(a.st_mode):
                    continue
                rp = remote_dir + "/" + a.filename
                lp_ = os.path.join(backup, a.filename)
                os.makedirs(lp_, exist_ok=True)
                for f2 in sftp.listdir(rp):
                    sftp.get(rp + "/" + f2, os.path.join(lp_, f2))
        except IOError:
            pass

    changed = 0
    for lp, rel in items:
        rp = remote_dist + "/" + rel
        rdir(backup)
        try:
            cur = sftp.stat(rp).st_size
            new = os.path.getsize(lp)
            if cur == new:
                print("SAME  %-28s %8d B (跳过)" % (rel, new))
                continue
            # 备份将被覆盖的旧文件
            bpath = os.path.join(backup, rel.replace("/", "_"))
            ensure(os.path.dirname(bpath))
            sftp.get(rp, bpath)
            print("BACKUP %-27s -> %s" % (rel, os.path.basename(bpath)))
        except IOError:
            print("NEW   %-28s" % rel)

        if dry:
            print("DRY   %-28s 待上传" % rel)
            continue
        ensure(os.path.dirname(rp))
        sftp.put(lp, rp)
        st = sftp.stat(rp)
        ok = "OK" if st.st_size == os.path.getsize(lp) else "SIZE-MISMATCH"
        print("PUT   %-28s %8d B  %s" % (rel, st.st_size, ok))
        changed += 1

    sftp.close()
    c.close()
    print("\n完成：变更 %d 个文件。备份位置：%s" % (changed, backup if changed else "(无需备份)"))


if __name__ == "__main__":
    main()
