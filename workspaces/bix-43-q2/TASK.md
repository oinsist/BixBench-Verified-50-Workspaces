# bix-43-q2

## Question

What is the odds ratio for p53-mediated cell cycle gene regulation in an enrichment analysis using gseapy with Reactome_2022 using all statistically differentially expressed genes from a pydeseq2 analysis that includes all related treatment groups (DMSO, DMSO_Serum_starvation, Cisplatin_IC50_CBD_IC50, Cisplatin_IC50_CBD_IC50_Serum_starvation_16h) for proper dispersion estimation, after pre-filtering to keep only genes with counts greater than 10 in at least one of all 30 samples, (padj<=0.05, absolute lfc>=0.5, baseMean>=10) between CBD/cisplatin combination treatment and DMSO?

## 工作目录

- `data/`：已校验的原始输入。先从仓库根目录执行 `python3 prepare.py bix-43-q2`。
- `analysis/`：分析脚本或 Notebook。
- `outputs/`：结果文件及图表。

完成后写入 `outputs/answer.json`，格式见 `AGENTS.md`。
