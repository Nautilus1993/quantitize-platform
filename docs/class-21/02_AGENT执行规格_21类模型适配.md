# Agent Execution Spec — Quantitize Platform 21-Class Adaptation

```yaml
document_status: PLAN_ONLY
created: 2026-09-03
execution_authorized: false
code_changes_authorized: false
tests_authorized: false
production_mutation_authorized: false
```

本文件用于后续 Agent 接手实施。当前不得按本计划执行任何修改、导出、量化、测试、服务重启或 FPGA 写入；只有用户明确授权相应阶段后才执行。

## 1. Objective

使 Quantitize Platform 同时安全支持：

- 旧 checkpoint：YOLOv8x-Pose-P6，`nc=2`，`kpt_shape=[2,3]`；
- 新 checkpoint：同拓扑，`nc=21`，`kpt_shape=[2,3]`；
- 软件 NMS/指标、INT8 `.bin`、FPGA/host 后处理对有效类别数和类别顺序有同一解释；
- 旧 2 类 golden task 不退化。

## 2. Mandatory operating constraints

1. 开始前完整读取项目根 `AGENTS.md`、`docs/agent/CONTEXT.md`、`docs/agent/RUNBOOK.md`。
2. H200 只能 `ssh H200` 直连；它是共享服务器。不得停止其他用户进程，不得修改全局 Docker/驱动/内核/APT。
3. 每次涉及 GPU 前重新检查利用率、显存、计算进程、进程用户和连续采样；历史状态无效。
4. 容器只暴露获授权的单卡 UUID；物理 GPU 3 在容器中通常是逻辑 GPU 0。
5. 未获授权时只允许本地/远端只读检查。服务重启、完整模型运行、量化、生成任务和 FPGA 操作分别需要明确授权。
6. 不加载不可信 `.pt` 到常驻 API 进程。checkpoint 检查必须在无网络、无 GPU、只读根文件系统、资源限额明确的短生命周期容器/进程中进行。
7. 不触碰工作树中已有的用户改动；修改前保存 `git status --short` 和目标文件 diff。
8. 禁止 `docker compose down -v`，禁止宽泛递归删除，禁止清理历史任务现场。

## 3. Frozen evidence

```yaml
old_checkpoint:
  path_local: <local-data-root>\model.pt
  bytes: 199005770
  sha256: DF30B9FBC1CB5EB48E9EFADB53B2DFA6E52375255625438F8DC68EE27CC5C8E0
  ultralytics: 8.3.98
  task: pose
  model_class: ultralytics.nn.tasks.PoseModel
  yaml_file: yolov8x-pose-p6.yaml
  nc: 2
  names: {0: aituosha, 1: moon}
  kpt_shape: [2, 3]
  nl: 4
  reg_max: 16
  head_no: 66
  params: 99169344
  state_numel: 99252199

new_checkpoint:
  path_local: <local-data-root>\weights\best.pt
  bytes: 199053642
  sha256: 94125BE741CC05BB2DF3F6D17D15FB07B182FB74011C2F5AB2669BE1C8F89E2F
  ultralytics: 8.3.98
  task: pose
  model_class: ultralytics.nn.tasks.PoseModel
  yaml_file: yolov8x-pose-p6.yaml
  nc: 21
  kpt_shape: [2, 3]
  nl: 4
  reg_max: 16
  head_no: 85
  params: 99193740
  state_numel: 99276595

proven_shape_delta:
  - pattern: model.30.cv3.{0,1,2,3}.2.weight
    old: [2, 320, 1, 1]
    new: [21, 320, 1, 1]
  - pattern: model.30.cv3.{0,1,2,3}.2.bias
    old: [2]
    new: [21]
  - unchanged: model.30.cv2.* box heads, model.30.cv4.* pose heads, backbone, neck
```

Canonical new class map:

```yaml
0: agaier
1: aipuha
2: aituosha
3: ansainusa
4: aoerhong
5: chapala
6: dibulong
7: didikaka
8: kanjialu
9: lupate
10: qinghai
11: rineiwa
12: sading
13: saersaer
14: saleikamei
15: taihu
16: taiwan
17: tana
18: tekesi
19: wennibeige
20: moon
```

Never reorder this map. Old `aituosha=0/moon=1` is incompatible with new `aituosha=2/moon=20`.

## 4. Desired contract

Create one versioned contract used by API, runner, reports, binary packer, FPGA host and firmware metadata.

Required fields:

```yaml
schema_version: 1
task: pose
nc: 21
class_names: map<int,string> with exact keys 0..20
kpt_shape: [2, 3]
input_size: 1280
strides: [8, 16, 32, 64]
num_candidates: 34000
logical_raw_channels: 91       # 64 DFL + 21 class + 6 pose; verify against ONNX
logical_decoded_channels: 31   # 4 box + 21 class + 6 pose; verify against ONNX
physical_output_channels: 32   # verify FPGA ABI
checkpoint_sha256: string
onnx_sha256: string
weights_sha256: string
bn_sha256: string
abi_version: string
```

Model, selected test dataset and job config must agree on `task/nc/class_names/kpt_shape`. Any mismatch is a hard validation error before GPU work begins.

## 5. Work breakdown

### T00 — Preflight and baseline capture

```yaml
depends_on: []
mutation: none
gpu: none
outputs:
  - preflight record
  - git status and target diff inventory
acceptance:
  - required docs read
  - exact code root and revision recorded
  - existing user changes identified and preserved
```

If later work uses H200, run the read-only baseline in `RUNBOOK.md`. Do not infer current GPU availability from saved documents.

### T01 — Reproducible checkpoint inspector

```yaml
depends_on: [T00]
mutation: code only after authorization
gpu: none
targets:
  - new isolated inspector module/test fixture
acceptance:
  - emits JSON with hash, task, nc, names, kpt_shape, nl, strides and state shapes
  - rejects non-pose or malformed names
  - API never unpickles checkpoint in its own long-lived process
  - inspection has timeout, memory/CPU cap, no network, no GPU and read-only root
```

Do not use `weights_only=True` as a claim that an Ultralytics checkpoint can always be fully inspected; design the isolation boundary as the security control.

### T02 — ONNX interface probe

```yaml
depends_on: [T01]
mutation: generated artifacts only after authorization
gpu: authorized assigned GPU only
inputs: both frozen checkpoints
fixed_export:
  imgsz: 1280
  dynamic: false
  opset: 17
outputs:
  - old/new ONNX graph inventories
  - initializer and value-info shape diff
  - node-name diff
  - final output semantic report
acceptance:
  - four-scale candidate count verified as 34000 or discrepancy explained
  - actual final output width and ordering proven
  - only expected class-head-related graph shapes differ
  - every hardcoded node consumed by bin generation is found exactly once
```

Do not run full quantization in this task. This is a separate, bounded structural probe.

### T03 — Model contract and task creation validation

```yaml
depends_on: [T01]
mutation: platform code
gpu: none for unit/fixture checks
targets:
  - pipeline/runner/_lib/job_config.py
  - pipeline/runner/_lib/validate_input.py
  - pipeline/runner/_lib/shared_datasets.py
  - apps/api/create_task.py
  - apps/api/app.py
  - apps/web/app.py
  - apps/web/templates/new_task.html
acceptance:
  - no main-path fallback to nc=2 or nc=6
  - model/dataset/job mismatch fails before task start
  - class keys must be continuous 0..nc-1
  - web shows inspected task, nc, names and compatibility result
  - ZIP and shared-dataset creation enforce the same rules
  - old 2-class fixture remains valid
```

Do not solve this by adding only a free-form `nc` field. Manual `nc` can be an override only if it must equal inspected model metadata.

### T04 — Input-size contract

```yaml
depends_on: [T02, T03]
mutation: platform code
decision_required: fixed_1280_or_dynamic_abi
recommended: fixed_1280
targets:
  - pipeline/engine/quantitize.py
  - pipeline/runner/_lib/runner_core.py
  - API and web validation
acceptance_fixed_1280:
  - API rejects imgsz != 1280
  - exporter/evaluator/FPGA pack/L43 all record 1280
  - num_candidates asserted as 34000
```

Reason: current `layer_wt_shapes.py` binds L43 to 34,000 candidates, while runner configuration currently appears configurable and exporter still hardcodes 1280.

### T05 — Shared dataset registration and coverage gate

```yaml
depends_on: [T03]
mutation: registry/config after authorization
inputs_required:
  - 21-class calibration dataset
  - 21-class labeled test dataset
  - confirmed preprocessing mode
acceptance:
  - registry nc=21 and exact canonical class map
  - label ids limited to 0..20
  - all 21 classes have explicit image and instance counts
  - zero/low-coverage classes are blocking or require documented waiver
  - calibration/test overlap is zero
  - model preprocessing matches dataset preprocessing
```

Do not reuse the old `aituosha_moon_840` dataset as 21-class acceptance data.

### T06 — Evaluation/report adaptation

```yaml
depends_on: [T03, T05]
mutation: platform code
targets:
  - pipeline/runner/_lib/eval_common.py
  - pipeline/engine/simple_onnx_inference.py
  - apps/api/artifacts.py
  - apps/web/templates/metrics.html
  - pipeline/runner/eval_fpga_results.py
  - pipeline/runner/03_yolo_labels_to_json.py
acceptance:
  - NMS receives contract nc=21
  - per-class P/R/F1 and confusion data cover all 21 ids
  - macro and micro summaries both emitted
  - FPGA matching considers class id, not IoU only
  - keypoint GT/result schema supports both keypoints if pose acceptance is required
  - missing class names do not silently pass as acceptable production output
```

### T07 — Quantization graph robustness

```yaml
depends_on: [T02, T04]
mutation: quantization code
targets:
  - pipeline/engine/quantitize.py
  - pipeline/engine/check_certain_layer_multi.py
  - pipeline/engine/get_conv_name.py
acceptance:
  - graph assertions replace or guard brittle node-name assumptions
  - /model.30 cv2/cv3/cv4 mapping is complete for four scales
  - actual final-output, DFL, sigmoid and pose-decode nodes are unambiguous
  - missing/duplicate required node causes hard failure
  - exclusion list is generated from current ONNX, not stale workspace files
```

Pay attention to cached `*_excluded_nodes.txt`: an existing workspace artifact must not allow a new model to reuse a stale exclusion list.

### T08 — Logical-to-physical weight packing

```yaml
depends_on: [T02, T07]
mutation: bin generation code
targets:
  - pipeline/bin_process/layer_wt_shapes.py
  - pipeline/engine/01_rename_wt_files.py
  - pipeline/engine/02_merge_wt_files.py
  - missing/runtime L43_bin_process.py provenance
expected_mapping:
  class_layers: [L35_s02, L36_s02, L37_s02, L38_s02]
  logical_shape: [21, 320, 1, 1]
  physical_shape: [32, 320, 1, 1]
  pad_output_channels: [21, 31]
acceptance:
  - first 21 channels round-trip equal quantized ONNX initializer bytes after defined layout transform
  - channels 21..31 equal hardware-approved neutral representation
  - bias/scale/zero-point entries follow the same logical/physical mapping
  - source logical out_channels > 32 is a hard error; never truncate
  - metadata records logical_shape, physical_shape and padding
  - merged bin offsets and generated header agree byte-for-byte
  - L43 generator source, version and semantics are in repository/build manifest
```

Static expectation: because physical classification width is already 32, `ALL_WT.bin` size and offsets may remain equal to the 2-class package. Treat this as a hypothesis to test, not an acceptance shortcut.

### T09 — FPGA/host ABI adaptation

```yaml
depends_on: [T02, T08]
owner: FPGA and host software team
mutation: FPGA/host source and interface documents
checks:
  - effective nc=21 versus physical channels=32
  - class argmax/sigmoid loop bound
  - box/class/keypoint offsets
  - output tensor stride and buffer capacity
  - DMA length/burst/alignment
  - class id serialization and exact name table
  - per-class or global confidence threshold behavior
  - ABI version and artifact hash rejection
acceptance:
  - padding channels cannot become detections
  - emitted class_id is always 0..20
  - aituosha is 2 and moon is 20
  - both keypoints decode at the proven offsets
  - firmware/host refuses incompatible ABI or hashes
```

### T10 — Versioned artifact manifest

```yaml
depends_on: [T03, T08, T09]
mutation: bundle/metadata code
targets:
  - bin metadata.json
  - weight_offset_table.h generation
  - fpga_test_pack/config/job_meta.json
  - bundle manifest
required_hashes:
  - checkpoint
  - fp16 ONNX
  - INT8 ONNX
  - ALL_WT.bin
  - ALL_BN.bin
acceptance:
  - all consumers can identify nc, class map, input size, strides, kpt shape and ABI
  - manifest and binary/header offsets are internally consistent
  - old and new packages cannot be accidentally cross-loaded
```

### T11 — Layered validation

```yaml
depends_on: [T05, T06, T07, T08, T09, T10]
mutation: controlled task artifacts
gpu: authorized assigned GPU only
sequence:
  - checkpoint/PT baseline
  - FP16 ONNX parity
  - INT8 ONNX quantization loss
  - layer-bin round trip and L35..L43 probes
  - FPGA versus INT8 ONNX
  - old 2-class golden regression
acceptance_inputs_required:
  - business-approved per-class metric thresholds
  - box IoU tolerance
  - confidence tolerance
  - keypoint pixel/normalized tolerance
  - allowed latency/resource envelope
```

Do not define success after seeing results. Thresholds must be agreed before the acceptance run.

## 6. Required validation matrix

| Case | Model | Dataset metadata | Expected result |
|---|---:|---:|---|
| C01 | nc=21 | nc=21, exact names | create/start allowed |
| C02 | nc=21 | nc=2 | hard fail before GPU |
| C03 | nc=2 | nc=21 | hard fail before GPU |
| C04 | nc=21 | nc=21, reordered names | hard fail |
| C05 | nc=21 | label id 21 or negative | hard fail |
| C06 | nc=21 | one class has zero coverage | fail or explicit approved waiver |
| C07 | nc=21 | imgsz != supported ABI | hard fail |
| C08 | logical class channels 21 | physical capacity 32 | pad 11 channels, no truncation |
| C09 | logical class channels 33 | physical capacity 32 | hard fail, no output package |
| C10 | new bin + old class map/ABI | mismatch | loader rejects |
| C11 | old nc=2 golden task | old matching dataset | unchanged behavior |

## 7. Artifact-level assertions

Checkpoint/ONNX:

- `task == pose`, `nc == 21`, `kpt_shape == [2,3]`, names keys exactly `0..20`.
- Four class terminal convolution initializers have logical shape `[21,320,1,1]`.
- Four box terminal layers remain 64 outputs; four pose terminal layers remain 6 outputs.

Packed weights:

- `L35_s02..L38_s02` physical shape is `[32,320,1,1]` only if FPGA confirms 32-channel ABI.
- Logical channels 0..20 preserve order; physical 21..31 are padding.
- No generic tail truncation is reachable for semantic tensors.
- All offsets are monotonic, non-overlapping and end exactly at binary file size.

Output/postprocess:

- Verify actual ONNX output layout before coding offsets.
- If decoded layout is `[4 box, 21 class, 6 pose]`, width is 31 and pose starts at channel 25.
- If raw layout is `[64 DFL, 21 class, 6 pose]`, width is 91.
- Never iterate padded physical channels as logical classes.

## 8. Stop conditions

Stop and report rather than improvise when any occurs:

- New checkpoint structure differs from frozen evidence or hash changes.
- Dataset class map is unavailable, ambiguous or differs from checkpoint names.
- Training preprocessing cannot be confirmed.
- ONNX final output ordering cannot be proven from graph and a controlled probe.
- `L43_bin_process.py` provenance/behavior cannot be located.
- FPGA physical channel capacity or quantization neutral padding value is unknown.
- A source tensor exceeds static physical shape and existing code would truncate it.
- GPU is not safely available under the shared-server rules.
- Required acceptance thresholds have not been provided before final validation.

## 9. Reporting template

```yaml
task_id: Txx
status: DONE|BLOCKED|FAILED
authorization:
precheck:
  code_revision:
  existing_changes:
  gpu_owner_sampling:
changes: []
commands_or_tools: []
generated_artifacts:
  - path:
    sha256:
verification:
  - assertion:
    result:
evidence:
risks: []
remaining: []
rollback:
```

Every implementation turn must state actual changes, verification performed, remaining work and whether any production/server state changed.
