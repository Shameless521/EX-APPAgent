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
git clone https://github.com/Shameless521/EX-APPAgent.git
```

作为 Codex 插件使用时，先把本仓库作为本地插件市场添加：

```bash
codex plugin marketplace add /path/to/EX-APPAgent
```

然后在 Codex 插件界面安装/启用 `ex-appagent`，进入你的 App 项目目录后输入 `/appagent` 或直接描述增长分析需求。

如果不使用插件安装，也可以把 `AGENTS.md` 复制到你的 App 项目根目录：

```bash
cp EX-APPAgent/AGENTS.md /path/to/your-app/AGENTS.md
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

直接用自然语言描述，Codex 会自动读取 `AGENTS.md`：

```
看看收入趋势
竞品最近在干嘛
这周做了什么
```

首次运行会自动引导你完成所有配置（API Key、App 注册等），跟着对话走就行。

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
