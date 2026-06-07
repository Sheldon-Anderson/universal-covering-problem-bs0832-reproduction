# Brass-Sharifi 0.832 下界的可复现证书包

本仓库给出 Lebesgue 万有覆盖问题**凸版本**中 Brass-Sharifi 0.832 下界的公开复现证书包。这里复现的是已有下界

$$
\alpha_{\mathrm{cvx}} \geq 0.832.
$$

本仓库的定位是 artifact 和 verification package。它不提出新的数值下界，也不声称已经完成 proof assistant 级别的形式化证明或独立外部审查。它所做的是把 Brass-Sharifi 计算辅助证明中的计算部分整理为一个有限、可读取、可重放、可审计的证书对象：源证书包、adaptive ledger、terminal-route replay、三类局部下界证书、紧凑完整性审计，以及最终 proof-obligation / signoff 层。

配套论文 PDF 放在 `paper/` 目录下。

---

## 1. 项目概览

本仓库有两条主线。

第一条是数学逻辑主线：把 Brass-Sharifi 的三测试集摆放问题写成归一化参数空间上的面积函数 $A(v)$，再通过 Branch-B 域覆盖、terminal route 局部证书和有限覆盖命题，推出凸万有覆盖下界。

第二条是复现工程主线：仓库包含 reference certificate artifacts、certificate-artifact SHA256 gate、V106-V109 分阶段 replay 脚本，以及快速最终验证脚本。快速验证检查随仓库发布的 signed-candidate 证书包；完整分阶段 replay 则用于重新生成和审计 V106-V109 的公开链条。

---

## 2. 问题背景：Lebesgue 万有覆盖问题的凸版本

### 2.1 什么是万有覆盖问题？

Lebesgue 万有覆盖问题问的是：平面上是否存在面积尽可能小的集合，使得每一个直径为 1 的平面集合都可以经过刚体运动放入其中。

### 2.2 本仓库只讨论凸版本

本仓库只讨论**凸版本**。也就是说，覆盖集合 $K$ 还要求是凸集。记

$$
\mathcal U_{\mathrm{cvx}}
=
\left\{
K \subset \mathbb R^2:
K \text{ 是凸集，且包含每个直径为 }1\text{ 的平面集合的某个合同副本}
\right\}.
$$

定义

$$
\alpha_{\mathrm{cvx}}
=
\inf_{K\in\mathcal U_{\mathrm{cvx}}}\operatorname{area}(K).
$$

### 2.3 凸版本下界与本项目的关系

Brass 和 Sharifi 证明了凸版本的 0.832 下界。本仓库围绕的正是这个既有下界：不是改进它，而是把其中的计算部分整理为一个可以公开检查的有限证书包。

---

## 3. Brass-Sharifi 的三测试集归一化问题

### 3.1 三个直径为 1 的测试集

Brass-Sharifi 的计算使用三个直径为 1 的测试集：

$$
C = \text{直径为 }1\text{ 的圆盘},
\qquad
T = \text{直径为 }1\text{ 的等边三角形},
\qquad
P_5 = \text{直径为 }1\text{ 的正五边形}.
$$

任意凸万有覆盖 $K$ 必须包含这三个测试集的某些合同副本。由于 $K$ 是凸集，它也必须包含这些副本的凸包。因此，如果能证明这三个测试集在所有允许相对摆放下的凸包面积都至少为 0.832，就能推出 $\operatorname{area}(K)\geq 0.832$，从而得到 $\alpha_{\mathrm{cvx}}\geq 0.832$。

### 3.2 归一化摆放参数

归一化后，圆盘固定在原点，三角形方向固定，只允许平移；正五边形允许旋转和平移。一个归一化摆放由五个参数记录：

$$
v=(\rho,x_3,y_3,x_5,y_5).
$$

记

$$
u_3=(x_3,y_3),
\qquad
u_5=(x_5,y_5).
$$

这里 $u_3$ 是三角形的平移向量，$\rho$ 是正五边形的旋转角，$u_5$ 是正五边形的平移向量。

### 3.3 凸包面积函数

若 $R_\rho$ 表示旋转角为 $\rho$ 的旋转，则定义

$$
H(v)=\operatorname{conv}\left(C\cup(T+u_3)\cup(R_\rho P_5+u_5)\right),
$$

以及

$$
A(v)=\operatorname{area}(H(v)).
$$

证书所对应的摆放层面结论是：对于证书模型中的每一个允许归一化摆放 $v$，都有

$$
A(v)\geq 0.832.
$$

<p align="center">
  <img src="assets/figures/geometry.png" alt="三个 Brass-Sharifi 测试集的归一化摆放" width="45%">
</p>

### 3.4 从摆放下界到凸万有覆盖下界

如果摆放层面下界对所有 admissible normalized placements 成立，那么任意凸万有覆盖 $K$ 的面积也至少为 0.832。原因是 $K$ 包含 $C$、$T$、$P_5$ 的某些合同副本，而凸性保证 $K$ 还包含这些副本的凸包。

---

## 4. 本仓库的目标与非目标

### 4.1 本仓库复现什么？

本仓库的目标是把 Brass-Sharifi 的 0.832 计算整理为可以公开检查的有限证书包，并提供用于检查该证书包的 Python 脚本。

### 4.2 本仓库不声称什么？

本仓库不声称以下内容：

- 不声称得到比 0.832 更强的数值下界；
- 不声称处理非凸版本的万有覆盖问题；
- 不声称已经完成 Lean、Coq、Isabelle 等系统中的形式化证明；
- 不声称已经经过独立外部审查；
- 不声称已经闭合下面所说的 Branch-A 符号化路线。

### 4.3 为什么 `theorem_ready=false` 是预期状态？

最终验证输出中的

```text
theorem_ready = false
```

是预期结果，不是错误。它表示本仓库是一个作者自审的 signed-candidate 证书包，而不是一个已经由 proof assistant 完整验证的定理包。

---

## 5. 本仓库相对于 Brass-Sharifi 原工作的补充

### 5.1 证明组织层面的补充

数学下界本身来自 Brass-Sharifi。这个仓库没有改变下界的数值，也没有替代原论文的数学贡献。它的补充主要在于把计算辅助证明拆成几个明确的逻辑对象：

1. 三测试集摆放问题中的面积函数 $A(v)$；
2. 归一化摆放域的覆盖关系；
3. 每个 terminal route 上的局部下界证书；
4. 从局部证书推出全局摆放下界的有限覆盖命题；
5. 从摆放下界推出凸万有覆盖下界的凸性推论；
6. 明确列出的 proof obligations，即 OB-A 到 OB-F。

### 5.2 编程实践层面的补充

在编程实践和 artifact 组织层面，本仓库补上了：

1. 有限 adaptive parent-child ledger；
2. terminal-route replay 数据；
3. directed interval、local tensor、$h=0.004$ bridge 三类局部证书；
4. 大表的 compact block-hash audit；
5. proof-obligation ledger；
6. 防止越界声称的 proof-boundary audit；
7. final signoff schema 与作者自审 JSON；
8. reference-signed 与 generated-chain 两种验证模式。

### 5.3 与原始 0.832 数值下界的关系

因此，本仓库的贡献不是“发现新的几何不等式”，而是把 Brass-Sharifi 计算组织为一个可以重放、审计和进一步形式化的有限证书对象。数值结论仍然是 Brass-Sharifi 的 0.832 凸下界。

---

## 6. 有限证书是什么意思？

### 6.1 连续问题如何被记录为有限对象

这里的“有限证书”不是说原问题本身变成了有限问题，而是说：用于支持 0.832 下界的连续摆放域，被记录为有限个机器可读取的对象。

### 6.2 adaptive ledger、terminal routes 与 local certificates

具体来说，证书包含：

1. 有限条 parent-child 细分记录；
2. 有限个 terminal route；
3. 有限条 directed interval / tensor / bridge 证书记录；
4. 有限个 row-count 和 block-hash 完整性记录；
5. 有限条 proof obligation；
6. 一个最终 signed-candidate signoff 记录。

### 6.3 verifier 检查什么、不检查什么？

验证程序不重新搜索整个连续空间。它读取这些已经生成的有限记录，检查它们的结构、哈希、局部余量、route 分配和证明边界，然后把这些记录汇总到最终证书结论中。

---

## 7. Branch-A 与 Branch-B 的说明

### 7.1 Branch-A：本仓库不声称闭合的符号化路线

Branch-A 和 Branch-B 是本复现项目内部使用的证书路线标签，不应理解为 Brass-Sharifi 原论文中的术语。

Branch-A 指一种符号化、闭式的 domain-reduction 路线。本仓库不声称这条路线已经闭合。

### 7.2 Branch-B：本仓库采用的扩大域重放路线

Branch-B 指本仓库实际采用的扩大域重放路线。它把需要考虑的 admissible normalized placement domain 放入一个记录好的扩大域 $\Omega_B$，然后用有限个 terminal routes 覆盖这个扩大域。

### 7.3 域包含关系

本仓库所有公开证书结论都走 Branch-B，而不是 Branch-A。证书层面的域关系是

$$
\Omega_{\mathrm{adm}} \subseteq \Omega_B
\subseteq \bigcup_{r\in\mathcal R}\Omega_r.
$$

这里 $\Omega_{\mathrm{adm}}$ 是证书模型中记录的归一化 admissible domain，$\Omega_B$ 是扩大后的 Branch-B replay domain，$\Omega_r$ 是第 $r$ 个 terminal route 所代表的局部区域。

### 7.4 为什么 Branch-B 是保守路线？

采用 Branch-B 是保守的：如果在较大的 $\Omega_B$ 上都能验证 $A(v)\geq 0.832$，那么在其子集 $\Omega_{\mathrm{adm}}$ 上当然也成立。

这个说明很重要。仓库采用的是“记录好的扩大域 + 有限 terminal-route replay”的证书路线，而不是声称独立完成了从原始未归一化摆放空间到 reduced domain 的完整符号化闭合证明。

---

## 8. 局部证书族

### 8.1 统一的 post-guard 接口

对于每个 terminal route $r$，局部验证器记录一个扣除 guard 之后的下界 $L^{\mathrm{post}}_r$，满足

$$
L^{\mathrm{post}}_r \leq \inf_{w\in\Omega_r} A(w),
\qquad
L^{\mathrm{post}}_r - 0.832 \geq 10^{-7}.
$$

因此，对任意 $v\in\Omega_r$，有

$$
A(v)
\geq \inf_{w\in\Omega_r}A(w)
\geq L^{\mathrm{post}}_r
\geq 0.832+10^{-7}
>0.832.
$$

三类局部证书内部机制不同，但进入最终聚合时都通过这个 route-level lower-bound interface。

### 8.2 Directed interval certificates

Directed interval family 是主要的局部证书族。它覆盖 338,367 个 terminal routes，使用 41,261 条 directed rows。扣除 guard 后，它记录的最小余量约为

$$
4.307276422\times 10^{-6}.
$$

### 8.3 Local tensor certificates

Local tensor family 处理 18,380 个 terminal routes。它由 8,751 个 tensor members 和 125 个 tensor packages 支撑。扣除 guard 后，它记录的最小余量约为

$$
2.318262102\times 10^{-5}.
$$

### 8.4 $h=0.004$ bridge

$h=0.004$ bridge 覆盖剩余的 69 个 terminal routes，并使用 282 条 frozen bridge witness rows。在最终聚合中，它作为一个独立 bridge component 处理，而不是被并入 directed interval 或 local tensor family。

### 8.5 三类局部证书如何进入最终聚合

每个 terminal route 都被分配给且只分配给一个局部证书族。只要 route $r$ 的局部记录被接受，最终聚合只需要使用下面的 route-level 结论：

$$
A(v)\geq 0.832,
\qquad v\in\Omega_r.
$$

---

## 9. 证书定理与凸万有覆盖推论

### 9.1 有限覆盖命题

假设有域包含关系

$$
\Omega_{\mathrm{adm}} \subseteq \Omega_B
\subseteq \bigcup_{r\in\mathcal R}\Omega_r,
$$

并且每个 terminal route 上都有局部下界

$$
A(v)\geq 0.832,
\qquad v\in\Omega_r.
$$

那么对所有 admissible normalized placements，都有

$$
A(v)\geq 0.832,
\qquad v\in\Omega_{\mathrm{adm}}.
$$

理由很直接：如果 $v\in\Omega_{\mathrm{adm}}$，那么由包含关系可知 $v\in\Omega_B$，进而 $v$ 落在至少一个 terminal-route domain $\Omega_r$ 中。该 route 对应的局部证书给出 $A(v)\geq 0.832$。

### 9.2 BS0832 certificate theorem

BS0832 certificate theorem 的含义是：在本文和本仓库规定的 verifier / proof-obligation 模型下，证书被接受会提供有限覆盖命题所需的两个输入：

1. Branch-B domain relation；
2. 每个 terminal route 上的 local lower-bound certificate。

因此可以推出摆放层面的结论：

$$
A(v)\geq 0.832
$$

对证书域模型中的所有 admissible normalized placements 成立。

### 9.3 Convex universal-cover consequence

若 $K$ 是凸万有覆盖，则 $K$ 必须包含 $C$、$T$、$P_5$ 的某些合同副本。由于 $K$ 是凸集，它也包含这些副本的凸包。归一化后，该凸包面积就是某个 $A(v)$。因此

$$
\operatorname{area}(K)\geq A(v)\geq 0.832.
$$

对所有凸万有覆盖取下确界，得到

$$
\alpha_{\mathrm{cvx}}\geq 0.832.
$$

### 9.4 逻辑依赖关系

<p align="center">
  <img src="assets/figures/certificate_flow.png" alt="证书结构示意图" width="35%">
</p>

逻辑顺序是：Branch-B domain relation 与 local route certificates 提供有限覆盖命题的输入；certificate theorem 在 verifier 模型下保证这些输入由有限证书给出；最后再由凸性推出 convex universal-cover consequence。

---

## 10. 证书数据与主要计数

### 10.1 adaptive ledger 与 terminal routes

| 组件 | 行数 / 个数 | 作用 |
|---|---:|---|
| Adaptive parent-child ledger | 379,192 | 有限细分树 |
| Adaptive terminal routes | 356,816 | terminal route 闭合 |

### 10.2 三类 route family 的数量

| Route family | Terminal routes |
|---|---:|
| Directed interval certificates | 338,367 |
| Local tensor certificates | 18,380 |
| $h=0.004$ bridge | 69 |
| **合计** | **356,816** |

### 10.3 supporting certificate tables

| Supporting table | 行数 / 个数 |
|---|---:|
| Directed interval rows | 41,261 |
| Local tensor members | 8,751 |
| Local tensor packages | 125 |
| $h=0.004$ bridge witnesses | 282 |

### 10.4 post-guard margin 与接受阈值

| Family | 0.832 之上的最小 post-guard margin |
|---|---:|
| Directed interval | 约 $4.307276422\times 10^{-6}$ |
| Local tensor | 约 $2.318262102\times 10^{-5}$ |
| Verifier acceptance threshold | $10^{-7}$ |

$h=0.004$ bridge 对它负责的 residual route set 通过零违规检查。

---

## 11. V106-V109 阶段标签说明

V106-V109 是本证书包开发历史中继承下来的公开阶段标签，不是数学常数，也不是定理编号。

| Stage | 作用 |
|---|---|
| V106 | Branch-B domain replay 和 final kernel-closure checks |
| V107 | independent replay、release-candidate checks 和 compact block-hash audit |
| V108 | theorem-level reproduction closure attempt 和 proof-obligation binding |
| V109 | final signoff adjudication 和 theorem-ready gate |

---

## 12. 仓库目录结构

```text
universal-cover-bs0832-reproduction/
├── README.md
├── README.zh-CN.md
├── ARTIFACTS.md
├── CERTIFICATE.md
├── EXPECTED_OUTPUTS.md
├── CITATION.cff
├── assets/figures/
├── app/domain/
├── scripts/
├── inputs/
├── certificate/
│   └── intermediate/
└── paper/
```

| 路径 | 作用 |
|---|---|
| `inputs/` | 分阶段复现所需的源证书包。 |
| `certificate/` | 最终 signed-candidate 证书、作者自审 signoff、manifest 和 checksum 文件。 |
| `certificate/intermediate/` | reference-signed 路线使用的 V106-V108 参考反馈包。 |
| `app/domain/` | 证书检查和分阶段 replay 的核心 Python 代码。 |
| `scripts/` | 命令行入口，使用 `python -m scripts.<name>` 运行。 |
| `paper/` | 配套论文 PDF。 |
| `assets/figures/` | README 使用的图。 |
| `runs/` | 脚本运行后生成的本地输出目录，Git 不跟踪。 |

仓库中不包含 `.github/workflows/` 目录。验证以本地命令为准，不依赖 GitHub Actions。

---

## 13. manifest / SHA256 策略

### 13.1 为什么只哈希 certificate artifacts？

`certificate/MANIFEST.json` 和 `certificate/SHA256SUMS.txt` 只描述**证书 artifact**，不再描述整个 GitHub 仓库。这样做的目的很直接：README、论文、图、代码注释和环境说明可以继续改进，而不会改变已经发布的证书数据本身。

### 13.2 哪些文件进入 SHA256 gate

纳入证书哈希检查的是：

```text
inputs/*.zip
certificate/intermediate/*.zip
certificate/feedback_v109_signed_author_self_review.zip
certificate/reviewer_signoff_v109.json
```

### 13.3 哪些文件不进入 SHA256 gate

以下文件不纳入证书 artifact SHA gate：

```text
README.md
README.zh-CN.md
ARTIFACTS.md
CERTIFICATE.md
EXPECTED_OUTPUTS.md
paper/**
assets/**
app/**
scripts/**
requirements.txt
environment.yml
pyproject.toml
CITATION.cff
```

### 13.4 README、论文和源码注释为什么不影响证书哈希？

最终验证脚本仍然要求源证书包、参考中间证书包、最终证书包、signoff JSON、`MANIFEST.json` 和 `SHA256SUMS.txt` 存在，并检查 `MANIFEST.json` 与 `SHA256SUMS.txt` 描述的是同一组证书 artifact。

但 README、论文、图片、Python 注释和环境说明不是证书数据本身。因此这些说明性文件可以继续改进，而不影响证书 artifact 的哈希检查。

---

## 14. 环境安装

### 14.1 使用 pip

命令：

```bash
python -m pip install -r requirements.txt
```

作用：安装 verifier 和 staged replay 脚本所需的 Python 依赖。

预期结果：命令正常退出，随后可以导入 `app/` 和 `scripts/` 下的模块。

### 14.2 使用 conda

命令：

```bash
conda env create -f environment.yml
conda activate bs0832-reproduction
```

作用：根据仓库中的环境文件创建并激活隔离环境。

预期结果：环境创建成功，后续可以在该环境中运行 `python -m scripts...` 命令。

---

## 15. 快速最终验证：`run_final_verification`

### 15.1 命令

```bash
python -m scripts.run_final_verification --root . --log-level INFO
```

### 15.2 作用

该命令检查随仓库发布的 reference certificate artifacts、certificate-only manifest/SHA256 gate、最终 signed-candidate archive，以及结构化的作者自审 signoff。

### 15.3 输出位置

```text
runs/final_verification/final_verification_summary.json
runs/final_verification/final_verification.log
```

### 15.4 关键预期字段

成功运行时，summary JSON 中应包含：

```text
status = success
bs0832_final_repository_verification_passed = true
required_file_count = 14
sha256_checked_file_count = 12
theorem_ready_signed_candidate = true
theorem_ready = false
proof_boundary_violations = 0
```

其中 `theorem_ready=false` 是预期状态，表示仓库保持 signed-candidate certificate package 的边界，而不是声称已经完成 proof-assistant formalization。

---

## 16. 完整分阶段复现：`run_all_stages`

### 16.1 命令

```bash
python -m scripts.run_all_stages --root . --log-level INFO
```

### 16.2 作用

该命令依次运行公开的 V106、V107、V108、V109 reference-signed 和 V109 generated-chain。

### 16.3 输出位置

```text
runs/stage_all/stage_chain_summary.json
runs/stage_all/public_stage_chain.log
runs/stage_v106/
runs/stage_v107/
runs/stage_v108/
runs/stage_v109_reference/
runs/stage_v109_generated/
```

### 16.4 关键预期字段

成功运行时，`stage_chain_summary.json` 中顶层应出现：

```text
status = success
```

并且每个 stage entry 都应报告成功。

### 16.5 为什么 V107 通常是最耗时阶段？

V107 执行最大的 independent replay 和 compact block-hash audit 检查，因此通常是公开链条中耗时最长的阶段。

---

## 17. 单阶段运行命令

### 17.1 V106

命令：

```bash
python -m scripts.run_stage_v106 --root . --log-level INFO
```

作用：重放 Branch-B domain records、adaptive ledger closure 和 kernel-closure checks。

预期输出：`runs/stage_v106/` 下生成 V106 feedback ZIP、summary JSON 和 log 文件。

### 17.2 V107

命令：

```bash
python -m scripts.run_stage_v107 --root . --log-level INFO
```

作用：执行 independent replay checks 和大表 compact integrity audits。

预期输出：`runs/stage_v107/` 下生成 V107 feedback ZIP、summary JSON 和 log 文件。

### 17.3 V108

命令：

```bash
python -m scripts.run_stage_v108 --root . --log-level INFO
```

作用：检查 theorem-level reproduction closure、proof-obligation binding 和 scope records。

预期输出：`runs/stage_v108/` 下生成 V108 feedback ZIP、summary JSON 和 log 文件。

### 17.4 V109 reference-signed

命令：

```bash
python -m scripts.run_stage_v109 --root . --mode reference-signed --log-level INFO
```

作用：使用随仓库发布的 reference V108 archive 和 author self-review signoff 进行最终签收验证。

预期输出：`runs/stage_v109_reference/` 下生成 V109 summary 和 log。

### 17.5 V109 generated-chain

命令：

```bash
python -m scripts.run_stage_v109 --root . --mode generated-chain \
  --v108-feedback-zip runs/stage_v108/feedback_v108_bs0832_theorem_level_reproduction_closure_attempt_and_final_signoff_package.zip \
  --log-level INFO
```

作用：对本机新生成的 V108-style archive 运行 V109 逻辑。

预期输出：`runs/stage_v109_generated/` 下生成 generated-chain V109 summary 和 log。

---

## 18. reference-signed 与 generated-chain 的区别

`reference-signed` 路线使用 `certificate/reviewer_signoff_v109.json` 中已经审阅的 reference V108 archive。这是快速最终验证使用的 signed-candidate 路线。

`generated-chain` 路线使用本地分阶段复现中新生成的 V108-style archive。这个新 ZIP 可以在语义上等价于 reference archive，但字节层面的 SHA256 不一定相同。它也不会自动继承绑定在 reference V108 archive 上的作者 signoff。

---

## 19. 为什么重新生成的 ZIP 不一定逐字节相同？

重新生成的 ZIP 文件不一定和随仓库发布的 reference ZIP 逐字节相同。原因包括：ZIP metadata、时间戳、压缩参数、文件排序、平台信息或 run identifier 可能不同。

因此，分阶段 summary 会记录 generated 和 reference 的 hash 以便追踪，但逐字节相等不是唯一的复现判据。随仓库发布的 reference artifacts 由 certificate-artifact SHA gate 保护；本机新生成的文件应保存在 `runs/` 目录下，除非有意准备新的 signed release，否则不应直接替换 reference artifacts。

---

## 20. 常见问题与排错

### 20.1 SHA256 检查失败怎么办？

先确认 `inputs/` 和 `certificate/` 下的证书 artifact 没有被手工编辑、重新压缩、下载不完整或路径移动。README、论文、图片和源码注释的修改不应影响 artifact SHA gate。

### 20.2 generated ZIP 与 reference ZIP 不同怎么办？

这不一定是失败。请先比较 staged summary fields 和日志。由于 ZIP metadata 等原因，新生成 ZIP 与 reference ZIP 的 SHA256 可能不同。

### 20.3 `theorem_ready=false` 是否表示失败？

不是。这个字段保持为 false 是预期状态。它表示仓库是 reproducible signed-candidate certificate package，而不是 proof-assistant theorem package。

### 20.4 为什么本仓库不声称更强数值下界？

本仓库只讨论 Brass-Sharifi 0.832 凸下界的证书化复现。它不声称得到更强的数值下界。

### 20.5 为什么本仓库不声称非凸版本？

本仓库只讨论凸版本的 $\alpha_{\mathrm{cvx}}$。它不对 unrestricted nonconvex universal-cover problem 给出下界声明。

### 20.6 为什么本仓库不声称 proof-assistant formalization？

本仓库包含 Python verifier 和证书记录，但不包含 Lean、Coq、Isabelle 或类似系统中的完整形式化证明。

---

## 21. 引用方式

请引用 Brass-Sharifi 原论文作为数学下界来源，并引用本仓库作为 BS0832 可复现证书包。

---

## 22. 许可证与致谢

许可证见 `LICENSE`。配套论文中说明了 ChatGPT 作为辅助工具在组织实现笔记、检查复现流程和改进表述方面的使用；数学声明、计算、证书判断和最终文本由作者负责。
