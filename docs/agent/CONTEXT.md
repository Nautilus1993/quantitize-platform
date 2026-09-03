# Agent 上下文入口

本文件只负责路由，不保存易变化的服务器、镜像、性能或备份数值。

## 资料权威性

| 需要的信息 | 唯一来源 |
|---|---|
| 架构、背景和人工交接 | [`../HANDOFF.md`](../HANDOFF.md) |
| 当前主机、服务、性能、备份和网络状态 | [`../status/platform.json`](../status/platform.json) |
| 当前状态的人类可读版本 | [`../status/CURRENT.md`](../status/CURRENT.md) |
| 操作门禁和命令 | [`RUNBOOK.md`](RUNBOOK.md) |
| 文档影响范围和更新方法 | [`../DOCUMENTATION.md`](../DOCUMENTATION.md) |
| 灾难恢复 | [`../reference/RECOVERY.md`](../reference/RECOVERY.md) |
| 环境重建 | [`../../rebuild/REBUILD_GUIDE.md`](../../rebuild/REBUILD_GUIDE.md) |
| 性能验证方法 | [`../reference/PERFORMANCE.md`](../reference/PERFORMANCE.md) |
| 21类适配计划 | [`../class-21/02_AGENT执行规格_21类模型适配.md`](../class-21/02_AGENT执行规格_21类模型适配.md) |

## 读取原则

1. 每次任务先读取本页和 `platform.json`，但把状态文件视为最近一次验收快照，不视为实时监控。
2. 再读取 `RUNBOOK.md` 中与任务对应的章节。
3. 只在恢复、重建、性能或21类适配等场景读取相应专项资料。
4. 不读取整个 `docs/evidence/`；只读取状态文件或任务明确引用的证据。
5. 执行前重新检查会变化的目标状态，例如GPU占用、服务health、磁盘和NAS挂载。

## 不变的安全边界

- H200使用 `ssh H200` 直连，不使用wrs跳板。
- H200是公用服务器；未经明确授权，不停止其他用户进程，不修改全局Docker、驱动、内核、APT或自动升级策略。
- 不保存或复述SSH、sudo、NAS等明文密码。
- `data/output_data`不进入系统恢复快照；验证NAS归档后才允许清理历史输出。
- 禁止 `docker compose down -v`、删除APT/DPKG lock文件以及使用宽泛通配符递归删除共享数据。
