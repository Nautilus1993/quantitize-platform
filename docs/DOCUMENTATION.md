# 文档分层与维护规则

本项目把文档分成稳定说明、当前状态和不可变证据。目标是让事实只有一个维护位置，同时避免每次变更都重新阅读全部文档。

## 三类资料

| 类型 | 内容 | 更新时机 |
|---|---|---|
| 稳定说明 | 架构、概念、操作流程、安全边界和恢复方法 | 对应行为或流程改变时 |
| 当前状态 | 当前主机、版本、服务、性能、备份和网络观察值 | 重新验证或状态发生变化时 |
| 不可变证据 | 某次性能测试、备份校验和验收记录 | 每次新增记录；已有记录不改写 |

稳定说明包括 `README.md`、`HANDOFF.md`、`AGENT_GUIDE.md`、`agent/RUNBOOK.md`、`reference/` 和 `rebuild/`。当前状态唯一来源是 `status/platform.json`，`status/CURRENT.md` 由它生成。历史证据放在 `evidence/<domain>/<date-or-id>/`。

## 引用规则

- 稳定文档不复制驱动版本、镜像 ID、最新快照、服务健康状态和性能数字，只链接 `status/CURRENT.md`。
- `platform.json` 的每个领域都有独立 `verified_at`；没有重新验证的领域不得顺带刷新日期。
- 证据文件记录一次已经发生的验收。后续测试新增文件，不覆盖旧报告。
- 当前状态可指向证据；证据不能反向声称自己仍是“当前状态”。
- Git 历史用于追溯被替换的说明，不在当前目录维护迁移流水账。

## 按影响范围更新

Agent先运行`python tools/doc_impact.py --base <base>`（或直接查看`git diff --name-only <base>`），再按下表读取和更新，不做全文语义扫描：

| 变更路径或事件 | 必读 | 可能更新的状态/证据 |
|---|---|---|
| `pipeline/**` | `pipeline/FLOW.md`、性能参考 | `performance`、性能证据 |
| `apps/api/**` | API 相关 Runbook | `production`、`runtime` |
| `deploy/**` | `deploy/README.md`、恢复手册 | `production`、`runtime`、`hardware` |
| `rebuild/**` | 重建指南 | 新的重建或 runtime 证据 |
| 服务器、GPU或网络变化 | `agent/RUNBOOK.md` | `production`、`hardware`、`network` |
| NAS备份或恢复 | `reference/RECOVERY.md` | `storage`、新的备份证据 |
| 仅文字或格式变化 | 被修改文档 | 通常不更新状态 |

状态字段没有变化时不要为了“有改动”而修改它；需要说明已复核但值未变时，只更新对应领域的 `verified_at`，并保留验证证据。

## Agent 写入流程

1. 读取 `agent/CONTEXT.md`，确定稳定说明、当前状态和任务专用资料。
2. 用 Git diff 和上表确定影响领域。
3. 从主机、任务或备份重新采集事实，不用旧文档推断当前值。
4. 新增不可变证据，再更新 `status/platform.json` 中受影响的字段和 `verified_at`。
5. 运行 `python tools/update_docs.py` 生成 `status/CURRENT.md`。
6. 运行 `python tools/update_docs.py --check`、Markdown 链接检查、敏感信息检查和相关测试。
7. 在交付说明中列出已更新领域、未重新验证领域和证据路径。

`CURRENT.md` 带有生成标记，禁止手工编辑。若只是实时排障且没有形成经过验收的新基线，不要把瞬时 GPU 利用率、临时故障或运行中任务写入状态文件。
