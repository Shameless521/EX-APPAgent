# phase4-stabilization

> Phase 4: 引擎稳定化与数据真实性修复。聚焦构建失败、版本不一致、health 状态误报、Google Play 收入/下载采集、评论落盘、daily metrics 字段并入、竞品 Android 信息、网络重试、program.md 解析和过期任务清单校正。

## 📊 进度概览

[████████████████████] **100%** (10/10)

| 状态 | 数量 |
|------|------|
| ✅ 已完成 | 10 |
| 🔄 进行中 | 0 |
| ⏸️ 待开始 | 0 |
| 🚫 阻塞中 | 0 |
| ⏭️ 已跳过 | 0 |

---

## 📋 任务列表

### ✅ 1. 修复 engine/README.md 缺失导致构建失败

**优先级:** 🔴 紧急 | **预估:** 0.25h

engine/pyproject.toml 声明 readme = "README.md"，但 engine/README.md 不存在。创建引擎 README，使 uv build/uv run 可正常构建 editable 包。


### ✅ 2. 统一版本号并重新同步 venv

**优先级:** 🔴 紧急 | **预估:** 0.5h | **依赖:** 1

统一 engine/pyproject.toml、appagent --version、插件 marketplace/plugin 元数据版本为 1.0.0，并运行 uv sync 让 engine/.venv 中的 console script 使用新版本。


### ✅ 3. 修复 health 状态 ok/partial/error 逻辑

**优先级:** 🔴 紧急 | **预估:** 1h

有采集失败时不能在最终 mark_run_success 覆盖为 ok。区分全部成功 ok、部分失败 partial、关键失败 error，并在 CLI health 中正确展示。


### ✅ 4. 实现 Google Play 收入/下载量采集

**优先级:** 🔴 紧急 | **预估:** 3h

补齐 fetch_monthly_report 和 collect_daily_metrics：通过 Google Play Console GCS 报告读取 sales/stats/installs/ratings 数据；无 bucket 或报告缺失时明确标记 unavailable，避免把未知数据伪装成 0。


### ✅ 5. 评论采集写入 .appagent/data/reviews/

**优先级:** 🔴 紧急 | **预估:** 1h

collect reviews 不只打印数量，还要将 iOS/Android 评论按日期落盘并做去重，供后续分析和情感扩展读取历史评论。


### ✅ 6. 将 reviews_new 和 rating 正确并入 daily metrics

**优先级:** 🟠 高 | **预估:** 1h | **依赖:** 4, 5

CLI metrics 采集时把评论、评分/评分数传入 assembler.py，确保 data/metrics/YYYY-MM-DD.json 中 reviews_new、rating、ratings_count 准确反映平台数据。


### ✅ 7. 增强 Android 竞品 Google Play 信息采集

**优先级:** 🟠 高 | **预估:** 1.5h

Google Play 竞品采集不只做页面存在性检查，还要解析名称、开发者、评分、评分数、价格、版本、更新时间、安装量、类别和描述摘要等关键字段。


### ✅ 8. 为 App Store / Google Play 网络错误增加重试与错误分类

**优先级:** 🟠 高 | **预估:** 1.5h

对 timeout、SSL EOF、5xx、429 等临时错误增加指数退避重试；保留代理环境变量支持，并在 README 说明代理和报告 bucket 配置。


### ✅ 9. 加固 program.md 解析

**优先级:** 🟡 中 | **预估:** 1.5h

替换分散的字符串扫描，集中实现结构化 section/key/list 解析器，用于 milestones、watch_list、daily_limit、min_roas 等配置，降低格式微调导致误读的风险。


### ✅ 10. 校正过期任务文档状态

**优先级:** 🟡 中 | **预估:** 1h

更新或移除 phase2/phase3 中与实际源码不一致的 pending 状态，避免任务清单误判当前进度。

---

*项目 ID: phase4-stabilization*
*创建时间: 2026/04/24 00:00*
*更新时间: 2026/04/24 00:00*
