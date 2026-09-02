# Quantitize 可重建环境资料索引

本目录保存 2026-09-01 从 `wrs` 当前可运行环境导出的重建资料。二进制镜像、环境包和业务数据位于 NAS；本机保存声明文件、原始构建文件、固定基础镜像版本和 Agent 操作文档。

## 从哪里开始

Agent 必须先阅读 [REBUILD_GUIDE.md](REBUILD_GUIDE.md)，再根据资产可用性选择：

1. 加载已备份 Docker 镜像：最可靠。
2. 使用 `yolov8_env.tar.gz` 和 pinned Dockerfile 重建：同为 Linux amd64 时可靠。
3. 使用 Conda/Pip 清单从软件源重建：灾难恢复路径，必须重新跑完整验收。

## 目录

```text
rebuild/
├── README.md
├── REBUILD_GUIDE.md
├── rebuild-manifest.yml
├── verify_host.sh
├── verify_runtime.py
├── manifests/
│   ├── source-runtime.json
│   ├── conda-explicit-linux-64.txt
│   ├── environment-full-linux-64.yml
│   ├── environment-from-history.yml
│   ├── pip-list-linux-amd64.lock.txt
│   ├── pip-freeze-raw-linux-amd64.txt
│   ├── requirements.api.lock.txt
│   ├── requirements.web.lock.txt
│   ├── runtime-import-versions.json
│   ├── api-image-dpkg.txt
│   ├── api-image-apt-manual.txt
│   ├── web-image-dpkg.txt
│   ├── web-image-pip.lock.txt
│   └── pipeline-patches-sha256.txt
└── snapshots/
    ├── Dockerfile.api
    ├── Dockerfile.api.pinned-amd64
    ├── Dockerfile.web
    ├── Dockerfile.web.pinned-amd64
    ├── docker-compose.yml
    ├── requirements.api.original.txt
    └── requirements.web.original.txt
```

## 二进制资产位置

```text
\\10.2.26.26\902_data\3-个人\16-王宇航\3-Project\2-DRO\模型量化\quantitize-platform-backup-20260901
```

其中：

- `docker-images.tar.zst`：已验证双镜像。
- `yolov8_env.tar.gz`：已验证 Conda 环境快照。
- `quantitize-platform-code.tar.zst`：代码和部署文件。
- `shared-data.tar.zst`：共享数据。
- `output-data.tar.zst`：历史任务。
- `SHA256SUMS`：完整性基线。

本目录不保存 NAS 密码。
