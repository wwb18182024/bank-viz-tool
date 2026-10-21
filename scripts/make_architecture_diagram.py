"""Generate the project architecture diagram for the Tracker PPT (slide 10)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

W, H = 16.0, 9.0
fig, ax = plt.subplots(figsize=(W, H), dpi=100)
ax.set_xlim(0, W)
ax.set_ylim(0, H)
ax.axis("off")
fig.patch.set_facecolor("white")

BLUE, BLUE_L = "#0C447C", "#E6F1FB"
PURPLE, PURPLE_L = "#3C3489", "#EEEDFE"
TEAL, TEAL_L = "#0F6E56", "#E1F5EE"
AMBER, AMBER_L = "#854F0B", "#FAEEDA"
GRAY = "#5F5E5A"


def box(x, y, w, h, title, lines, ec, fc, title_size=15, body_size=11.5):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.18",
                                linewidth=1.4, edgecolor=ec, facecolor=fc))
    ax.text(x + w / 2, y + h - 0.42, title, ha="center", va="center",
            fontsize=title_size, fontweight="bold", color=ec)
    ax.plot([x + 0.35, x + w - 0.35], [y + h - 0.72, y + h - 0.72], color=ec, lw=0.8, alpha=0.55)
    body = "\n".join(lines)
    ax.text(x + w / 2, y + (h - 0.95) / 2, body, ha="center", va="center",
            fontsize=body_size, color="#1C2333", linespacing=1.75)


def arrow(x1, y1, x2, y2, label=None, color=GRAY, ls="-", lx=None, ly=None, fs=10.5):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=22,
                                 linewidth=1.6, color=color, linestyle=ls, shrinkA=4, shrinkB=4))
    if label:
        ax.text(lx if lx is not None else (x1 + x2) / 2, ly if ly is not None else (y1 + y2) / 2 + 0.16,
                label, ha="center", va="bottom", fontsize=fs, color=color, style="italic")


ax.text(W / 2, H - 0.42, "BankViz — System Architecture (fully local, no external network)",
        ha="center", fontsize=17, fontweight="bold", color="#1C2333")

# Frontend
box(0.55, 1.7, 4.0, 5.6, "React Frontend (Vite)",
    ["Dataset upload & profile UI", "Auto-visualisation dashboard", "Manual chart builder",
     "ECharts rendering + PNG export"], BLUE, BLUE_L)

# Backend
box(6.1, 1.2, 5.6, 6.6, "FastAPI Backend (localhost:8000)",
    [], PURPLE, PURPLE_L)
bx, by, bw = 6.1, 1.2, 5.6
mods = [
    ("data_A · Metadata — types, ranges, missing, unique", 6.05),
    ("data_B · Chart library — 9 pre-coded chart types", 5.55),
    ("data_C · Processing — group, sum, mean, count, binning", 5.05),
    ("Plan schema + validator — JSON contract checks", 4.55),
    ("Domain-aware filter — 2-layer rules + theme ranking", 4.05),
    ("Plan executor — spec → ECharts option", 3.55),
    ("Fallback recommender — works when LLM offline", 3.05),
]
ax.text(bx + bw / 2, by + 6.6 - 0.42, "FastAPI Backend (localhost:8000)", ha="center",
        fontsize=15, fontweight="bold", color=PURPLE)
ax.plot([bx + 0.35, bx + bw - 0.35], [by + 6.6 - 0.72, by + 6.6 - 0.72], color=PURPLE, lw=0.8, alpha=0.55)
for t, y in mods:
    ax.add_patch(FancyBboxPatch((bx + 0.4, y), bw - 0.8, 0.38,
                                boxstyle="round,pad=0.02,rounding_size=0.08",
                                linewidth=0.8, edgecolor=PURPLE, facecolor="white"))
    ax.text(bx + bw / 2, y + 0.19, t, ha="center", va="center", fontsize=9.5, color="#1C2333")

# LLM
box(13.0, 3.3, 2.5, 2.6, "Ollama LLM",
    ["Qwen2.5 (local)", "localhost:11434", "open-source"], TEAL, TEAL_L)

# Session store chip
ax.add_patch(FancyBboxPatch((6.55, 1.45), 4.7, 0.5, boxstyle="round,pad=0.02,rounding_size=0.1",
                            linewidth=1.0, edgecolor=AMBER, facecolor=AMBER_L))
ax.text(8.9, 1.7, "In-memory session store — raw data never written to disk or cloud",
        ha="center", va="center", fontsize=10, color=AMBER, style="italic")

# Arrows
arrow(4.75, 4.5, 5.95, 4.5, "HTTP / JSON", BLUE, lx=5.35, ly=4.62)
arrow(11.95, 5.1, 12.9, 5.1, "metadata only", TEAL, lx=12.42, ly=5.22, fs=9)
arrow(12.9, 4.0, 11.95, 4.0, "JSON plan", TEAL, ls=(0, (4, 2)), lx=12.42, ly=3.42, fs=9)

# Privacy band
ax.add_patch(FancyBboxPatch((0.55, 0.35), 14.95, 0.6, boxstyle="round,pad=0.02,rounding_size=0.12",
                            linewidth=1.2, edgecolor=TEAL, facecolor=TEAL_L))
ax.text(3.0 + 2.5, 0.65, "Privacy: all computation local · LLM endpoint must be localhost (fail closed) · no login · no telemetry",
        ha="center", va="center", fontsize=11.5, color=TEAL, fontweight="bold")

ax.text(2.55, 0.05, "", fontsize=8)
plt.savefig(r"E:\bank-viz-tool\docs\architecture_diagram.png", bbox_inches="tight", facecolor="white")
print("saved")
