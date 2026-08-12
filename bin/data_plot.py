#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_plot.py — 科研骨架数据图模块（精确数据图，代码驱动）
依赖: matplotlib, pandas, numpy

用法:
  绘图脚本里 import:
    from data_plot import pub_style, save_fig, okabe_ito
    pub_style(col="single")                    # 期刊样式（单栏 3.3in / 双栏 6.8in）
    fig, ax = plt.subplots()
    ...
    save_fig(fig, "result", data=df)           # pdf矢量 + png 300dpi + csv 数据耦合

  CLI:
    python bin/data_plot.py demo               # 生成演示图（测试环境）
    python bin/data_plot.py list               # 列出可用的样式/配方

可复现约定（scitex-plt 模式）:
  - 脚本自包含 + 确定性（seed 固定）
  - save_fig 自动把数据 csv 与图同存 → 图不脱离数据
  - PDF 矢量投稿 / PNG 300dpi 预览 双出
  - 禁止捏造：数据文件不全要明说，不画假图
"""

import argparse
import os
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

# ── 色盲安全色板（Okabe-Ito）──
OKABE_ITO = ["#E69F00", "#56B4E9", "#009E73", "#F0E442",
             "#0072B2", "#D55E00", "#CC79A7", "#000000"]


def pub_style(col="single"):
    """应用期刊出版样式。col: 'single' 单栏 3.3in / 'double' 双栏 6.8in。

    字体 8pt 基准（最终≥8pt 达标）、无顶/右边框、紧凑布局、
    色盲安全色板、300dpi。不用再逐条设 rcParams。
    """
    import matplotlib
    import matplotlib.pyplot as plt
    w = 3.3 if col == "single" else 6.8
    matplotlib.rcParams.update({
        "figure.figsize": (w, w * 0.72),
        "figure.dpi": 100, "savefig.dpi": 300,
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 8, "axes.titlesize": 10,
        "axes.labelsize": 9, "xtick.labelsize": 8, "ytick.labelsize": 8,
        "legend.fontsize": 8, "legend.frameon": False,
        "axes.prop_cycle": plt.cycler(color=OKABE_ITO),
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.linewidth": 0.8, "grid.linewidth": 0.5,
        "xtick.direction": "out", "ytick.direction": "out",
        "lines.linewidth": 1.5, "lines.markersize": 4,
        "figure.constrained_layout.use": True,
    })
    return matplotlib.rcParams


def save_fig(fig, name, data=None, figdir="figures", dpi=300):
    """数据耦合保存：pdf（矢量，投稿）+ png（300dpi，预览）+ csv（数据）。

    data: pandas DataFrame 或 dict → 同存 csv，保证图不脱离数据。
    """
    import matplotlib.pyplot as plt
    import pandas as pd
    os.makedirs(figdir, exist_ok=True)
    pdf = os.path.join(figdir, f"{name}.pdf")
    png = os.path.join(figdir, f"{name}.png")
    fig.savefig(pdf, dpi=dpi, bbox_inches="tight")
    fig.savefig(png, dpi=dpi, bbox_inches="tight")
    paths = [pdf, png]
    if data is not None:
        df = data if isinstance(data, pd.DataFrame) else pd.DataFrame(data)
        csv = os.path.join(figdir, f"{name}.csv")
        df.to_csv(csv, index=False, encoding="utf-8")
        paths.append(csv)
    plt.close(fig)
    return paths


# ── 演示 ──

def demo():
    """生成演示图（带误差棒的折线）测试环境。"""
    import matplotlib.pyplot as plt
    import pandas as pd
    rng = np.random.default_rng(42)
    x = np.arange(1, 8)
    ours = 0.55 + 0.06 * x + rng.normal(0, 0.01, x.size)
    base = 0.35 + 0.04 * x + rng.normal(0, 0.01, x.size)
    df = pd.DataFrame({
        "step": x,
        "ours_mean": ours, "ours_std": rng.uniform(0.02, 0.04, x.size),
        "baseline_mean": base, "baseline_std": rng.uniform(0.02, 0.04, x.size),
    })
    pub_style(col="single")
    fig, ax = plt.subplots()
    ax.errorbar(df["step"], df["ours_mean"], yerr=df["ours_std"],
                label="Ours", marker="o", capsize=3)
    ax.errorbar(df["step"], df["baseline_mean"], yerr=df["baseline_std"],
                label="Baseline", marker="s", capsize=3)
    ax.set_xlabel("Step")
    ax.set_ylabel("Accuracy")
    ax.legend()
    paths = save_fig(fig, "demo_figure", data=df, figdir="figures")
    for p in paths:
        print(f"  → {p}")
    print("\ndemo 完成：环境正常，样式/色板/数据耦合保存全部可用")


def cmd_list():
    print("data_plot.py — 科研骨架数据图模块\n")
    print("样式:  pub_style(col='single'|'double')")
    print("      单栏 3.3in / 双栏 6.8in, 8pt 基准, Okabe-Ito 色盲安全, 300dpi")
    print("保存:  save_fig(fig, name, data=df) → pdf+png+csv 数据耦合")
    print("色板:  okabe_ito 列表 (8 色, 色盲安全)")
    print("\n工作流: 数据(xlsx/csv) → pandas 读入 → matplotlib 脚本 → 执行循环\n"
          "        → vision.py 渲染检查 → PDF+PNG 双出 → 投稿前可升 PGFPlots")


def main():
    p = argparse.ArgumentParser(description="科研骨架数据图模块")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo", help="生成演示图测试环境")
    sub.add_parser("list", help="列出样式/配方")
    args = p.parse_args()
    if args.cmd == "demo":
        demo()
    else:
        cmd_list()


if __name__ == "__main__":
    main()
