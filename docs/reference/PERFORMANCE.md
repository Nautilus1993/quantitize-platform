# 性能验证与优化规则

本文只保存可重复使用的方法，不保存“当前最快耗时”等易变化数字。

- 当前性能摘要：[当前状态](../status/CURRENT.md#最近性能基线)
- 当前状态数据源：[`platform.json`](../status/platform.json)
- 2026-09-03 H200 优化验收：[不可变证据](../evidence/performance/2026-09-03-h200-optimization.md)

## 建立可比较基线

性能测试必须固定模型、校准集、测试集、预处理、容器镜像、GPU分配和任务配置。记录代码提交、环境版本、各阶段耗时、最终指标和产物哈希；只比较总耗时不能证明结果等价。

至少执行两次完整任务，区分冷启动和稳态结果。对共享服务器还要记录测试期间GPU冲突、CPU负载和数据盘状态。

## 验收门禁

- 八个阶段均为 `completed`，最终 bundle 存在。
- PT、ONNX和FPGA指标在业务容差内。
- 要求确定性的BIN文件清单、大小和SHA-256与基线一致。
- manifest记录真实阶段耗时和实际provider。
- scratch失败归档和成功清理行为经过验证。
- 单元测试、runner自检、Compose配置和服务health全部通过。

## 更新文档

一次新的有效基线应新增 `docs/evidence/performance/<date>-<name>.md`，不得覆盖旧报告。随后只更新 `docs/status/platform.json` 的 `performance` 字段及其 `verified_at`、`evidence`，再运行：

```bash
python tools/update_docs.py
python tools/update_docs.py --check
```

是否需要更新其他文档由 [`DOCUMENTATION.md`](../DOCUMENTATION.md) 的影响表决定。
