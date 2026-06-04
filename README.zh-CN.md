# Brass-Sharifi 0.832 下界的可复现证书包

本仓库提供 Lebesgue 万有覆盖问题中 Brass-Sharifi 0.832 凸下界的可复现证书包。这里的目标不等式是：

```text
A(v) >= 0.832
```

Brass-Sharifi 原论文是这个下界的数学来源。本仓库不提高这个数值，也不重新发明这个下界；它做的是把原来的计算辅助证明整理成一条可以运行、重放和审计的有限证书链。

## 1. 什么是 Lebesgue 万有覆盖问题？

给定一个平面集合，如果任意直径为 1 的平面集合都可以通过平移和旋转得到一个全等副本，并放入这个集合中，那么这个集合就是一个万有覆盖。本文和本仓库讨论的是凸情形：覆盖集合本身要求是凸集，目标是让这个凸集的面积尽可能小。

Brass-Sharifi 证明了凸情形下的 0.832 下界。他们使用三个直径为 1 的测试集：圆盘、正三角形和正五边形。经过归一化后，圆盘固定，三角形只平移，正五边形先旋转再平移。下界计算研究的是这三个测试集在归一化摆放下的凸包面积。

<p align="center">
  <img src="assets/figures/geometry.png" alt="三测试集归一化摆放" width="45%">
</p>

## 2. Brass-Sharifi 原论文做了什么？

Brass-Sharifi 原论文把凸万有覆盖下界问题化为一个三测试集摆放问题，并结合几何估计和计算搜索，证明相关凸包面积始终不小于 0.832。因此，任意凸万有覆盖的面积也至少为 0.832。

原论文给出了数学思想、估计方法和汇总计算规模。但是，它没有以现代可复现证书包的形式公开完整的终端路线、重放表、哈希审计和证明义务层。

## 3. 本仓库补充了什么？

本仓库补充的是“可复现证书”这一层。它把 Brass-Sharifi 的计算辅助证明整理成一套有限、结构化、可运行检查的数据与脚本，包括：

1. 记录细分树的 adaptive ledger；
2. 记录终端子问题的 terminal-route replay；
3. 三类局部下界证书；
4. 大型表格的完整性检查；
5. 把计算数据连接到最终下界陈述的证明义务层；
6. 作者自审签收记录。

本仓库的增量不在于提高 0.832 这个数值，而在于让这次计算辅助证明可以被重放、审计和复查。

## 4. 为什么这条证书链能支撑 0.832 下界？

证书链的逻辑是有限的。Branch-B 域记录先覆盖需要考虑的归一化摆放域；然后重放程序把该域覆盖为有限个终端路线；每个终端路线都被分派给一个局部证书族；每个被接受的局部证书都证明该路线上的凸包面积不小于 0.832；最后，证明义务层检查这些局部结论能否汇总为全局下界。

简化地说：

```text
可考虑的摆放域
  -> Branch-B 重放域
  -> 终端路线
  -> 局部下界证书
  -> 证明义务
  -> BS0832 证书陈述
```

<p align="center">
  <img src="assets/figures/certificate_flow.png" alt="证书流程" width="35%">
</p>

## 5. V106-V109 阶段标签说明

V106-V109 是本复现项目中的阶段标签，来自开发版本 v0.10.6-v0.10.9 的简写。它们不是数学常数，也不是定理编号。仓库使用这些标签，是为了标识最终证书链中的四个验证阶段。

<table>
  <thead>
    <tr>
      <th align="center" valign="middle">阶段</th>
      <th align="center" valign="middle">对应开发版本</th>
      <th align="center" valign="middle">作用</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center" valign="middle">V106</td>
      <td align="center" valign="middle">v0.10.6</td>
      <td align="center" valign="middle">Branch-B 域重放和 kernel-closure 检查</td>
    </tr>
    <tr>
      <td align="center" valign="middle">V107</td>
      <td align="center" valign="middle">v0.10.7</td>
      <td align="center" valign="middle">独立重放和分块哈希审计</td>
    </tr>
    <tr>
      <td align="center" valign="middle">V108</td>
      <td align="center" valign="middle">v0.10.8</td>
      <td align="center" valign="middle">复现闭合和证明义务绑定</td>
    </tr>
    <tr>
      <td align="center" valign="middle">V109</td>
      <td align="center" valign="middle">v0.10.9</td>
      <td align="center" valign="middle">最终签收裁决和作者自审验证</td>
    </tr>
  </tbody>
</table>

## 6. 仓库目录结构

```text
universal-cover-bs0832-reproduction/
├── README.md
├── README.zh-CN.md
├── ARTIFACTS.md
├── CERTIFICATE.md
├── EXPECTED_OUTPUTS.md
├── CITATION.cff
├── .github/workflows/
├── assets/figures/
├── app/domain/
├── scripts/
├── inputs/
├── certificate/
│   └── intermediate/
└── paper/
```

<table>
  <thead>
    <tr>
      <th align="center" valign="middle">路径</th>
      <th align="center" valign="middle">作用</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="center" valign="middle"><code>assets/figures/</code></td>
      <td align="center" valign="middle">README 中使用的说明图</td>
    </tr>
    <tr>
      <td align="center" valign="middle"><code>app/domain/</code></td>
      <td align="center" valign="middle">证书读取、哈希检查、签收验证、分阶段重放和最终验证的核心逻辑</td>
    </tr>
    <tr>
      <td align="center" valign="middle"><code>scripts/</code></td>
      <td align="center" valign="middle">用户运行入口，建议用 <code>python -m scripts.xxx</code> 执行</td>
    </tr>
    <tr>
      <td align="center" valign="middle"><code>inputs/</code></td>
      <td align="center" valign="middle">分阶段复现所需的源证书压缩包</td>
    </tr>
    <tr>
      <td align="center" valign="middle"><code>certificate/</code></td>
      <td align="center" valign="middle">最终证书、作者自审文件、manifest 和校验清单</td>
    </tr>
    <tr>
      <td align="center" valign="middle"><code>certificate/intermediate/</code></td>
      <td align="center" valign="middle">V106-V108 参考反馈包，用于比对和 reference-signed 验证</td>
    </tr>
    <tr>
      <td align="center" valign="middle"><code>paper/</code></td>
      <td align="center" valign="middle">配套论文 PDF</td>
    </tr>
    <tr>
      <td align="center" valign="middle"><code>runs/</code></td>
      <td align="center" valign="middle">脚本运行后自动生成的输出目录，不需要手工创建或提交</td>
    </tr>
  </tbody>
</table>

## 7. 必需文件

`inputs/` 目录中应包含分阶段复现所需的源证书包：

```text
feedback_v050_h004_local_proof_freeze_main.zip
feedback_v086_true_arb_and_local_tensor_port_v1.zip
feedback_v096_adaptive_full_ledger_rerun_executor.zip
adaptive_full_ledger_export_v096.zip
feedback_v097_external_proof_replay_and_proof_package_v6_audit.zip
feedback_v104_bs0832_domain_closure_and_final_theorem_freeze_decision.zip
feedback_v105_bs0832_domain_resolution_final_signoff_and_conditional_enlarged_domain_execution.zip
```

`certificate/` 目录中应包含最终证书和签收文件：

```text
feedback_v109_signed_author_self_review.zip
reviewer_signoff_v109.json
MANIFEST.json
SHA256SUMS.txt
```

请不要手工修改这些 ZIP 文件。验证脚本会把它们作为证书数据读取。

## 8. 环境安装

建议使用 Python 3.10 或更新版本。

```bash
python -m pip install -r requirements.txt
```

也可以使用 Conda：

```bash
conda env create -f environment.yml
conda activate bs0832-reproduction
```

## 9. 快速最终验证

如果只想检查仓库中已有的最终证书和作者自审文件是否自洽，运行：

```bash
python -m scripts.run_final_verification --root . --log-level INFO
```

成功后会生成：

```text
runs/final_verification/final_verification_summary.json
runs/final_verification/final_verification.log
```

重点字段应为：

```text
bs0832_final_repository_verification_passed = true
theorem_ready_signed_candidate = true
theorem_ready = false
proof_boundary_violations = 0
```

`theorem_ready=false` 是预期结果。它表示本仓库是作者自审的可复现证书包，而不是 Lean、Coq、Isabelle 等形式化证明系统中的完整机器检验证明。

## 10. 完整分阶段复现

运行：

```bash
python -m scripts.run_all_stages --root . --log-level INFO
```

该命令会依次运行 V106、V107、V108 和两种 V109 模式，并把结果写到 `runs/` 目录。

预期顶层输出包括：

```text
runs/stage_v106/
runs/stage_v107/
runs/stage_v108/
runs/stage_v109_reference/
runs/stage_v109_generated/
runs/stage_all/stage_chain_summary.json
```

V107 会执行独立重放和分块哈希审计，是几个阶段中最重的一步，运行时间可能明显长于其它阶段。

## 11. 单阶段运行命令

### V106

```bash
python -m scripts.run_stage_v106 --root . --log-level INFO
```

作用：从源证书包重建 Branch-B 域重放和 kernel-closure 反馈包。

### V107

```bash
python -m scripts.run_stage_v107 --root . --log-level INFO
```

作用：执行独立重放和紧凑哈希审计。若要强制使用刚生成的 V106 文件：

```bash
python -m scripts.run_stage_v107 --root . \
  --v106-feedback-zip runs/stage_v106/feedback_v106_bs0832_branchB_domain_and_final_kernel_closure_sprint.zip \
  --log-level INFO
```

### V108

```bash
python -m scripts.run_stage_v108 --root . --log-level INFO
```

作用：把重放得到的证书数据绑定到证明义务。若同时使用刚生成的 V106 和 V107 文件：

```bash
python -m scripts.run_stage_v108 --root . \
  --v107-feedback-zip runs/stage_v107/feedback_v107_bs0832_final_theorem_release_candidate_and_independent_review_bundle.zip \
  --v106-feedback-zip runs/stage_v106/feedback_v106_bs0832_branchB_domain_and_final_kernel_closure_sprint.zip \
  --log-level INFO
```

### V109：reference-signed 模式

```bash
python -m scripts.run_stage_v109 --root . --mode reference-signed --log-level INFO
```

作用：用仓库中的参考 V108 文件验证作者自审签收。

### V109：generated-chain 模式

```bash
python -m scripts.run_stage_v109 --root . --mode generated-chain \
  --v108-feedback-zip runs/stage_v108/feedback_v108_bs0832_theorem_level_reproduction_closure_attempt_and_final_signoff_package.zip \
  --log-level INFO
```

作用：使用刚生成的 V108-style 文件运行 V109。除非额外提供与该新文件匹配的签收文件，否则该模式不会自动继承作者自审签收。

## 12. reference-signed 与 generated-chain 两种模式

仓库支持两种 V109 运行模式。

### reference-signed 模式

reference-signed 模式使用仓库中已经随附的参考 V108 文件，并检查作者自审文件是否确实绑定到这个参考文件的 SHA256。

换句话说，这个模式验证的是“仓库随附的、已经作者自审的最终证书链”。快速最终验证使用的就是这条路径。

### generated-chain 模式

generated-chain 模式使用用户本地重新生成的 V108-style 文件。

重新生成的 ZIP 即使内部证书内容在逻辑上等价，外层 ZIP 的 SHA256 也可能和参考文件不同。这通常是因为 ZIP 文件可能记录压缩时间、压缩参数、文件顺序或其它元数据。

因此，仓库自带的作者自审文件不会被视为已经签收这个新生成的 ZIP。它绑定的是 signoff 文件中记录的参考 V108 文件 SHA256。

也就是说，generated-chain 模式可以检查新生成的证书链是否通过预期的结构和验证检查，但不会自动给这个新 ZIP 附加仓库自带的作者自审签收。

## 13. 为什么重新生成的 ZIP 不一定逐字节相同？

重新生成的 ZIP 文件可能与仓库中的参考 ZIP 不完全一致，即使其中关键证书内容是等价的。这并不自动表示复现失败。

**为什么 SHA256 可能不同？** ZIP 文件不仅保存文件内容，还可能保存压缩时间、文件顺序、压缩参数等元数据。重新打包时，这些元数据可能发生变化。

**脚本到底检查什么？** 分阶段复现时，脚本会检查更关键的内部内容：状态文件、schema 检查、replay 行数、边界审计、关键内容哈希，以及在适用时检查签收绑定。

**为什么还要记录两个 SHA256？** 阶段摘要会同时记录新生成 ZIP 和参考 ZIP 的 SHA256，方便追踪来源和比对。外层 ZIP 的 SHA256 用来识别文件；真正决定证书是否通过的是内部检查。

## 14. 预期输出

快速最终验证成功时，应看到：

```text
status = success
bs0832_final_repository_verification_passed = true
theorem_ready_signed_candidate = true
theorem_ready = false
proof_boundary_violations = 0
```

完整分阶段复现成功时，`runs/stage_all/stage_chain_summary.json` 中应报告：

```text
status = success
```

其中 generated-chain 模式下的 V109 通常不会继承作者自审签收，除非提供与新生成 V108 文件匹配的新签收文件。

## 15. 常见问题

- 如果缺少文件，请先检查 `inputs/` 和 `certificate/` 目录。
- 如果 SHA256 检查失败，不要手工修改 ZIP 文件；请恢复原始证书文件。
- 如果 V107 运行时间较长，这是正常的，因为它包含较重的独立重放和哈希审计。
- 如果 generated-chain 模式没有继承作者自审签收，这是预期行为；仓库中的签收文件绑定的是参考 V108 文件。

## 16. 引用与许可证

请引用 Brass-Sharifi 原论文作为 0.832 下界的数学来源。如果使用本仓库，也请引用配套论文和本仓库公开版本。

代码许可证见 `LICENSE`。
