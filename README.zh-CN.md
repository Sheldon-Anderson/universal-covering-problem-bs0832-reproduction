# Lebesgue 万有覆盖问题 - 认证下界证书

本仓库包含一个有限证书（finite certificate）和一套 Python 验证程序，用于在凸 Brass-Sharifi 三测试集下界框架中验证阈值

$$
\tau = 0.83201.
$$

验证通过后得到的凸版本结论是

$$
\alpha_{\mathrm{cvx}} \ge 0.83201.
$$

本仓库已经包含验证所需的证书数据，位于 `certificate/final_chain/`。不需要额外下载证书归档。

## 目录

- [背景：Lebesgue 万有覆盖问题是什么](#1-背景lebesgue-万有覆盖问题是什么)
- [这个仓库验证什么](#2-这个仓库验证什么)
- [术语表](#3-术语表)
- [证明思路](#4-证明思路)
- [这个仓库包含哪些内容](#5-这个仓库包含哪些内容)
- [快速开始](#6-快速开始)
- [安装](#7-安装)
- [主证书验证](#8-主证书验证)
- [检查公开仓库](#9-检查公开仓库)
- [完整证书链 replay](#10-完整证书链-replay)
- [高级组件 replay 命令](#11-高级组件-replay-命令)
- [输出文件怎么看](#12-输出文件怎么看)
- [SHA256 策略](#13-sha256-策略)
- [故障排除](#14-故障排除)
- [常见问题](#15-常见问题)
- [论文、引用和许可](#16-论文引用和许可)

## 1. 背景：Lebesgue 万有覆盖问题是什么

Lebesgue 万有覆盖问题研究：平面中面积尽可能小的集合，是否能包含每一个直径为 1 的平面集合的一个全等副本。

本文档只讨论凸版本。也就是说，覆盖集合 $K$ 要求是凸集。记凸万有覆盖集合类为 $\mathcal{U}_{\mathrm{cvx}}$，并定义

$$
\alpha_{\mathrm{cvx}}
=
\inf_{K\in\mathcal{U}_{\mathrm{cvx}}}\mathrm{area}(K).
$$

本仓库验证的是 $\alpha_{\mathrm{cvx}}\ge0.83201$ 这个凸版本证书结论。

## 2. 这个仓库验证什么

仓库验证的是：在 Brass-Sharifi 的凸三测试集框架中，归一化配置域上的 hull 面积函数满足

$$
A(v)\ge 0.83201
\qquad(v\in\Omega_{\mathrm{adm}}).
$$

这里 $\Omega_{\mathrm{adm}}$ 是容许域（admissible domain），即 Brass-Sharifi 归一化之后的参数域。

本仓库不声称解决非凸版本问题，不声称完成 proof assistant 形式化，也不声称已经完成外部独立验证。

## 3. 术语表

| 术语 | English | 说明 |
|---|---|---|
| 凸万有覆盖集合类 | convex universal cover class | 只讨论凸覆盖集合。 |
| 容许域 | admissible domain | Brass-Sharifi 归一化后的参数域，记为 $\Omega_{\mathrm{adm}}$。 |
| 有限证书 | finite certificate | 由有限个可检查记录组成的证明对象。 |
| 证书验证 | certificate verification | 读取证书数据并检查关键有限条件。 |
| 证书链 replay | certificate-chain replay | 逐层重放四个证书组件的检查。 |
| 逐记录证据 | per-record evidence | 每个局部记录都对应到可检查证据，而不只依赖汇总统计。 |
| witness construction | witness construction | 用内接见证多边形处理 witness domains。 |
| 向外舍入区间算术 | outward-rounded interval arithmetic | 区间端点向外舍入，保证记录的下界是安全下界。 |
| 鞋带公式 | shoelace formula | 用顶点循环顺序计算多边形面积的公式。 |

## 4. 证明思路

### 第一步：从凸万有覆盖集合得到三测试集凸包

若 $K\in\mathcal{U}_{\mathrm{cvx}}$，则 $K$ 包含圆盘 $C$、等边三角形 $T$ 和正五边形 $P_5$ 的全等副本。因为 $K$ 是凸的，所以它包含这三个副本的凸包。

### 第二步：用归一化参数描述凸包面积

归一化配置写成

$$
v=(\rho,x_3,y_3,x_5,y_5),
\qquad
u_3=(x_3,y_3),
\qquad
u_5=(x_5,y_5).
$$

令 $R_\rho$ 表示角度 $\rho$ 的旋转，并定义

$$
X(v)=C\cup(T+u_3)\cup(R_\rho P_5+u_5),
\qquad
H(v)=\mathrm{conv}(X(v)),
\qquad
A(v)=\mathrm{area}(H(v)).
$$

因此，只要能在容许域 $\Omega_{\mathrm{adm}}$ 上证明 $A(v)$ 的统一下界，就能得到凸万有覆盖集合的面积下界。

### 第三步：用有限覆盖把全域问题化为局部检查

证书验证一个有限覆盖族 $\mathcal F$，满足

$$
\Omega_{\mathrm{adm}}\subseteq\bigcup_{B\in\mathcal F}B.
$$

对每个覆盖单元 $B\in\mathcal F$，证书给出局部下界 $L_B$，并验证

$$
A(v)\ge L_B\ge\tau
\qquad(v\in B).
$$

### 第四步：用 witness construction 处理 witness domains

在 witness domains 上，证书给出一组见证点 $Q_B(v)\subseteq X(v)$。于是

$$
W_B(v)=\mathrm{conv}(Q_B(v))\subseteq H(v),
$$

所以 $A(v)\ge\mathrm{area}(W_B(v))$。验证程序再用向外舍入区间算术检查循环顺序和鞋带公式面积下界。

### 第五步：合并所有局部下界

因为每个 $v\in\Omega_{\mathrm{adm}}$ 都落在某个 $B\in\mathcal F$ 中，所以所有局部下界合并后得到

$$
A(v)\ge0.83201
\qquad(v\in\Omega_{\mathrm{adm}}),
$$

进而得到

$$
\alpha_{\mathrm{cvx}}\ge0.83201.
$$

## 5. 这个仓库包含哪些内容

| 路径 | 作用 |
|---|---|
| `certificate/final_chain/` | 四个证书链归档，是主验证的数据输入。 |
| `certificate/manifest/` | 证书归档的 SHA256 清单。 |
| `certificate/public/` | 人类可读的证书状态和声明边界说明。 |
| `ucbs/certificate/` | 读取证书归档并 replay 关键检查的 Python 模块。 |
| `ucbs/verification/` | 仓库发布检查模块，例如 README 数学渲染、claim boundary、hash 检查。 |
| `scripts/` | 公开命令行入口。 |
| `docs/` | 输出说明、复现说明、FAQ 和数据策略。 |
| `paper/` | 编译后的论文预览。 |

四个证书链归档是：

```text
certificate/final_chain/per_record_evidence_feedback.zip
certificate/final_chain/construction_audit_feedback.zip
certificate/final_chain/witness_construction_feedback.zip
certificate/final_chain/final_adjudication_feedback.zip
```

## 6. 快速开始

```bash
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
python scripts/verify_certificate.py --root . --log-level INFO
python scripts/check_repository.py --root . --log-level INFO
```

主证书验证成功后，重点看：

```text
runs/certificate_verification/status/certificate_verification.status.json
runs/certificate_verification/log/certificate_verification.log
```

期望核心字段：

```json
{
  "status": "passed",
  "certificate_verified": true,
  "threshold_proved": true,
  "certified_threshold": "0.83201",
  "failed_component_count": 0
}
```

## 7. 安装

环境要求：

- Python 3.10 或更高版本。
- 依赖见 `requirements.txt`。
- 不需要 GPU。

推荐使用虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
```

Windows PowerShell 中激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

## 8. 主证书验证

命令：

```bash
python scripts/verify_certificate.py --root . --log-level INFO
```

作用：

- 读取 `certificate/final_chain/` 中四个归档。
- replay 逐记录证据、construction audit、witness construction 和 final adjudication 四个组件。
- 输出详细日志、诊断 CSV 和状态 JSON。

输出：

```text
runs/certificate_verification/status/certificate_verification.status.json
runs/certificate_verification/diagnostics/component_checks.csv
runs/certificate_verification/diagnostics/failed_component_checks.csv
runs/certificate_verification/log/certificate_verification.log
runs/certificate_verification/certificate_verification_feedback.zip
```

## 9. 检查公开仓库

命令：

```bash
python scripts/check_repository.py --root . --log-level INFO
```

作用：

- 检查 Python 代码能否编译。
- 检查仓库目录结构和空目录。
- 检查 README 数学公式是否能在 GitHub 上渲染。
- 检查公开叙事和声明边界。
- 检查证书归档 SHA256。
- 内部运行主证书验证。

输出：

```text
runs/repository_check/status/repository_check.status.json
runs/repository_check/diagnostics/failed_checks.csv
runs/repository_check/diagnostics/readme_math.csv
runs/repository_check/diagnostics/narrative_lint.csv
runs/repository_check/diagnostics/claim_boundary.csv
runs/repository_check/diagnostics/artifact_hashes.csv
runs/repository_check/log/repository_check.log
runs/repository_check/repository_check_feedback.zip
```

因为它会内部运行主证书验证，所以也会生成：

```text
runs/certificate_verification/
```

## 10. 完整证书链 replay

命令：

```bash
python scripts/replay_certificate_chain.py --root . --log-level INFO
```

作用：只 replay 四个证书链组件，不检查 README、目录结构或发布文案。

输出：

```text
runs/certificate_chain_replay/status/certificate_chain_replay.status.json
runs/certificate_chain_replay/diagnostics/component_checks.csv
runs/certificate_chain_replay/log/certificate_chain_replay.log
runs/certificate_chain_replay/certificate_chain_replay_feedback.zip
```

期望字段：

```json
{
  "status": "passed",
  "per_record_evidence_passed": true,
  "construction_audit_passed": true,
  "witness_construction_passed": true,
  "final_adjudication_passed": true,
  "failed_component_count": 0
}
```

## 11. 高级组件 replay 命令

这些命令用于单独检查某个证书组件。它们不会替代主证书验证。

### 11.1 逐记录证据

```bash
python scripts/replay_per_record_evidence.py --root . --log-level INFO
```

读取 `per_record_evidence_feedback.zip`，检查 supporting local records 是否有逐记录证据。期望 `status = passed`、`failed_rows = 0`。

### 11.2 Construction audit

```bash
python scripts/replay_construction_audit.py --root . --log-level INFO
```

读取 `construction_audit_feedback.zip`，检查 construction-stage 归档、rounding rows 和 integrity rows。期望 `status = passed`、`construction_audit_passed = true`。

### 11.3 Witness construction

```bash
python scripts/replay_witness_construction.py --root . --log-level INFO
```

读取 `witness_construction_feedback.zip`，检查 witness containment、accepted terminal subdomains、orientation rows 和 shoelace lower bounds。期望 `status = passed`、`witness_construction_passed = true`、`accepted_terminal_subdomains = 140`。

### 11.4 Final adjudication

```bash
python scripts/replay_final_adjudication.py --root . --log-level INFO
```

读取 `final_adjudication_feedback.zip`，检查最终有限证书条件、proof obligations、claim-boundary rows 和 scope flags。期望 `status = passed`、`threshold_proved = true`。

## 12. 输出文件怎么看

| 文件 | 含义 |
|---|---|
| `runs/certificate_verification/status/certificate_verification.status.json` | 主证书验证状态。 |
| `runs/certificate_verification/diagnostics/component_checks.csv` | 四个组件的 replay 摘要。 |
| `runs/repository_check/status/repository_check.status.json` | 仓库发布检查状态。 |
| `runs/repository_check/diagnostics/failed_checks.csv` | 失败项；没有失败时也会有 summary row。 |
| `runs/certificate_chain_replay/status/certificate_chain_replay.status.json` | 仅证书链 replay 的状态。 |

所有诊断 CSV 都会输出表头和 summary row。

## 13. SHA256 策略

SHA256 gate 只覆盖 `certificate/final_chain/` 中的证书归档。这些归档是证书数据。README、论文和 Python 源码由仓库检查与版本控制管理，不进入证书数据 hash gate。

清单文件是：

```text
certificate/manifest/key_artifacts_sha256.txt
```

查看清单：

```bash
cat certificate/manifest/key_artifacts_sha256.txt
```

## 14. 故障排除

### 依赖安装失败

先升级 `pip`：

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 找不到证书归档

确认 `certificate/final_chain/` 中存在四个 zip 文件。

### 主证书验证失败

查看：

```text
runs/certificate_verification/log/certificate_verification.log
runs/certificate_verification/diagnostics/failed_component_checks.csv
```

### 仓库检查失败

查看：

```text
runs/repository_check/diagnostics/failed_checks.csv
runs/repository_check/log/repository_check.log
```

### README 数学公式渲染失败

公开 Markdown 中，行内公式使用 `$...$`，块级公式使用 `$$...$$`。仓库检查会拒绝 `\(...\)` 和 `\[...\]`。

## 15. 常见问题

### 仓库是否已经包含全部证书数据？

是。四个必要归档都在 `certificate/final_chain/`。

### 这个结论是否解决非凸版本问题？

不是。本仓库验证的是凸 Brass-Sharifi 三测试集框架中的证书结论。

### 这是 proof assistant 形式化吗？

不是。本仓库提供有限证书和 Python replay 检查，不声称 Lean、Coq、Isabelle 等形式化完成。

### 为什么 witness-domain 的局部面积下界大于 0.83201？

这个数值只对应 witness domains。全局阈值需要把整个有限覆盖中的所有局部记录一起考虑。

## 16. 论文、引用和许可

编译后的论文预览在 `paper/`。

引用信息见 `CITATION.cff`。

本仓库采用 MIT 许可，详见 `LICENSE`。
