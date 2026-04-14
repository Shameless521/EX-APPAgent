# phase3-self-improvement

> Phase 3 剩余部分：能力扩展工作流、预算 ROI 追踪、里程碑自动检测。补全 EX-APPAgent 的自我改进系统。

## 📊 进度概览

[░░░░░░░░░░░░░░░░░░░░] **0%** (0/13)

| 状态 | 数量 |
|------|------|
| ✅ 已完成 | 0 |
| 🔄 进行中 | 0 |
| ⏸️ 待开始 | 13 |
| 🚫 阻塞中 | 0 |
| ⏭️ 已跳过 | 0 |

---

## 📋 任务列表

### ⏸️ 1. 实现里程碑自动检测引擎

**优先级:** 🔴 紧急 | **预估:** 1.5h

在 engine/src/appagent_engine/analyzer/ 下新建 milestone.py：(1) 读取 data/metrics/ 最近 N 天的 daily_revenue；(2) 对照 program.md 中的 milestones 配置判断是否连续 3 天达标；(3) 返回 {reached: bool, milestone: str, consecutive_days: int, unlocks: str}。不修改 state.json（由 Skill 层负责）。验收：给定模拟数据，连续 3 天 $1.2/day 能正确检测到 $1 里程碑达成。


### ⏸️ 2. 实现里程碑配置解析器

**优先级:** 🔴 紧急 | **预估:** 1h

在 config.py 中添加 parse_milestones(program_md_path) 函数：从 program.md 解析 milestones 列表，返回 [{target: 1.0, label: '$1/day', unlocks: 'small ad spend'}, ...] 结构。验收：能正确解析 ClipAudio 和 HairMakeover 的 program.md 中的 milestones。


### ⏸️ 3. 集成里程碑检测到 CLI collect

**优先级:** 🔴 紧急 | **预估:** 1h | **依赖:** 1, 2

在 cli.py 的 _collect_one_app 末尾、experiments 之后增加里程碑检测：调用 milestone.check_milestone()，如果达成则输出提示并写入一个标记文件 .appagent/milestone_pending.json（包含 milestone 信息）。Skill 层 harness-loop 在 Step 3 读到此文件后触发 Priority 1。验收：当 metrics 数据连续 3 天达到 $1 时，collect 命令输出里程碑提示。


### ⏸️ 4. 更新 Skill 层里程碑处理逻辑

**优先级:** 🔴 紧急 | **预估:** 1.5h | **依赖:** 3

更新 harness-loop.md Step 3 和 priority-engine.md：(1) Step 3 读取 .appagent/milestone_pending.json，如果存在则标记 milestone_reached；(2) Priority 1 逻辑：展示庆祝信息、显示解锁的策略空间、更新 state.json 的 stage 字段、删除 milestone_pending.json。验收：/appagent 运行时能检测到里程碑并正确触发 Priority 1 流程。


### ⏸️ 5. 实现预算追踪数据模型

**优先级:** 🟠 高 | **预估:** 1h

新建 engine/src/appagent_engine/analyzer/budget.py：(1) 定义 BudgetEntry 数据结构（date, channel, spend, attributed_revenue）；(2) 实现 load_budget_log(appagent_dir) 从 .appagent/data/budget/log.jsonl 读取支出记录；(3) 实现 append_budget_entry() 追加记录（原子写入）。验收：能正确读写预算记录。


### ⏸️ 6. 实现 ROAS 计算与预算校验

**优先级:** 🟠 高 | **预估:** 1.5h | **依赖:** 5

在 budget.py 中添加：(1) calc_roas(entries, days=7) 计算过去 N 天的 ROAS（总归因收入/总支出）；(2) calc_daily_spend(entries, date) 计算单日总支出；(3) check_budget_compliance(entries, daily_limit, min_roas) 返回 {within_limit: bool, current_roas: float, daily_spend: float, warnings: []}。对照 program.md 的 daily_limit 和 min_roas。验收：给定模拟数据，能正确计算 ROAS 并检测超预算。


### ⏸️ 7. 添加预算 CLI 命令

**优先级:** 🟠 高 | **预估:** 1.5h | **依赖:** 6

在 cli.py 中添加 appagent budget 命令组：(1) appagent budget add --channel 'Apple Search Ads' --spend 5.0 --date 2026-04-15 记录支出；(2) appagent budget status 显示 ROAS、日支出、预算合规状态。验收：能通过 CLI 记录支出并查看 ROI 状态。


### ⏸️ 8. 集成预算到 Skill 层分析

**优先级:** 🟠 高 | **预估:** 1h | **依赖:** 7

更新 harness-loop.md：(1) Step 4 之后新增读取 .appagent/data/budget/log.jsonl；(2) 在分析中引用 ROAS 数据；(3) 如果 ROAS < min_roas，在 Step 9 摘要中警告；(4) 如果日支出接近 daily_limit，提醒用户。验收：/appagent 运行时在摘要中展示预算 ROI 信息。


### ⏸️ 9. 实现能力扩展安全检查器

**优先级:** 🟠 高 | **预估:** 2h

在 guardrails.py 中添加 validate_extension_code(code_str) 函数：(1) 静态分析代码字符串，检查 import 列表；(2) 检查是否有 open() 调用写入 .appagent/ 和 engine/ 之外的路径；(3) 检查是否有 requests/httpx/urllib 调用非白名单域名；(4) 检查是否访问敏感路径（~/.ssh 等）；(5) 返回 {safe: bool, violations: []}。验收：包含 open('/etc/passwd') 的代码被标记为不安全。


### ⏸️ 10. 实现扩展加载器和 dry-run 框架

**优先级:** 🟠 高 | **预估:** 2h | **依赖:** 9

新建 engine/src/appagent_engine/extensions/loader.py：(1) list_extensions() 列出 extensions/ 下所有 .py 文件；(2) load_extension(name) 动态导入指定扩展模块；(3) dry_run_extension(name, mock_input) 在沙盒中运行扩展，捕获输出但不写入真实文件（用 mock 替换 writer）；(4) activate_extension(name) 标记为活跃。扩展状态存在 extensions/registry.json。验收：能加载、dry-run、激活一个示例扩展。


### ⏸️ 11. 创建能力扩展 Skill 层工作流

**优先级:** 🟠 高 | **预估:** 1.5h | **依赖:** 10

新建 plugins/ex-appagent/modules/capability-expansion.md：定义完整的能力扩展流程指令，包括 (1) agent 识别能力缺口时如何生成扩展请求（actions/pending/ 格式，含完整代码）；(2) 安全检查展示（调用 guardrails.validate_extension_code）；(3) 用户审批流程；(4) dry-run 执行和结果展示；(5) 激活确认。在 harness-loop Step 8 Priority 5 (Routine) 中引用此模块。验收：Skill 层能按指令完成一次完整的能力扩展流程。


### ⏸️ 12. 创建示例扩展：评论情感分析

**优先级:** 🟡 中 | **预估:** 1.5h | **依赖:** 10

创建 engine/src/appagent_engine/extensions/review_sentiment.py 作为第一个实际扩展：(1) 简单的关键词情感分析（不依赖外部 NLP 库）；(2) 输入：评论列表；(3) 输出：{positive: N, negative: N, neutral: N, top_complaints: [...], top_praises: [...]}；(4) 关键词库涵盖常见 app 评论词汇（crash, bug, love, great 等）。注册到 registry.json。验收：给定 ClipAudio 的评论数据，能输出有意义的情感分析结果。


### ⏸️ 13. 更新 README 并提交

**优先级:** 🟡 中 | **预估:** 0.5h | **依赖:** 4, 8, 11, 12

更新 README.md 和 README_CN.md：Phase 3 状态改为 complete。提交并推送所有改动。验收：git push 成功，README 反映最新状态。


---

*项目 ID: phase3-self-improvement*
*创建时间: 2026/04/15 03:20*
*更新时间: 2026/04/15 03:20*

*此文件由 SuperPlanners 自动生成，请勿手动编辑*