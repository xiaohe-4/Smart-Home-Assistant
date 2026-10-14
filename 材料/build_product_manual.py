# -*- coding: utf-8 -*-
"""生成《产品实现方向——产品说明书》PDF 与其他辅助材料 ZIP。"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    KeepTogether,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
MAT = Path(__file__).resolve().parent
AUX = MAT / "产品实现方向_其他辅助材料"
SIMHEI = Path(r"C:\Windows\Fonts\simhei.ttf")
MSYH = Path(r"C:\Windows\Fonts\msyh.ttc")

GREEN = colors.HexColor("#16a34a")
DARK = colors.HexColor("#08241c")
TEXT = colors.HexColor("#123026")
MUTED = colors.HexColor("#5f746a")
CREAM = colors.HexColor("#f4faf6")
LINE = colors.HexColor("#d1e7db")


def register_fonts():
    if SIMHEI.exists():
        pdfmetrics.registerFont(TTFont("CN", str(SIMHEI)))
    elif MSYH.exists():
        pdfmetrics.registerFont(TTFont("CN", str(MSYH), subfontIndex=0))
    else:
        raise SystemExit("未找到中文字体 simhei.ttf / msyh.ttc")


def styles():
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "cover_title", fontName="CN", fontSize=28, leading=36, textColor=colors.white, alignment=1, spaceAfter=12
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", fontName="CN", fontSize=13, leading=20, textColor=colors.HexColor("#bbf7d0"), alignment=1, spaceAfter=8
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", fontName="CN", fontSize=10, leading=16, textColor=colors.HexColor("#9eccb8"), alignment=1
        ),
        "h1": ParagraphStyle("h1", fontName="CN", fontSize=16, leading=24, textColor=DARK, spaceBefore=14, spaceAfter=8),
        "h2": ParagraphStyle("h2", fontName="CN", fontSize=12, leading=18, textColor=GREEN, spaceBefore=10, spaceAfter=6),
        "body": ParagraphStyle("body", fontName="CN", fontSize=10, leading=16, textColor=TEXT, spaceAfter=6),
        "small": ParagraphStyle("small", fontName="CN", fontSize=8.5, leading=13, textColor=MUTED, spaceAfter=4),
        "bullet": ParagraphStyle("bullet", fontName="CN", fontSize=10, leading=15, textColor=TEXT),
        "code": ParagraphStyle("code", fontName="Courier", fontSize=8, leading=11, textColor=DARK, backColor=CREAM),
        "footer": ParagraphStyle("footer", fontName="CN", fontSize=8, textColor=MUTED, alignment=1),
    }


def p(text: str, style):
    return Paragraph(text.replace("\n", "<br/>"), style)


def bullets(items, st):
    return ListFlowable(
        [ListItem(Paragraph(i, st["bullet"]), leftIndent=8, bulletColor=GREEN) for i in items],
        bulletType="bullet",
        start="•",
        leftIndent=12,
        bulletFontName="CN",
        bulletFontSize=10,
    )


def table(data, col_widths):
    cell_style = ParagraphStyle("cell", fontName="CN", fontSize=8.5, leading=12, textColor=TEXT)
    head_style = ParagraphStyle("head", fontName="CN", fontSize=8.5, leading=12, textColor=DARK)
    rows = []
    for r, row in enumerate(data):
        rows.append([Paragraph(str(c), head_style if r == 0 else cell_style) for c in row])
    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), CREAM),
                ("TEXTCOLOR", (0, 0), (-1, 0), DARK),
                ("GRID", (0, 0), (-1, -1), 0.4, LINE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(GREEN)
    canvas.setLineWidth(2)
    canvas.line(18 * mm, A4[1] - 12 * mm, A4[0] - 18 * mm, A4[1] - 12 * mm)
    canvas.setFont("CN", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, A4[1] - 10 * mm, "智家能 · 产品说明书")
    canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}")
    canvas.restoreState()


def cover_page(st):
    story = []
    story.append(Spacer(1, 45 * mm))
    story.append(p("智家能", st["cover_title"]))
    story.append(p("产品说明书", st["cover_title"]))
    story.append(Spacer(1, 8 * mm))
    story.append(p("今晚该关什么 · 家庭多模态能源决策系统", st["cover_sub"]))
    story.append(Spacer(1, 6 * mm))
    story.append(
        p(
            "产品实现方向提交材料<br/>含：产品概述 · 目标用户 · 核心功能 · AI 角色与价值 · 技术实现思路 · 应用场景示例",
            st["cover_meta"],
        )
    )
    story.append(Spacer(1, 20 * mm))
    story.append(p("指标口径：models/metrics.json（2026-08-23）", st["cover_meta"]))
    story.append(p("仓库：github.com/xiaohe-4/Smart-Home-Assistant", st["cover_meta"]))
    story.append(p("本地演示：http://127.0.0.1:5174/", st["cover_meta"]))
    story.append(PageBreak())
    return story


def build_manual_pdf() -> Path:
    register_fonts()
    st = styles()
    out = MAT / "产品实现方向_产品说明书_智家能.pdf"
    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title="智家能·产品说明书",
        author="智家能团队",
    )

    story = []
    # Cover with dark band drawn via table full-width feel
    cover_data = [[p("<font color='white'><b>智家能</b></font><br/><font color='#bbf7d0'>产品说明书 · 今晚该关什么</font>", st["cover_sub"])]]
    cover_t = Table(cover_data, colWidths=[174 * mm])
    cover_t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), DARK),
                ("TOPPADDING", (0, 0), (-1, -1), 28),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 28),
                ("LEFTPADDING", (0, 0), (-1, -1), 16),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ]
        )
    )
    story.append(cover_t)
    story.append(Spacer(1, 10 * mm))
    story.append(p("基于多模态家庭数据分析的 AI 能源管理与节能决策系统", st["body"]))
    story.append(p("版本 V1.0（校园赛提交） · 团队：蔡华升、何鹏", st["small"]))
    story.append(p("本文档对应赛事栏目「产品实现方向——产品说明书」（PDF）。", st["small"]))
    story.append(Spacer(1, 4 * mm))
    story.append(
        p(
            "电表只告诉你这个月多少度。智家能回答三件事：为什么贵、哪笔是浪费、今晚关哪一档——"
            "并把建议交给管家模拟执行，对比电量与电费变化。",
            st["body"],
        )
    )
    story.append(PageBreak())

    # 1
    story.append(p("1. 产品概述", st["h1"]))
    story.append(
        p(
            "智家能是面向普通家庭的多模态能源决策系统。以电力、室内温湿度、占用、天气四路传感时序为输入，"
            "经对齐、预测、异常解释、策略与执行，形成「看懂 → 查清 → 去办」的闭环。",
            st["body"],
        )
    )
    story.append(
        bullets(
            [
                "为什么贵：今日电量、峰谷结构、第一耗电设备",
                "哪笔浪费：凌晨异常、低占用高功率等，规则归因",
                "今晚关哪一档：可勾选策略 + 管家宝强模拟执行与电费对比",
            ],
            st,
        )
    )
    story.append(
        p(
            "演示家庭：成都四口之家 · 夏季 · 约 30 天 · 时刻锁定 2026-08-19 20:30。"
            "演示户保证现场可复现；验证户证明导入与缺模态降级能力。",
            st["body"],
        )
    )

    # 2
    story.append(p("2. 目标用户", st["h1"]))
    story.append(
        table(
            [
                ["用户", "痛点", "产品如何帮到"],
                ["城市家庭住户", "账单难懂、不知今晚改什么", "总览回放 + 执行单 + 管家一句话"],
                ["宿舍 / 合租", "待机与异常浪费看不见", "异常解释器按规则归因"],
                ["能源服务 / 物业演示", "需要可移植决策内核", "标准表灌库 + 缺模态降级 + 验证户导入"],
                ["技术评审", "要看真实指标与边界", "实验舱落盘指标；F1 主动展示"],
            ],
            [32 * mm, 55 * mm, 87 * mm],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(p("非目标：不替代缴费电表；不做无标签总表 NILM；现场不控制真实物理插座。", st["small"]))

    # 3
    story.append(p("3. 核心功能", st["h1"]))
    story.append(p("3.1 智能总览", st["h2"]))
    story.append(
        p(
            "今日用电、电费、能源评分、第一耗电设备；24 小时功率回放（实际/优化/占用）；"
            "四路对齐提示：室内温度进模型，室外天气不进，光照与 CO₂ 只解释。",
            st["body"],
        )
    )
    story.append(p("3.2 能耗分析与设备", st["h2"]))
    story.append(
        p(
            "分路电量占比（演示日空调约 41%、热水器约 22%、冰箱约 12%）。占比来自分路汇总，不是总表盲拆。",
            st["body"],
        )
    )
    story.append(p("3.3 能耗预测", st["h2"]))
    story.append(
        p(
            "XGBoost 递推未来 6/24 小时；绿色带宽=真实 RMSE。只报 MAE/RMSE/MAPE/R²，"
            "并对照昨天同时段与近 7 日同时段平均。禁止用 100−MAPE 当准确率。",
            st["body"],
        )
    )
    story.append(p("3.4 异常解释器", st["h2"]))
    story.append(
        p(
            "主规则（凌晨用水电、无人仍高功率等）+ Isolation Forest 打分。"
            "演示户 03:17 热水器可回放归因。F1=0.35（标注 13/检出 27）主动展示，结论以规则为准，不做自动断电。",
            st["body"],
        )
    )
    story.append(p("3.5 AI 节能建议", st["h2"]))
    story.append(
        p(
            "多目标：收益×可行性×接受度×舒适度。Top 策略：空调 24℃→26℃。"
            "同屏对比电量/电费/碳排/削峰曲线；节能量按本户今日电量估算。",
            st["body"],
        )
    )
    story.append(p("3.6 管家宝强与生活系统", st["h2"]))
    story.append(
        p(
            "管家支持白话指令与点头确认，模拟改当前设定、不改历史曲线，拒绝关冰箱。"
            "生活系统提供电价时钟、今晚任务、电网削峰邀约、谷电预约。",
            st["body"],
        )
    )
    story.append(p("3.7 数据来源与模型实验舱", st["h2"]))
    story.append(
        p(
            "传感合同表写清采样、单位、是否进模型、演示/验证对照；缺一路降级。"
            "实验舱并排演示户与验证户指标；验证户周均值优于模型时诚实提示。",
            st["body"],
        )
    )

    # 4
    story.append(p("4. AI 的角色与价值", st["h1"]))
    story.append(
        p(
            "AI 在本产品中不是聊天报分，而是可落盘复现的预测、打分与分类模块，"
            "与规则引擎分工：模型给能力与不确定性，规则给可执行结论与安全底线。",
            st["body"],
        )
    )
    story.append(
        table(
            [
                ["模块", "方法", "角色", "价值边界"],
                ["能耗预测", "XGBoost\nTimeSeriesSplit", "预判今晚/明天负荷", "只报落盘指标；带宽≠保证"],
                ["异常检测", "IF + 规则", "IF 打分；规则归因", "F1=0.35；上线以规则为准"],
                ["负荷识别", "RandomForest\n有标签 1h 窗", "有分路时的窗分类", "不是总表 NILM"],
                ["节能策略", "规则多目标", "生成今晚动作并模拟", "按本户估算，不空头承诺"],
                ["管家/助手", "规则意图", "把建议变成动作", "大模型不算指标；模拟控制"],
            ],
            [28 * mm, 36 * mm, 42 * mm, 68 * mm],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        p(
            "<b>AI 价值一句话：</b>把「看不懂的度」变成「说得清的原因」和「今晚可执行的一档」，"
            "并用可复现实验同时展示能力与短板。",
            st["body"],
        )
    )

    # 5
    story.append(p("5. 技术实现思路", st["h1"]))
    story.append(p("5.1 架构与技术栈", st["h2"]))
    story.append(
        Preformatted(
            "传感四路 → 5分钟对齐/缺模态降级 → SQLite\n"
            "              ↓\n"
            "       FastAPI 业务服务\n"
            "    ┌───────┼───────┐\n"
            " 预测(XGB) 异常(IF+规则) 策略/管家\n"
            "    └───────┬───────┘\n"
            "     React 可视化 + 三幕演示",
            st["code"],
        )
    )
    story.append(Spacer(1, 2 * mm))
    story.append(
        p(
            "前端 React+TS+Vite+Ant Design+ECharts；后端 FastAPI+SQLAlchemy；"
            "AI 为 XGBoost / IsolationForest / RandomForest；默认 SQLite。",
            st["body"],
        )
    )
    story.append(p("5.2 两户数据设计", st["h2"]))
    story.append(
        table(
            [
                ["户", "用途", "说明"],
                ["演示户 user_id=1", "现场主演示", "完整四路；稳定复现 03:17"],
                ["验证户 user_id=2", "迁移与诚实对照", "公开负荷或插座导出；缺占用摘特征；预测变差为预期"],
            ],
            [40 * mm, 40 * mm, 94 * mm],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(p("5.3 关键实验指标（以 models/metrics.json 2026-08-23 为准）", st["h2"]))
    story.append(
        table(
            [
                ["实验", "关键指标", "说明"],
                ["预测·演示户", "MAPE 20.34% · R² 0.9369\nMAE 110.76 W · RMSE 234.51 W", "对照昨天 23.01%；周均值 55.36%"],
                ["预测·验证户", "MAPE 25.09% · R² 0.8922", "周均值 MAPE 23.95% 优于模型"],
                ["异常·演示户", "P 0.26 · R 0.54 · F1 0.35", "标注 13 / 检出 27"],
                ["负荷识别", "Acc 0.9513 · macro-F1 0.9515", "有标签窗口；非 NILM"],
                ["策略结构", "今日约 18.73 kWh", "Top：空调 24→26℃"],
            ],
            [32 * mm, 70 * mm, 72 * mm],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(p("5.4 实现流程", st["h2"]))
    story.append(
        p(
            "generate_demo_data → init_db → train_models 落盘 → 启动 uvicorn:8000 与 Vite:5174 →"
            "浏览器打开 http://127.0.0.1:5174/（勿用 localhost IPv6）。改 Python 后须重启后端。",
            st["body"],
        )
    )

    # 6
    story.append(p("6. 应用场景示例", st["h1"]))
    scenes = [
        (
            "场景 A · 工作日晚高峰 20:30",
            "打开总览看到空调占比与高峰电价；策略建议空调升至 26℃；管家执行后对比电费。",
        ),
        (
            "场景 B · 凌晨异常 03:17",
            "异常解释器标出热水器非常规启动：功率←插座，占用低←门磁/作息，时段←时钟。",
        ),
        (
            "场景 C · 出门与安全底线",
            "「我出门了」关非刚需；「关掉冰箱」被拒绝，食品安全硬约束。",
        ),
        (
            "场景 D · 电网削峰邀约",
            "生活系统应下削峰邀约，按节能方案执行，演示家庭侧需求响应。",
        ),
        (
            "场景 E · 换户 / 接传感",
            "plug.csv / env.csv 导入验证户；缺占用降级，不在页面假装精度不变。",
        ),
    ]
    for title, body in scenes:
        block = [p(title, st["h2"]), p(body, st["body"])]
        story.append(KeepTogether(block))

    # 7
    story.append(p("7. 产品边界与诚实声明", st["h1"]))
    story.append(
        bullets(
            [
                "四路均为传感时序，不是图像或语音",
                "演示含过程模型；未灌真实 CSV 时勿宣称已接真实家庭电表",
                "负荷识别 ≠ 总表 NILM",
                "异常 F1=0.35，上线以规则为准",
                "预测不用 100−MAPE 报准确率；不对标虚构全市平均",
                "管家为模拟控制，不改历史曲线，不接真插座",
            ],
            st,
        )
    )

    # 8
    story.append(p("8. 快速上手（评审）", st["h1"]))
    story.append(
        bullets(
            [
                "按仓库 README 启动后端 8000 与前端 5174",
                "浏览器必须使用 http://127.0.0.1:5174/",
                "点「3 分钟演示」锁定演示户并静音",
                "三幕：总览回放 → 异常 03:17 → 策略 24→26℃ + 管家 / 拒关冰箱",
                "追问数据：打开「数据来源」「模型实验舱」",
            ],
            st,
        )
    )

    # 9
    story.append(p("9. 团队", st["h1"]))
    story.append(
        table(
            [
                ["成员", "负责"],
                ["蔡华升", "产品 / 前端；演示 / 材料"],
                ["何鹏", "后端 / 数据；AI / 实验"],
            ],
            [50 * mm, 124 * mm],
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(p("本说明书不含指导教师、专利、合同、论文信息。数值以 models/metrics.json 为准。", st["small"]))

    def first_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(DARK)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        canvas.setFillColor(GREEN)
        canvas.rect(0, 0, 8, A4[1], fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("CN", 36)
        canvas.drawCentredString(A4[0] / 2, A4[1] / 2 + 40, "智家能")
        canvas.setFont("CN", 18)
        canvas.setFillColor(colors.HexColor("#bbf7d0"))
        canvas.drawCentredString(A4[0] / 2, A4[1] / 2 + 8, "产品说明书")
        canvas.setFont("CN", 12)
        canvas.setFillColor(colors.HexColor("#f59e0b"))
        canvas.drawCentredString(A4[0] / 2, A4[1] / 2 - 28, "今晚该关什么")
        canvas.setFont("CN", 9)
        canvas.setFillColor(colors.HexColor("#9eccb8"))
        canvas.drawCentredString(A4[0] / 2, 48 * mm, "产品实现方向 · PDF")
        canvas.drawCentredString(A4[0] / 2, 40 * mm, "metrics.json · 2026-08-23")
        canvas.drawCentredString(A4[0] / 2, 32 * mm, "蔡华升 · 何鹏")
        canvas.restoreState()

    # Rebuild story: real cover page + content (skip the table cover we added)
    content = story[story.index(next(x for x in story if isinstance(x, PageBreak))) + 1 :]
    # Actually simpler: build fresh
    story2 = [Spacer(1, 1)]  # placeholder consumed on cover-only first page approach

    # Use two-pass: page 1 cover drawn in onFirstPage, story starts with content
    story_final = []
    story_final.append(p("目录", st["h1"]))
    story_final.append(
        bullets(
            [
                "1 产品概述",
                "2 目标用户",
                "3 核心功能",
                "4 AI 的角色与价值",
                "5 技术实现思路",
                "6 应用场景示例",
                "7 产品边界与诚实声明",
                "8 快速上手",
                "9 团队",
            ],
            st,
        )
    )
    story_final.append(PageBreak())
    # Reuse content after first PageBreak from story - find content starting at "1. 产品概述"
    # Easier: just rebuild content sections without the messy cover table
    story_final.extend(
        [
            x
            for x in story
            if not (
                isinstance(x, Table)
                and getattr(x, "_argW", None)
                and len(getattr(x, "_argW", [])) == 1
                and abs(x._argW[0] - 174 * mm) < 1
            )
        ]
    )
    # The above may still include early cover paragraphs. Clean approach: rewrite build without dual cover.

    doc.build(story_final, onFirstPage=first_page, onLaterPages=add_page_number)
    return out


def write_aux_pack() -> Path:
    if AUX.exists():
        shutil.rmtree(AUX)
    AUX.mkdir(parents=True)

    (AUX / "00_目录与说明.md").write_text(
        """# 产品实现方向——其他辅助材料

本目录对应赛事「其他辅助材料」：可运行 Demo、代码仓库、原型说明、流程图等。

| 文件 | 内容 |
| --- | --- |
| 01_代码仓库与体验入口.txt | GitHub 地址与本地演示 URL |
| 02_本地可运行Demo启动说明.md | Windows 启动步骤 |
| 03_产品流程图.md | 感知→决策→执行主流程 |
| 04_可点击原型页面地图.md | 前端路由与演示路径 |
| 05_技术架构摘要.md | 架构与技术栈 |
| 06_传感数据合同摘要.md | 四路传感与两户边界 |
| 07_实验指标摘要.md | 落盘指标速查 |

正式提交可将本目录打成 ZIP：`产品实现方向_其他辅助材料_智家能.zip`。
""",
        encoding="utf-8",
    )

    (AUX / "01_代码仓库与体验入口.txt").write_text(
        """智家能 · 代码仓库与体验入口

1) 代码仓库（公开）
https://github.com/xiaohe-4/Smart-Home-Assistant

2) 本地可运行 Demo（需按启动说明起服务）
前端：http://127.0.0.1:5174/
后端 API 文档：http://127.0.0.1:8000/docs
使用说明页：http://127.0.0.1:5174/guide

重要：请使用 127.0.0.1，不要用 localhost（避免 IPv6 导致语音/部分接口异常）。
演示默认无需登录；演示户 user_id=1，演示日 2026-08-19 20:30。
""",
        encoding="utf-8",
    )

    (AUX / "02_本地可运行Demo启动说明.md").write_text(
        """# 本地可运行 Demo 启动说明（Windows）

## 环境

- Python 3.10+（项目含 `.venv` 时可直接用）
- Node.js 18+（前端）

## 步骤

在项目根目录 `智家能/`：

```powershell
# 依赖（若尚未安装）
.\\.venv\\Scripts\\python.exe -m pip install -r backend\\requirements.txt

# 数据与模型（若库已有可跳过）
.\\.venv\\Scripts\\python.exe scripts\\generate_demo_data.py
.\\.venv\\Scripts\\python.exe scripts\\init_db.py
.\\.venv\\Scripts\\python.exe scripts\\train_models.py

# 后端（新终端）
$env:PYTHONPATH = "$pwd\\backend;$pwd"
.\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000

# 前端（新终端）
cd frontend
npm install
npm run dev
```

打开：http://127.0.0.1:5174/

点右下角「3 分钟演示」可锁定演示户并静音。

改 Python 代码后必须重启 uvicorn。
""",
        encoding="utf-8",
    )

    (AUX / "03_产品流程图.md").write_text(
        """# 产品主流程

## 业务闭环

```text
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│ 1 看懂为何贵  │ →  │ 2 查清哪笔浪费│ →  │ 3 今晚关哪一档│
│ 总览回放     │    │ 异常解释器   │    │ 策略 + 管家  │
└──────────────┘    └──────────────┘    └──────────────┘
```

## 数据与模型流

```text
电力 / 温湿度 / 占用 / 天气
        │
        ▼
  重采样对齐到 5 分钟合同（缺一路 → 降级）
        │
        ▼
  ┌─────┴─────┬────────────┐
  ▼           ▼            ▼
XGBoost预测  IF打分+规则   分路汇总/可选负荷识别
  │           │            │
  └─────┬─────┴────────────┘
        ▼
  多目标策略引擎 → 管家模拟执行 → 生活系统反馈
        │
        ▼
  指标落盘 models/metrics.json（实验舱可核对）
```

## 现场 150 秒三幕

1. `/` 回放到 20:30  
2. `/anomaly` 看 03:17 热水器，口述 F1=0.35  
3. `/strategy` 24→26℃ → `/butler` 点头；试关冰箱被拒  
""",
        encoding="utf-8",
    )

    (AUX / "04_可点击原型页面地图.md").write_text(
        """# 可点击原型 · 页面地图

本地前端即高保真可点击原型（React）。

| 页面 | 路由 | 演示要点 |
| --- | --- | --- |
| 智能总览 | `/` | 回放、KPI、四路对齐、今晚怎么做 |
| 能耗分析 | `/energy` | 分路占比（非 NILM） |
| 家庭设备 | `/devices` | 单设备曲线 |
| 能耗预测 | `/prediction` | MAE/RMSE/MAPE/R² 带宽 |
| 异常解释器 | `/anomaly` | 03:17 规则归因；F1=0.35 |
| AI 节能建议 | `/strategy` | 24→26℃ 对比 |
| 管家宝强 | `/butler` | 执行 / 拒关冰箱 |
| 生活系统 | `/life` | 电价时钟、邀约、任务 |
| 数据来源 | `/sources` | 传感合同、两户对照 |
| 模型实验 | `/models` | 落盘指标、周均值对照 |
| 家庭能源画像 | `/profile` | 能效分与潜力 |
| 使用说明 | `/guide` | 三幕上手与 FAQ |
| 能源助手 | `/assistant` | 解释已算结果 |

推荐点击路径：`/` → `/anomaly` → `/strategy` → `/butler` → `/sources` → `/models`。
""",
        encoding="utf-8",
    )

    (AUX / "05_技术架构摘要.md").write_text(
        (ROOT / "docs" / "技术架构.md").read_text(encoding="utf-8")
        if (ROOT / "docs" / "技术架构.md").exists()
        else "# 技术架构\n见仓库 docs/技术架构.md\n",
        encoding="utf-8",
    )

    (AUX / "06_传感数据合同摘要.md").write_text(
        """# 传感数据合同摘要

## 四路（均为时序，不是图像）

| 模态 | 作用 | 是否进预测模型 |
| --- | --- | --- |
| 电力（分路/总功率） | 用电主信号 | 是（滞后与滚动特征） |
| 室内温湿度 | 环境驱动 | 有则进；验证户可降级 |
| 占用 | 人在/人走 | 有则进；验证户常摘掉 |
| 天气（室外） | 解释与展示 | 默认不进模型 |

对齐合同：异构采样重采样到 **5 分钟**；缺一路降级，不崩溃。

## 两户

- **演示户**：过程模型完整四路，服务现场 03:17 叙事。  
- **验证户**：`data/raw/real_home_01/` + `scripts/import_real_home.py`；可为公开负荷重建或真实插座/DHT 导出。

未灌真实 CSV 前，答辩不得说「已接真实家庭电表」。
""",
        encoding="utf-8",
    )

    (AUX / "07_实验指标摘要.md").write_text(
        """# 实验指标摘要（对外唯一口径）

来源：`models/metrics.json`，generated_at = 2026-08-23T17:26:21

## 能耗预测

| | 演示户 | 验证户 |
| --- | --- | --- |
| MAPE | 20.34% | 25.09% |
| R² | 0.9369 | 0.8922 |
| MAE | 110.76 W | 55.92 W |
| 周均值 MAPE | 55.36% | **23.95%（优于模型）** |

## 异常（演示户）

Precision 0.2593 · Recall 0.5385 · F1 **0.35** · 标注 13 / 检出 27

## 负荷识别

Accuracy 0.9513 · macro-F1 0.9515（有标签窗口，不是 NILM；验证户不适用）

禁止再报：准确率 82.48%、R² 0.9525（那是 8/19 旧版）。
""",
        encoding="utf-8",
    )

    # copy product manual md into aux for convenience
    src_md = MAT / "产品实现方向_产品说明书_智家能.md"
    if src_md.exists():
        shutil.copy2(src_md, AUX / "产品说明书_文本源.md")

    zpath = MAT / "产品实现方向_其他辅助材料_智家能.zip"
    if zpath.exists():
        zpath.unlink()
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in AUX.rglob("*"):
            if p.is_file():
                zf.write(p, p.relative_to(AUX.parent))
    return zpath


def rewrite_manual_pdf() -> Path:
    """Clean rebuild of the product manual PDF."""
    register_fonts()
    st = styles()
    out = MAT / "产品实现方向_产品说明书_智家能.pdf"

    story: list = []
    story.append(p("目录", st["h1"]))
    story.append(
        bullets(
            [
                "1 产品概述",
                "2 目标用户",
                "3 核心功能",
                "4 AI 的角色与价值",
                "5 技术实现思路",
                "6 应用场景示例",
                "7 产品边界与诚实声明",
                "8 快速上手",
                "9 团队",
            ],
            st,
        )
    )
    story.append(PageBreak())

    story.append(p("1. 产品概述", st["h1"]))
    story.append(
        p(
            "智家能是面向普通家庭的多模态能源决策系统。以电力、室内温湿度、占用、天气四路传感时序为输入，"
            "经对齐、预测、异常解释、策略与执行，形成「看懂 → 查清 → 去办」的闭环。",
            st["body"],
        )
    )
    story.append(
        bullets(
            [
                "为什么贵：今日电量、峰谷结构、第一耗电设备",
                "哪笔浪费：凌晨异常、低占用高功率等，规则归因",
                "今晚关哪一档：可勾选策略 + 管家宝强模拟执行与电费对比",
            ],
            st,
        )
    )
    story.append(
        p(
            "演示家庭：成都四口之家 · 夏季 · 约 30 天 · 时刻锁定 2026-08-19 20:30。"
            "演示户保证现场可复现；验证户证明导入与缺模态降级能力。",
            st["body"],
        )
    )

    story.append(p("2. 目标用户", st["h1"]))
    story.append(
        table(
            [
                ["用户", "痛点", "产品如何帮到"],
                ["城市家庭住户", "账单难懂、不知今晚改什么", "总览回放 + 执行单 + 管家一句话"],
                ["宿舍 / 合租", "待机与异常浪费看不见", "异常解释器按规则归因"],
                ["能源服务 / 物业演示", "需要可移植决策内核", "标准表灌库 + 缺模态降级 + 验证户导入"],
                ["技术评审", "要看真实指标与边界", "实验舱落盘指标；F1 主动展示"],
            ],
            [32 * mm, 55 * mm, 87 * mm],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(p("非目标：不替代缴费电表；不做无标签总表 NILM；现场不控制真实物理插座。", st["small"]))

    story.append(p("3. 核心功能", st["h1"]))
    for title, body in [
        ("3.1 智能总览", "今日用电、电费、能源评分、第一耗电设备；24 小时功率回放；四路对齐：室内温度进模型，室外天气不进，光照与 CO₂ 只解释。"),
        ("3.2 能耗分析与设备", "分路电量占比（演示日空调约 41%、热水器约 22%、冰箱约 12%）。占比来自分路汇总，不是总表盲拆。"),
        ("3.3 能耗预测", "XGBoost 递推未来 6/24 小时；绿色带宽=真实 RMSE。只报 MAE/RMSE/MAPE/R²，并对照昨天同时段与近 7 日同时段平均。禁止用 100−MAPE 当准确率。"),
        ("3.4 异常解释器", "主规则 + Isolation Forest 打分。演示户 03:17 热水器可回放归因。F1=0.35（标注 13/检出 27）主动展示，结论以规则为准，不做自动断电。"),
        ("3.5 AI 节能建议", "多目标策略。Top：空调 24℃→26℃。同屏对比电量/电费/碳排/削峰；节能量按本户今日电量估算。"),
        ("3.6 管家宝强与生活系统", "白话指令与点头确认；模拟控制不改历史；拒绝关冰箱。生活系统含电价时钟、今晚任务、削峰邀约、谷电预约。"),
        ("3.7 数据来源与模型实验舱", "传感合同表；缺一路降级。实验舱并排演示/验证指标；验证户周均值优于模型时诚实提示。"),
    ]:
        story.append(p(title, st["h2"]))
        story.append(p(body, st["body"]))

    story.append(p("4. AI 的角色与价值", st["h1"]))
    story.append(
        p(
            "AI 不是聊天报分，而是可落盘复现的预测、打分与分类模块，与规则引擎分工："
            "模型给能力与不确定性，规则给可执行结论与安全底线。",
            st["body"],
        )
    )
    story.append(
        table(
            [
                ["模块", "方法", "角色", "价值边界"],
                ["能耗预测", "XGBoost / TimeSeriesSplit", "预判今晚/明天负荷", "只报落盘指标；带宽≠保证"],
                ["异常检测", "IF + 规则", "IF 打分；规则归因", "F1=0.35；上线以规则为准"],
                ["负荷识别", "RF 有标签 1h 窗", "有分路时的窗分类", "不是总表 NILM"],
                ["节能策略", "规则多目标", "生成今晚动作并模拟", "按本户估算，不空头承诺"],
                ["管家/助手", "规则意图", "把建议变成动作", "大模型不算指标；模拟控制"],
            ],
            [28 * mm, 42 * mm, 42 * mm, 62 * mm],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        p(
            "<b>AI 价值一句话：</b>把「看不懂的度」变成「说得清的原因」和「今晚可执行的一档」，并用可复现实验同时展示能力与短板。",
            st["body"],
        )
    )

    story.append(p("5. 技术实现思路", st["h1"]))
    story.append(p("5.1 架构与技术栈", st["h2"]))
    story.append(
        Preformatted(
            "传感四路 -> 5分钟对齐/缺模态降级 -> SQLite\n"
            "              |\n"
            "       FastAPI 业务服务\n"
            "    +-------+-------+-------+\n"
            " 预测(XGB) 异常(IF+规则) 策略/管家\n"
            "    +-------+-------+-------+\n"
            "     React 可视化 + 三幕演示",
            st["code"],
        )
    )
    story.append(Spacer(1, 2 * mm))
    story.append(
        p(
            "前端 React+TS+Vite+Ant Design+ECharts；后端 FastAPI+SQLAlchemy；"
            "AI 为 XGBoost / IsolationForest / RandomForest；默认 SQLite。",
            st["body"],
        )
    )
    story.append(p("5.2 两户数据设计", st["h2"]))
    story.append(
        table(
            [
                ["户", "用途", "说明"],
                ["演示户 user_id=1", "现场主演示", "完整四路；稳定复现 03:17"],
                ["验证户 user_id=2", "迁移与诚实对照", "公开负荷或插座导出；缺占用摘特征；预测变差为预期"],
            ],
            [40 * mm, 40 * mm, 94 * mm],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(p("5.3 关键实验指标（models/metrics.json · 2026-08-23）", st["h2"]))
    story.append(
        table(
            [
                ["实验", "关键指标", "说明"],
                ["预测·演示户", "MAPE 20.34% · R² 0.9369 · MAE 110.76 W", "昨天同时段 23.01%；周均值 55.36%"],
                ["预测·验证户", "MAPE 25.09% · R² 0.8922", "周均值 MAPE 23.95% 优于模型"],
                ["异常·演示户", "P 0.26 · R 0.54 · F1 0.35", "标注 13 / 检出 27"],
                ["负荷识别", "Acc 0.9513 · macro-F1 0.9515", "有标签窗口；非 NILM"],
                ["策略结构", "今日约 18.73 kWh", "Top：空调 24→26℃"],
            ],
            [32 * mm, 72 * mm, 70 * mm],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(p("5.4 实现流程", st["h2"]))
    story.append(
        p(
            "generate_demo_data → init_db → train_models 落盘 → 启动 uvicorn:8000 与 Vite:5174 →"
            "打开 http://127.0.0.1:5174/（勿用 localhost）。改 Python 后须重启后端。",
            st["body"],
        )
    )

    story.append(p("6. 应用场景示例", st["h1"]))
    for title, body in [
        ("场景 A · 工作日晚高峰 20:30", "打开总览看到空调占比与高峰电价；策略建议空调升至 26℃；管家执行后对比电费。"),
        ("场景 B · 凌晨异常 03:17", "异常解释器标出热水器非常规启动：功率←插座，占用低←门磁/作息，时段←时钟。"),
        ("场景 C · 出门与安全底线", "「我出门了」关非刚需；「关掉冰箱」被拒绝，食品安全硬约束。"),
        ("场景 D · 电网削峰邀约", "生活系统应下削峰邀约，按节能方案执行，演示家庭侧需求响应。"),
        ("场景 E · 换户 / 接传感", "plug.csv / env.csv 导入验证户；缺占用降级，不在页面假装精度不变。"),
    ]:
        story.append(KeepTogether([p(title, st["h2"]), p(body, st["body"])]))

    story.append(p("7. 产品边界与诚实声明", st["h1"]))
    story.append(
        bullets(
            [
                "四路均为传感时序，不是图像或语音",
                "演示含过程模型；未灌真实 CSV 时勿宣称已接真实家庭电表",
                "负荷识别 ≠ 总表 NILM",
                "异常 F1=0.35，上线以规则为准",
                "预测不用 100−MAPE 报准确率；不对标虚构全市平均",
                "管家为模拟控制，不改历史曲线，不接真插座",
            ],
            st,
        )
    )

    story.append(p("8. 快速上手（评审）", st["h1"]))
    story.append(
        bullets(
            [
                "按仓库 README 启动后端 8000 与前端 5174",
                "浏览器必须使用 http://127.0.0.1:5174/",
                "点「3 分钟演示」锁定演示户并静音",
                "三幕：总览回放 → 异常 03:17 → 策略 24→26℃ + 管家 / 拒关冰箱",
                "追问数据：打开「数据来源」「模型实验舱」",
            ],
            st,
        )
    )

    story.append(p("9. 团队", st["h1"]))
    story.append(
        table(
            [["成员", "负责"], ["蔡华升", "产品 / 前端；演示 / 材料"], ["何鹏", "后端 / 数据；AI / 实验"]],
            [50 * mm, 124 * mm],
        )
    )
    story.append(Spacer(1, 4 * mm))
    story.append(p("本说明书不含指导教师、专利、合同、论文信息。数值以 models/metrics.json 为准。", st["small"]))

    def first_page(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(DARK)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
        canvas.setFillColor(GREEN)
        canvas.rect(0, 0, 8, A4[1], fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("CN", 36)
        canvas.drawCentredString(A4[0] / 2, A4[1] / 2 + 44, "智家能")
        canvas.setFont("CN", 18)
        canvas.setFillColor(colors.HexColor("#bbf7d0"))
        canvas.drawCentredString(A4[0] / 2, A4[1] / 2 + 10, "产品说明书")
        canvas.setFont("CN", 12)
        canvas.setFillColor(colors.HexColor("#f59e0b"))
        canvas.drawCentredString(A4[0] / 2, A4[1] / 2 - 24, "今晚该关什么")
        canvas.setFont("CN", 9)
        canvas.setFillColor(colors.HexColor("#9eccb8"))
        canvas.drawCentredString(A4[0] / 2, 52 * mm, "产品实现方向 · 提交用 PDF")
        canvas.drawCentredString(A4[0] / 2, 44 * mm, "基于多模态家庭数据分析的 AI 能源管理与节能决策系统")
        canvas.drawCentredString(A4[0] / 2, 36 * mm, "指标口径 models/metrics.json · 2026-08-23")
        canvas.drawCentredString(A4[0] / 2, 28 * mm, "团队：蔡华升 · 何鹏")
        canvas.restoreState()

    doc = SimpleDocTemplate(
        str(out),
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=16 * mm,
        title="智家能·产品说明书",
        author="智家能团队",
    )
    doc.build(story, onFirstPage=first_page, onLaterPages=add_page_number)
    return out


def write_checklist(manual: Path, zpath: Path):
    def mb(p: Path) -> str:
        return f"{p.stat().st_size / 1024 / 1024:.2f} MB" if p.exists() else "缺失"

    text = f"""# 新材料要求 · 提交清单

依据：`新材料要求/要求.md`

## 1. 产品实现方向——产品说明书（必交）

| 项 | 文件 | 状态 |
| --- | --- | --- |
| PDF | `{manual.name}` | 已生成（{mb(manual)}） |
| 文本源 | `产品实现方向_产品说明书_智家能.md` | 已写好 |

覆盖要求：产品概述、目标用户、核心功能、AI 的角色与价值、技术实现思路、应用场景示例。

## 2. 产品实现方向——其他辅助材料

| 项 | 文件 | 状态 |
| --- | --- | --- |
| ZIP 包 | `{zpath.name}` | 已打包（{mb(zpath)}） |
| 展开目录 | `产品实现方向_其他辅助材料/` | 含仓库、Demo 启动、流程图、原型地图、指标摘要 |

已包含：可运行 Demo 说明、代码仓库链接、可点击原型页面地图、流程图、技术架构与传感合同摘要。

## 口径

- 指标：`models/metrics.json`（2026-08-23）演示户 MAPE 20.34% / R² 0.9369
- 团队姓名：蔡华升、何鹏
- 仓库：https://github.com/xiaohe-4/Smart-Home-Assistant

## 重新生成

```powershell
.\\.venv\\Scripts\\python.exe 材料\\build_product_manual.py
```
"""
    (MAT / "00_新材料要求_提交清单.md").write_text(text, encoding="utf-8")


def main():
    manual = rewrite_manual_pdf()
    zpath = write_aux_pack()
    # also put pdf into aux and re-zip? keep separate as requirement splits 说明书 vs 辅助
    write_checklist(manual, zpath)
    print("manual", manual, manual.stat().st_size)
    print("aux_zip", zpath, zpath.stat().st_size)


if __name__ == "__main__":
    main()
