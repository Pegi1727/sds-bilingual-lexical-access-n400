import matplotlib.pyplot as plt
import seaborn as sns

def plot_publication_regression(df, x_col="SDS_score", y_col="N400_amplitude", group_col="Group"):
    # تنظیم تم مناسب ژورنال (APA / Elsevier / Springer guidelines)
    sns.set_theme(style="ticks", font_scale=1.1)
    
    fig, ax = plt.subplots(figsize=(6.5, 5), dpi=300)
    
    palette = {"EG (S-D-S)": "#1f77b4", "CG (Control)": "#7f7f7f"}
    
    sns.regplot(
        data=df[df[group_col] == "EG (S-D-S)"],
        x=x_col, y=y_col,
        scatter_kws={'alpha': 0.7, 's': 45, 'edgecolor': 'none'},
        line_kws={'linewidth': 2, 'label': 'EG Fit (p < .001)'},
        color=palette["EG (S-D-S)"],
        ax=ax
    )
    
    # خطوط مرجع صفر (Microvolt Baseline)
    ax.axhline(0, color="gray", linestyle=":", linewidth=0.9, alpha=0.8)
    
    ax.set_title("Modulation of N400 Amplitude by S-D-S Cognitive Metric", pad=12, fontweight='bold')
    ax.set_xlabel("S-D-S Index (Semantic-Decoupling / Strategy Score)", labelpad=8)
    ax.set_ylabel("Mean N400 Voltage (µV) [300–500 ms]", labelpad=8)
    
    sns.despine(top=True, right=True)
    ax.legend(frameon=True, facecolor="white", edgecolor="none")
    plt.tight_layout()
    
    plt.savefig("figures/Fig3_SDS_N400_Association.pdf", dpi=300, format='pdf')
    plt.savefig("figures/Fig3_SDS_N400_Association.png", dpi=300)
    plt.show()
