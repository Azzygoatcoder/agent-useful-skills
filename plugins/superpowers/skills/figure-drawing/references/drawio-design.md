## draw.io XML 约定（踩坑总结）

- 结构：`<mxfile> → <diagram> → <mxGraphModel> → <root>`；`id="0"`/`id="1"` 是保留哨兵 cell
- 顶点：`<mxCell id="x" value="..." style="..." vertex="1" parent="1"><mxGeometry x=".." y=".." width=".." height=".." as="geometry"/></mxCell>`
- 连线：`<mxCell ... edge="1" parent="1" source="a" target="b"><mxGeometry relative="1" as="geometry"/></mxCell>`
- **HTML 必须转义**：`<b>`→`&lt;b&gt;`、`<br>`→`&lt;br&gt;`（踩过坑：图例用原始标签 → XML 非法）
- 样式：`rounded=1;fillColor=#hex;strokeColor=#hex;fontSize=11;verticalAlign=middle;align=center`
- 箭头语义：**实线**=数据流/代码提交 · **虚线**=委托/反馈 · 高亮闸门用红框+加粗
- 布局：避免元素重叠、连线交叉；信息层级分明；加标题+副标题+图例

## 编辑级别设计系统（吸收自 diagram-design，2026-08-11）

第三方 skill（cathrynlavery/diagram-design，27 类型编辑器级图表）的设计系统。核心哲学：**克制是最高级的操作，密度 4/10**。场景 B 对外图、以及任何 draw.io 产出，生成后用此清单自查。

### 反 AI-slop 清单（AI 味元凶）

| 禁 | 原因 |
|----|------|
| 阴影（box-shadow） | 边界才是高级；阴影=AI 味 |
| 深色+cyan/紫光晕 | "看起来技术"≠设计决策 |
| 全同方块 | 抹平层级 |
| 图例浮在图内 | 和节点打架（放底部横向条带） |
| 圆角 >10px | 最大 6-10px 或直角 |
| 强调色 >2 处 | 用多了就没强调 |
| 对角线连接 | **必须正交直角弯（r=8）**，共享 x/y 轴才用直线 |
| 箭头标签压线 | 标签下白底遮罩 + 与线 **6-10px 空隙** |
| 两条线重叠/同路径 | 各自可追踪；交叉用桥接/错位 ≥12px |
| 同边多线共用一个连接点 | 沿边展开 **≥12px 间距**（N 线位置=L·k/(N+1)） |
| 连线穿过非端点盒子 | 绕行；不可避免时虚线(4,3)+标签放可见端+箭头不落中间盒子 |
| 垂直 writing-mode 文字 | 不可读 |
| JetBrains Mono 铺满 | Mono 只给端口/URL/命令，名字用 sans |
| 3 个等宽总结卡片 | 通用网格感；卡片要变宽度 |

### 节点语义→样式（类型决定填色描边）

| 节点类型 | 填充 | 描边 |
|---------|------|------|
| Focal（1-2 个） | accent-tint | accent |
| Backend/API/Step | 白 | ink |
| Store/State | ink@0.05 | muted |
| External/Cloud | ink@0.03 | ink@0.30 |
| Input/User | muted@0.10 | soft |
| Optional/Async | ink@0.02 | ink@0.20 虚线 4,3 |
| Security/Boundary | accent@0.05 | accent@0.50 虚线 4,4 |

### 硬规则

- **4px 网格**：所有坐标/宽高/间距/字号能被 4 整除（非协商；坐标尾数 1/2/3/5/6/7/9 必改）
- **复杂度预算**：≤9 节点 / ≤12 箭头 / 强调 ≤2 处；超了拆两图（总览+细节）
- **箭头语义**：实线=数据流 · 虚线=委托/返回/异步 · accent=主要路径
- **图例**：底部横向条带 + 细线分隔，viewBox 加高 ~60px
- **连线先画，盒子后画**（z-order 线在节点下）
