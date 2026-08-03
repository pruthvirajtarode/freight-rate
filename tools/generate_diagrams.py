import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pathlib import Path

# Setup output dir
output_dir = Path("project/backend/charts")
output_dir.mkdir(parents=True, exist_ok=True)

plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#334155'

# -------------------------------------------------------------
# 1. SYSTEM ARCHITECTURE DIAGRAM
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
fig.patch.set_facecolor('#0F172A')
ax.set_facecolor('#0F172A')
ax.axis('off')

# Title
plt.title("FreightAI End-to-End System Architecture", fontsize=16, fontweight='bold', color='#F8FAFC', pad=25)

# Outer Bounding Box (Cloud / Host System)
outer = patches.FancyBboxPatch((0.5, 0.5), 11, 5.5, boxstyle="round,pad=0.2",
                            fc="#1E293B", ec="#4F46E5", lw=2, linestyle='--')
ax.add_patch(outer)
ax.text(1, 5.6, "Production Environment (FastAPI + SPA Stack)", color="#818CF8", fontsize=10, fontweight='bold')

# Nodes: (x, y, w, h, title, subtitle, icon/color)
nodes = [
    (1.0, 3.2, 2.0, 1.6, "Frontend SPA", "HTML5/CSS3/JS\n(Glassmorphism UI)", "#6366F1"),
    (3.6, 3.2, 2.0, 1.6, "API Gateway", "FastAPI Router\n(/api/v1/*)", "#0EA5E9"),
    (6.2, 3.8, 2.2, 1.4, "Data Pipeline", "Preprocessing &\n25 Feature Eng.", "#10B981"),
    (6.2, 1.6, 2.2, 1.4, "XAI Engine", "SHAP TreeExplainer\nAttribution", "#F59E0B"),
    (9.0, 2.7, 2.0, 1.8, "ML Core", "Optuna Tuned\nGradient Boosting\n(0.8507 R²)", "#8B5CF6")
]

for x, y, w, h, title, sub, col in nodes:
    box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15",
                                fc="#0F172A", ec=col, lw=2)
    ax.add_patch(box)
    # Header bar
    hbar = patches.FancyBboxPatch((x, y+h-0.35), w, 0.35, boxstyle="round,pad=0",
                                  fc=col, ec=col)
    ax.add_patch(hbar)
    ax.text(x + w/2, y + h - 0.2, title, color="#FFFFFF", fontsize=10, fontweight='bold', ha='center', va='center')
    ax.text(x + w/2, y + (h-0.35)/2, sub, color="#CBD5E1", fontsize=8.5, ha='center', va='center')

# Draw Arrows
arrow_style = dict(arrowstyle="->,head_width=0.4,head_length=0.6", color="#94A3B8", lw=2)

# Frontend -> API Gateway
ax.annotate("", xy=(3.55, 4.0), xytext=(3.05, 4.0), arrowprops=arrow_style)
# API Gateway -> Data Pipeline
ax.annotate("", xy=(6.15, 4.5), xytext=(5.65, 4.0), arrowprops=arrow_style)
# Data Pipeline -> ML Core
ax.annotate("", xy=(8.95, 4.0), xytext=(8.45, 4.5), arrowprops=arrow_style)
# ML Core -> XAI Engine
ax.annotate("", xy=(8.45, 2.3), xytext=(8.95, 3.2), arrowprops=arrow_style)
# XAI Engine -> API Gateway
ax.annotate("", xy=(5.65, 3.5), xytext=(6.15, 2.3), arrowprops=arrow_style)

ax.set_xlim(0, 12)
ax.set_ylim(0, 6.5)
plt.savefig(output_dir / "architecture_diagram.png", facecolor=fig.get_facecolor())
plt.close()


# -------------------------------------------------------------
# 2. USE CASE DIAGRAM
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
fig.patch.set_facecolor('#0F172A')
ax.set_facecolor('#0F172A')
ax.axis('off')

plt.title("FreightAI Platform Use Case Diagram", fontsize=16, fontweight='bold', color='#F8FAFC', pad=25)

# Bounding Box for System
sys_box = patches.FancyBboxPatch((3.2, 0.5), 7.2, 5.0, boxstyle="round,pad=0.2",
                               fc="#1E293B", ec="#334155", lw=2)
ax.add_patch(sys_box)
ax.text(3.5, 5.2, "FreightAI System Boundary", color="#818CF8", fontsize=10, fontweight='bold')

# Actor Node (Shipper / Broker)
actor_box = patches.FancyBboxPatch((0.5, 2.0), 2.0, 2.0, boxstyle="round,pad=0.15",
                                  fc="#4338CA", ec="#6366F1", lw=2)
ax.add_patch(actor_box)
ax.text(1.5, 3.2, "ACTOR", color="#A5B4FC", fontsize=9, fontweight='bold', ha='center')
ax.text(1.5, 2.7, "Shipper / Broker /\nLogistics Analyst", color="#FFFFFF", fontsize=10, fontweight='bold', ha='center')

# Use Cases (Ellipses / Rounded Boxes)
use_cases = [
    (4.0, 4.0, 5.5, 0.8, "UC-1: Instant Spot Freight Rate Prediction"),
    (4.0, 2.9, 5.5, 0.8, "UC-2: Automated Batch Load Board CSV Scoring"),
    (4.0, 1.8, 5.5, 0.8, "UC-3: Audit SHAP Explainability & Feature Drivers"),
    (4.0, 0.7, 5.5, 0.8, "UC-4: Analyze December Seasonal Rate Forecast")
]

for x, y, w, h, label in use_cases:
    uc = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.3",
                               fc="#0F172A", ec="#0EA5E9", lw=1.5)
    ax.add_patch(uc)
    ax.text(x + w/2, y + h/2, label, color="#F8FAFC", fontsize=9.5, fontweight='bold', ha='center', va='center')

    # Association Line from Actor
    ax.plot([2.55, x], [3.0, y + h/2], color="#64748B", lw=1.5, linestyle="-")

ax.set_xlim(0, 11)
ax.set_ylim(0, 6)
plt.savefig(output_dir / "use_case_diagram.png", facecolor=fig.get_facecolor())
plt.close()


# -------------------------------------------------------------
# 3. SEQUENCE DIAGRAM
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
fig.patch.set_facecolor('#0F172A')
ax.set_facecolor('#0F172A')
ax.axis('off')

plt.title("Single Prediction Execution Sequence Diagram", fontsize=16, fontweight='bold', color='#F8FAFC', pad=25)

# Lifelines
lifelines = [
    (1.5, "Client SPA"),
    (4.2, "FastAPI Router"),
    (7.0, "Feature Pipeline"),
    (9.8, "GradientBoosting Engine")
]

for x, name in lifelines:
    ax.plot([x, x], [0.8, 5.2], color="#334155", lw=2, linestyle="--")
    box = patches.FancyBboxPatch((x-1.0, 5.2), 2.0, 0.6, boxstyle="round,pad=0.1",
                                fc="#1E293B", ec="#6366F1", lw=1.5)
    ax.add_patch(box)
    ax.text(x, 5.5, name, color="#FFFFFF", fontsize=9.5, fontweight='bold', ha='center', va='center')

# Message Calls
messages = [
    (1.5, 4.2, 4.5, "1: POST /api/v1/predict/single", "#38BDF8", False),
    (4.2, 7.0, 3.7, "2: Transform Features & Impute", "#10B981", False),
    (7.0, 9.8, 2.9, "3: Model Inference & TreeExplainer", "#F59E0B", False),
    (9.8, 4.2, 2.1, "4: Return Predicted Rate & SHAP Values", "#8B5CF6", True),
    (4.2, 1.5, 1.3, "5: Render JSON Response & Waterfall UI", "#38BDF8", True)
]

for x1, x2, y, msg, col, is_return in messages:
    ls = "--" if is_return else "-"
    arr = "<-" if is_return else "->"
    ax.annotate("", xy=(x2, y), xytext=(x1, y),
                arrowprops=dict(arrowstyle=f"{arr},head_width=0.3,head_length=0.5", color=col, lw=1.8, linestyle=ls))
    ax.text((x1+x2)/2, y + 0.15, msg, color=col, fontsize=8.5, fontweight='bold', ha='center')

ax.set_xlim(0, 12)
ax.set_ylim(0, 6.5)
plt.savefig(output_dir / "sequence_diagram.png", facecolor=fig.get_facecolor())
plt.close()

print("All 3 diagram images generated successfully in project/backend/charts/")
