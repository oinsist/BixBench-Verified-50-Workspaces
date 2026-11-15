# bix-20-q3

## Question

Among samples with a 'Carrier' BLM mutation status, what proportion of somatic CHIP variants (VAF < 0.3) with ClinVar classifications are classified as Benign or Likely Benign? The proportion of somatic CHIP variants should be calculated after filtering out intronic, intergenic, UTR regions, and reference (non-variant) calls.

## 工作目录

- `data/`：已校验的原始输入。先从仓库根目录执行 `python3 prepare.py bix-20-q3`。
- `analysis/`：分析脚本或 Notebook。
- `outputs/`：结果文件及图表。

完成后写入 `outputs/answer.json`，格式见 `AGENTS.md`。
