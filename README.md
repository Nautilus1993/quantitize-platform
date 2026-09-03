# 量化平台交接文档

这是文档总入口，面向第一次接触模型量化、不了解服务器和网络环境的同事。

## 谁应该读什么

| 读者 | 从哪里开始 | 用途 |
|---|---|---|
| 新接手同事 | [docs/HANDOFF.md](docs/HANDOFF.md) | 理解背景、服务器、网络、存储、平台架构和日常操作 |
| 使用 Agent 的同事 | 先读 HANDOFF，再读 [docs/AGENT_GUIDE.md](docs/AGENT_GUIDE.md) | 学会给 Agent 下达安全、可验证的任务 |
| 自动化 Agent | [AGENTS.md](AGENTS.md) | 获取强制阅读顺序、边界和当前事实来源 |
| 查看当前状态 | [docs/status/CURRENT.md](docs/status/CURRENT.md) | 最近验证的服务、环境、性能、备份和网络状态 |
| 故障恢复人员 | [docs/reference/RECOVERY.md](docs/reference/RECOVERY.md) | H200 重启、系统重装或数据盘丢失后的恢复 |
| 环境重建人员 | [rebuild/REBUILD_GUIDE.md](rebuild/REBUILD_GUIDE.md) | 镜像不可用时从环境包或依赖清单重建 |
| 性能优化人员 | [docs/reference/PERFORMANCE.md](docs/reference/PERFORMANCE.md) | 理解 H200 性能瓶颈和优化路线 |
| 21 类模型适配人员 | [docs/class-21/01_人类阅读_21类模型适配分析与计划.md](docs/class-21/01_人类阅读_21类模型适配分析与计划.md) | 阅读分析结论与实施边界 |

## 推荐阅读顺序

```text
README.md
  └─ docs/HANDOFF.md
       ├─ docs/AGENT_GUIDE.md
       ├─ docs/status/CURRENT.md
       ├─ docs/DOCUMENTATION.md
       ├─ docs/reference/RECOVERY.md
       ├─ docs/reference/PERFORMANCE.md
       └─ rebuild/REBUILD_GUIDE.md

AGENTS.md
  └─ docs/agent/CONTEXT.md
       └─ docs/agent/RUNBOOK.md
```

## 当前有效资料

- `README.md`、`AGENTS.md`、`docs/` 和 `rebuild/` 是当前有效资料。
- 历史迁移资料由 Git 历史以及本机/NAS 归档保存，不进入当前仓库目录。
- 当前仓库是 H200 项目代码的受控镜像；项目内说明用于开发，交接请从本页开始。
- 文档不保存 SSH、sudo 或 NAS 明文密码。

生产入口和最近验收状态以 [docs/status/CURRENT.md](docs/status/CURRENT.md) 为准。
