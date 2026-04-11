"""Generate viz3-crossmarket.png — Sharpe ratio + Max Drawdown comparison.
US period = 5 years (2013-2018) | A-share period = 11 years (2015-2026)
Sharpe ratio and Max Drawdown are time-normalized metrics."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

OUT = "/Users/rayzhang/Downloads/stock-visualization/docs/img/viz3-crossmarket.png"

# Numbers from backtest
labels = ["B1\nUS (5yr)", "B1\nA-share (11yr)", "B2\nUS (5yr)", "B2\nA-share (11yr)"]
sharpe = [1.03, 1.59, 0.41, 1.60]
maxdd = [-23.8, -8.0, -21.6, -12.0]

fig, axs = plt.subplots(1, 2, figsize=(13, 6))
fig.patch.set_facecolor('white')

x = np.arange(len(labels))
width = 0.55
us_color = '#3b82f6'
cn_color = '#22c55e'
bar_colors = [us_color if i % 2 == 0 else cn_color for i in range(4)]

for ax in axs:
    ax.set_facecolor('white')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(axis='y', color='#f5f5f5', linewidth=0.5)

# Left: Sharpe Ratio
ax1 = axs[0]
bars1 = ax1.bar(x, sharpe, width, color=bar_colors, edgecolor='none')
ax1.axhline(y=1.0, color='#9ca3af', linestyle='--', linewidth=1, alpha=0.6)
ax1.set_xticks(x)
ax1.set_xticklabels(labels, fontsize=10, color='#374151')
ax1.set_ylabel('Sharpe Ratio', fontsize=12, color='#374151')
ax1.set_title('Sharpe Ratio\nHigher = Better', fontsize=12, fontweight='bold',
              color='#1a1a2e', pad=8)
ax1.set_ylim(0, 2.2)
ax1.tick_params(colors='#374151')
for bar, val in zip(bars1, sharpe):
    ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.06,
             f'{val:.2f}', ha='center', va='bottom', fontsize=11, fontweight='bold', color='#1a1a2e')
# No y-axis tick labels overlap — just 0, 0.5, 1.0, 1.5, 2.0

# Right: Max Drawdown
ax2 = axs[1]
bars2 = ax2.bar(x, maxdd, width, color=bar_colors, edgecolor='none')
ax2.axhline(y=-10, color='#9ca3af', linestyle='--', linewidth=1, alpha=0.6)
ax2.set_xticks(x)
ax2.set_xticklabels(labels, fontsize=10, color='#374151')
ax2.set_ylabel('Max Drawdown (%)', fontsize=12, color='#374151')
ax2.set_title('Max Drawdown\nLess Negative = Better', fontsize=12, fontweight='bold',
              color='#1a1a2e', pad=8)
ax2.set_ylim(-26, 4)
ax2.tick_params(colors='#374151')
# Reduce tick count to prevent overlap
ax2.set_yticks([-25, -20, -15, -10, -5, 0])
for bar, val in zip(bars2, maxdd):
    label_y = bar.get_height() - 1.1
    ax2.text(bar.get_x() + bar.get_width()/2, label_y,
             f'{val:.1f}%', ha='center', va='bottom', fontsize=10, fontweight='bold', color='#1a1a2e')

# Legend: upper center below title
us_patch = mpatches.Patch(color=us_color, label='US (S&P 500)')
cn_patch = mpatches.Patch(color=cn_color, label='A-share (China)')
ax1.legend(handles=[us_patch, cn_patch], loc='lower center',
           bbox_to_anchor=(0.5, -0.22), ncol=2, fontsize=10, frameon=False)

# Note at very bottom
fig.text(0.5, 0.01,
         'US period = 5 years (2013–2018)  |  A-share period = 11 years (2015–2026)',
         ha='center', fontsize=9, color='#6b7280', style='italic')

# Use constrained_layout instead of tight_layout to control spacing
plt.subplots_adjust(bottom=0.18, hspace=0.3)
import os
plt.savefig(OUT, dpi=150, facecolor='white', pad_inches=0.15)
print(f"Saved {OUT} ({os.path.getsize(OUT)} bytes), h={fig.get_figheight()}in w={fig.get_figwidth()}in")