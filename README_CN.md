# EX-APPAgent

App 自动化运营代理。设定目标，agent 自动采集数据、分析趋势、生成优化方案，你只需审批。

目标：帮每个 App 实现日收入 $20。

## 安装

**Claude Code：**

```bash
claude plugins marketplace add Shameless521/EX-APPAgent
claude plugins install ex-appagent
```

**Codex CLI：**

```bash
codex plugin marketplace add Shameless521/EX-APPAgent
```

开发调试时也可以从本地 clone 安装：

```bash
git clone https://github.com/Shameless521/EX-APPAgent.git
codex plugin marketplace add /path/to/EX-APPAgent
```

然后在 Codex 插件界面安装/启用 `ex-appagent`。

Python 数据引擎对纯分析不是必需的，但自动采集数据时需要安装：

```bash
git clone https://github.com/Shameless521/EX-APPAgent.git
cd EX-APPAgent/engine
uv sync
uv run appagent --version
```

## 使用

到你的 App 项目目录下：

**Claude Code：**

```bash
/appagent                        # 自动分析，agent 决定干什么
/appagent 看看收入趋势            # 指定分析方向
/appagent 竞品最近在干嘛          # 竞品分析
/appagent 这周做了什么            # 周报
```

**Codex CLI：**

安装插件后，进入你的 App 项目目录启动 Codex：

```bash
cd /path/to/your-app
codex
```

在 Codex 里，`/appagent` 是 skill 启动词，不是 Claude Code 那种原生 slash command。你可以输入 `/appagent`，也可以直接自然语言描述：

```text
/appagent
看看收入趋势
竞品最近在干嘛
这周做了什么
```

首次运行会自动引导你完成配置（`program.md`、`.appagent/`、API Key、App 注册等）。

## 复用 Claude Code 旧数据

EX-APPAgent 的运行数据存在你的 App 项目里，不存在 Claude Code 会话里。如果你之前用的是 Claude Code 插件，只要继续使用同一个 App 项目目录即可：

```text
program.md
.appagent/state.json
.appagent/health.json
.appagent/data/metrics/
.appagent/experiments/
.appagent/insights/
```

Codex 会读取同一批文件并接着之前的状态执行。只有旧 Claude Code 对话里的纯聊天上下文不会迁移，除非它已经写入 `.appagent/`。

## 它能干什么

- 自动从 App Store Connect / Google Play 拉取收入、下载量、评论
- 追踪 ASO 关键词排名变化
- 分析竞品公开数据
- 检测数据异常并诊断原因
- 管理 A/B 实验（提出假设 → 观察 → 判定保留/放弃）
- 越用越聪明——agent 会学习自己的数据采集策略
- 预算 ROI 追踪，ROAS 计算与合规检查
- 里程碑自动检测——达成目标时庆祝并解锁新策略
- 能力自扩展——agent 发现能力缺口时自动提议新分析工具

## 你需要做的

1. 填写 `program.md`（目标、竞品、预算等）
2. 定期跑 `/appagent`
3. 审批 agent 生成的方案
4. 执行 AI 做不了的事（提交 App Store、付款等）

## 更新

Skill 层随插件自动更新。数据引擎跑 `/appagent` 时会自动检测新版本并提示升级。

## Google Play 报告

Google Play 收入、下载量、评分来自 Play Console 导出到私有 Google Cloud Storage 的报告 bucket。请在 Play Console > Download reports 复制 bucket，并配置：

```json
{
  "google_play": {
    "service_account_path": "/path/to/service-account.json",
    "reports_bucket": "pubsite_prod_rev_01234567890987654321"
  }
}
```

网络请求支持 `HTTPS_PROXY`、`HTTP_PROXY`、`https_proxy`、`http_proxy` 代理环境变量，并会对 timeout、SSL EOF、429、5xx 等临时错误做退避重试。

## 依赖

- [Claude Code](https://claude.ai/claude-code) 或 [Codex CLI](https://github.com/openai/codex)
- Python 3.12+ / [uv](https://docs.astral.sh/uv/)
- Apple 开发者账号
- Google Play 开发者账号（可选）
