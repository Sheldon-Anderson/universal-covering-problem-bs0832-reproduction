# Lebesgue 万有覆盖问题认证下界证书

本仓库包含一个有限证书包和确定性的 Python 验证程序，用于验证凸 Brass-Sharifi 三测试集框架下的认证下界。

本仓库验证随仓库打包的有限证书记录。它不会重新运行原始几何搜索程序，也不会从零生成证书记录。

## 1. 这个仓库验证什么

本仓库验证阈值 $\tau=0.83201$。结合 Brass-Sharifi 归一化原理，它给出凸版本的证书结论：

```math
\alpha_{\mathrm{cvx}} \ge 0.83201.
```

这里 $\alpha_{\mathrm{cvx}}$ 表示凸万有覆盖集合面积的下确界。证明使用有限覆盖、支撑型局部记录、见证域多边形记录、外向舍入区间估计和最终聚合检查。

## 2. 范围边界

本仓库声称：

- 在凸 Brass-Sharifi 三测试集证书框架下验证 $\tau=0.83201$；
- 得到对应的凸版本证书结论；
- 对随仓库打包的证书记录做确定性复验。

本仓库不声称：

- 包含非凸版本结论；
- 已有 proof-assistant 形式化；
- 已完成独立外部验证；
- 重新运行原始几何搜索或重新生成证书归档。

## 3. 仓库包含哪些内容

| 路径 | 作用 |
|---|---|
| `certificate/final_chain/` | 四个随仓库打包的证书链归档。 |
| `certificate/manifest/` | SHA256 清单和手动校验说明。 |
| `certificate/public/CERTIFICATE_INDEX.md` | 证书组件和证明义务角色的索引。 |
| `ucbs/` | Python 包根目录，可理解为 universal-cover Brass-Sharifi certificate verifier。 |
| `scripts/` | 稳定的命令行入口。 |
| `tests/` | 可选开发者回归测试。 |
| `docs/` | 复现说明、输出字段、数据字典、artifact 策略和声明边界。 |
| `paper/` | 编译后的论文 PDF。 |

仓库已经包含验证所需的证书数据，不需要额外下载。

### 关键术语

| 术语 | 含义 |
|---|---|
| 有限证书 | 用有限条记录验证下界结论。 |
| 证书验证 | 对随仓库打包的证书记录做确定性复验。 |
| 见证构造 | 见证域上的多边形下界记录。 |
| 构造审计 | support-to-area 与区间舍入检查。 |
| 最终核验 | 证明义务和声明边界检查。 |

## 4. 数学证明链路

证明链路是：

1. 凸万有覆盖集合包含直径为 1 的圆盘、等边三角形和正五边形的合同副本。
2. Brass-Sharifi 归一化把对应的三测试集凸包写成容许域 $\Omega_{\mathrm{adm}}$ 上的参数化问题。
3. 有限证书验证 $\Omega_{\mathrm{adm}}$ 的有限覆盖。
4. 每个覆盖域都有局部下界。支撑域使用支撑型局部记录，见证域使用有序见证多边形和区间鞋带公式下界。
5. 最终聚合得到 $A(v)\ge 0.83201$，从而推出凸版本下界。

证书链复验只复验 `certificate/final_chain/` 中已经打包的证书记录，不搜索新的证书。

## 5. 快速验证

直接在解压后的源码目录中运行：

```bash
python scripts/check_repository.py --root . --log-level INFO
```

仓库发布检查会在内部运行主证书验证。使用 `python scripts/...` 命令时，不需要先执行 editable install。

## 6. 主要命令

### 6.1 主证书验证

```bash
python scripts/verify_certificate.py --root . --log-level INFO
```

作用：验证四个证书链归档，并在 `runs/certificate_verification/` 下写出主证书状态。

### 6.2 仓库发布检查

```bash
python scripts/check_repository.py --root . --log-level INFO
```

作用：检查 Python 编译、包配置、仓库布局、Markdown 数学渲染、声明边界、artifact 哈希和主证书验证。

### 6.3 证书链验证

```bash
python scripts/replay_certificate_chain.py --root . --log-level INFO
```

作用：验证四个证书链组件，不检查 README、docs、仓库目录结构或发布质量。

分组件复验命令见 `docs/reproducibility.md`。

### 6.4 开发者回归测试

```bash
python -m unittest discover -s tests
```

公开证书验证不要求运行这些测试。它们用于检查命令行入口、README 数学渲染 lint、公开叙事 lint 和证书校验辅助函数是否被后续修改破坏。

## 7. 成功结果怎么看

主证书验证应包含：

```json
{
  "status": "passed",
  "certificate_verified": true,
  "threshold_proved": true,
  "certified_threshold": "0.83201",
  "failed_component_count": 0
}
```

仓库发布检查应包含：

```json
{
  "status": "passed",
  "failed_step_count": 0
}
```

详细输出字段见 `docs/expected_outputs.md` 和 `docs/data_dictionary.md`。

## 8. 论文、引用和许可

论文 PDF 位于：

`paper/A_Certified_Lower_Bound_for_Lebesgues_Universal_Cover_Problem.pdf`

LaTeX 源码由论文发布包或 arXiv source archive 保存，不放在这个证书验证仓库中。

引用信息见 `CITATION.cff`。代码和公开文档采用 MIT 许可，见 `LICENSE`。

故障排除见 `docs/reproducibility.md`；常见问题见 `docs/faq.md`。
