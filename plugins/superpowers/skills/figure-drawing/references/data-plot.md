## D 场景：精确数据图（代码驱动，2026-08-12）

**为什么不能 AI 画**：数据图的值必须与数据完全一致——gpt-image-2/diagram-design 画的是结构不是数据。唯一可靠路径是 **数据 → 代码 → 渲染**。gpt-image-2 对数据图**禁用**（会伪造数值）。

### D1. 数据准备
- xlsx/csv → pandas 读入（复用 office_tools 的 xlsx 处理）
- **数据文件不全 → 明说缺口，不画假图**（scitex-plt 禁止捏造原则）

### D2. 脚本生成
```python
from data_plot import pub_style, save_fig   # bin/data_plot.py
pub_style(col="single")                      # 单栏 3.3in / 双栏 6.8in
fig, ax = plt.subplots()
# ... 画图（误差棒/图例/标签/色盲安全色板）...
save_fig(fig, "result", data=df)             # pdf矢量 + png300dpi + csv 数据耦合
```
- 脚本自包含 + 确定性（seed 固定、路径硬编码）——可复现
- `pub_style` 已内置：8pt 基准 / Okabe-Ito 色盲安全 / 无顶右边框 / 300dpi

### D3. 执行循环
- 运行脚本 → traceback 回喂重生成（≤4 次）
- 数据耦合输出：pdf + png + **csv 与图同存**（图不脱离数据）

### D4. vision 渲染检查（必做）
- `vision.py` 看图：图例冲突 / 未标注序列 / 坐标轴截断 / 文字溢出 / 配色
- 数值准确性由代码保证（值来自数据）；vision 查**视觉错误**
- 与概念图共用 vision 验证环，但标准不同：数据图看"清楚 + 值对"，概念图看"设计一致"

### D5. 投稿升级（可选）
- 论文接近投稿、需字体对齐 → 从 matplotlib 升 **PGFPlots**（LaTeX 原生，接 latex-templates）
- 规则：matplotlib 快速迭代 → PGFPlots 定稿（camera-ready）
