# H200 量化平台恢复手册

只在普通重启、服务丢失、系统重装或`/data3`丢失时阅读。当前主机、镜像和快照值先看`../status/platform.json`；本文只保存恢复流程。

## 1. 恢复级别

| 场景 | 需要 NAS | 操作 |
|---|---|---|
| H200 普通重启 | 否 | 检查 Docker/GPU，启动 Compose |
| 容器或镜像丢失，项目仍在 | 可能 | 从快照加载 API/Web 镜像 |
| 项目目录丢失 | 是 | 校验快照，恢复项目和镜像 |
| 系统重装 | 是 | 准备驱动/Docker/Toolkit/CIFS，再恢复项目和镜像 |
| 镜像和环境包都不可用 | 是且需外网 | 按 `../../rebuild/REBUILD_GUIDE.md` Level 3 重建 |

最新已验证快照及证据见[当前状态](../status/CURRENT.md#存储与备份)。

## 2. 普通重启

项目和共享数据在本地 `/data3`，不依赖 NAS 挂载即可启动：

```bash
ssh H200
systemctl is-active docker
nvidia-smi -L
cd /data3/ywang/quantitize-platform
docker compose -f deploy/docker-compose.yml up -d --no-build
docker compose -f deploy/docker-compose.yml ps
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8088/health
```

验收：两个容器 `healthy`，两个 health 成功。若 API 健康但 `/ready` 返回 503，先检查 GPU 资源，不要重建服务。

## 3. 系统重装后的主机门禁

目标必须是 Linux `x86_64`。发行版可以变化，但要准备：

- 支持 H200 和保存镜像中 CUDA 12.8 runtime 的 NVIDIA 驱动。
- Docker Engine、Compose v2。
- NVIDIA Container Toolkit，已配置到 Docker。
- `cifs-utils`、`zstd`、`tar`、`gzip`、`curl`。

验证：

```bash
uname -m
nvidia-smi
docker version
docker compose version
nvidia-ctk --version
docker info | sed -n '/Runtimes/,+2p'
df -h /data3 /var/lib/docker
```

这是公用服务器。不要在恢复过程中顺带修改全局 Docker data-root、内核、驱动或自动升级策略。

## 4. 挂载 NAS

NAS 凭据必须交互输入并保存在 root-only 文件中：

```bash
sudo install -d -m 0700 -o ywang -g ywang /mnt/ywang-nas
sudo install -m 0600 -o root -g root /dev/null /etc/samba/credentials-ywang
sudoedit /etc/samba/credentials-ywang
```

文件格式：

```ini
username=orange
password=<交互输入，不写入文档>
```

挂载：

```bash
sudo mount -t cifs //10.2.26.26/902_data /mnt/ywang-nas \
  -o credentials=/etc/samba/credentials-ywang,vers=3.0,iocharset=utf8,uid=$(id -u ywang),gid=$(id -g ywang),file_mode=0600,dir_mode=0700,nosuid,nodev,noexec
findmnt /mnt/ywang-nas
```

是否配置持久挂载不能从旧文档推断。恢复时检查`findmnt /mnt/ywang-nas`和`/etc/fstab`，当前记录见状态文件的`storage.nas_mount_persistent`。

## 5. 选择并校验快照

只选择 `LATEST.txt` 指向、且状态为 `VERIFIED` 的目录。忽略任何 `.partial` 文件。

```bash
SNAPSHOT_ROOT='<storage.backup_root from docs/status/platform.json>'
SNAPSHOT_NAME='<storage.latest_verified_snapshot from docs/status/platform.json>'
SNAPSHOT="$SNAPSHOT_ROOT/$SNAPSHOT_NAME"
cd "$SNAPSHOT"
sha256sum -c SHA256SUMS
zstd -q -t quantitize-platform-no-output.tar.zst
zstd -q -t docker-images-api-web.tar.zst
gzip -t yolov8_env.tar.gz
find . -name '*.partial' -print
```

任一检查失败都停止恢复，不删除目标机现有数据。

采用快照目录自己的`SHA256SUMS`作为校验权威；该次快照的不可变验收记录由状态文件`storage.evidence`指向。

## 6. 恢复项目与镜像

如果目标目录已经存在，不要覆盖；先确认它是否为需要保留的现场，并选择新的恢复目录或在明确授权后重命名旧目录。

恢复到空目录：

```bash
SNAPSHOT_ROOT='<storage.backup_root from docs/status/platform.json>'
SNAPSHOT_NAME='<storage.latest_verified_snapshot from docs/status/platform.json>'
SNAPSHOT="$SNAPSHOT_ROOT/$SNAPSHOT_NAME"
PROJECT='/data3/ywang/quantitize-platform'

mkdir -p "$PROJECT"
zstd -dc "$SNAPSHOT/quantitize-platform-no-output.tar.zst" \
  | tar -xpf - -C "$PROJECT"
mkdir -p "$PROJECT/data/output_data"

zstd -dc "$SNAPSHOT/docker-images-api-web.tar.zst" | docker load
docker image inspect quantitize-platform-api:latest quantitize-platform-web:latest
```

归档保存的是项目根目录内容，不带额外的 `quantitize-platform/` 外层。系统快照不含 `output_data`，恢复后应创建空目录；历史任务只按明确需求单独恢复。

如果重装后 UID/GID 改变：

```bash
sudo chown -R ywang:ywang /data3/ywang/quantitize-platform
```

## 7. GPU 配置和启动

先查看 GPU UUID 和实时资源：

```bash
nvidia-smi --query-gpu=index,uuid,name,memory.free,utilization.gpu --format=csv
```

`deploy/.env` 必须使用经过协调的 UUID：

```ini
GPU_DEVICE_ID=<获批的 GPU 或 MIG UUID>
GPU_READINESS_REQUIRED=1
GPU_MIN_FREE_MIB=32768
GPU_MAX_UTILIZATION_PERCENT=20
GPU_READY_POLL_SECONDS=30
WEB_DEMO_MODE=0
```

启动：

```bash
cd /data3/ywang/quantitize-platform
docker compose -f deploy/docker-compose.yml config >/tmp/quantitize-compose.resolved.yml
docker compose -f deploy/docker-compose.yml up -d --no-build
docker compose -f deploy/docker-compose.yml ps
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1:8088/health
```

## 8. 运行环境验收

```bash
cd /data3/ywang/quantitize-platform
docker run --rm --gpus all \
  -v "$PWD/rebuild:/rebuild:ro" \
  quantitize-platform-api:latest \
  /home/rs/miniconda3/envs/yolov8/bin/python /rebuild/verify_runtime.py
```

必须看到 CUDA 可用、`sm_90` 和 `CUDAExecutionProvider`。最后在获批 GPU 上运行受控 golden task；只有八步全部完成、error 为空、ZIP 生成且指标满足容差，恢复才算完成。

## 9. 镜像不可用时的优先级

1. 加载已验证 `docker-images-api-web.tar.zst`：最快、最接近原环境。
2. 使用 `yolov8_env.tar.gz` 和 pinned Dockerfile 重建：行为应一致，镜像 ID 不保证一致。
3. 使用 Conda/Pip manifests 联网重建：最后手段，必须完整回归。

具体命令见 `../../rebuild/REBUILD_GUIDE.md`。
