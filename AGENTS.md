# Agent Instructions — Quantitize Platform

本文件面向自动化 Agent。不要把历史迁移文档当作当前状态。

## 必读顺序

1. 读取 `docs/agent/CONTEXT.md`，确定资料权威性和任务所需文档。
2. 读取 `docs/status/platform.json` 获取最近验证状态；执行前重新检查会变化的目标资源。
3. 读取 `docs/agent/RUNBOOK.md`，按任务类型选择门禁、命令和验收。
4. 只有在对应场景下再读取：
   - 灾难恢复：`docs/reference/RECOVERY.md`
   - 环境重建：`rebuild/REBUILD_GUIDE.md`
   - 性能优化与验收：`docs/reference/PERFORMANCE.md`
   - 21 类模型适配：`docs/class-21/02_AGENT执行规格_21类模型适配.md`

## 强制边界

- H200 使用 `ssh H200` 直连，禁止配置或使用 `wrs` 跳板。
- H200 是公用服务器。未经明确授权，不停止其他用户进程，不修改全局 Docker、驱动、内核、APT 或自动升级策略。
- GPU 使用前同时检查利用率、显存、进程所有者和持续采样；单次 `0%` 不等于空闲。
- 默认只做只读检查。启动量化、重启服务、挂载 NAS、写备份或删除数据前，确认任务授权覆盖该动作。
- 不在文件、命令参数、日志、Git 或回复中保存/复述明文密码。
- 系统备份明确排除 `data/output_data`。历史输出归档是独立任务，验证 NAS 副本后才允许清理本地。
- 禁止 `docker compose down -v`，禁止删除 APT/DPKG lock 文件，禁止用宽泛通配符递归删除共享盘数据。

## 工作方式

- 开始时报告将检查什么、是否会使用 GPU、是否会修改状态。
- 先收集证据，再给判断；不要从历史文档推断当前 GPU、磁盘或服务状态。
- 变更采用可回滚步骤，大文件先写 `.partial`，校验后再原子改名。
- 每个任务结束时报告：实际变更、验证结果、未完成项和下一步。
- 修改代码、部署、服务器、网络或备份后，按 `docs/DOCUMENTATION.md` 的影响表只检查受影响领域。
- 易变事实只写入 `docs/status/platform.json`；运行 `python tools/update_docs.py` 生成 `CURRENT.md`，禁止手改生成文件。
- 性能和备份验收新增到 `docs/evidence/`，不覆盖旧证据，不把瞬时运行状态写成长期基线。
