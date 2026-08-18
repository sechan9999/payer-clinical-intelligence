import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUTPUT_PNG = os.path.join("docs", "architecture_diagram.png")

def draw_architecture_diagram():
    fig, ax = plt.subplots(figsize=(16, 10), dpi=150)
    ax.set_facecolor('#0f172a')
    fig.patch.set_facecolor('#0f172a')
    ax.axis('off')

    # Title
    ax.text(0.5, 0.96, "Governed Payer Clinical Intelligence Fleet — System Architecture",
            ha='center', va='center', color='#38bdf8', fontsize=20, fontweight='bold')
    ax.text(0.5, 0.925, "Google ADK + Gemini 3.5 Flash + Server-Derived RBAC + Two-Stage SQL RAG + HTTP 409 Approval Gate",
            ha='center', va='center', color='#94a3b8', fontsize=12)

    # Box Helper Function
    def draw_box(x, y, w, h, title, subtitle, color, text_color='#ffffff'):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02",
                                     linewidth=2, edgecolor=color, facecolor='#1e293b')
        ax.add_patch(rect)
        ax.text(x + w/2, y + h*0.65, title, ha='center', va='center', color=color, fontsize=11, fontweight='bold')
        ax.text(x + w/2, y + h*0.35, subtitle, ha='center', va='center', color=text_color, fontsize=9)

    # Draw Nodes
    draw_box(0.05, 0.78, 0.22, 0.10, "Pub/Sub Event Stream", "CLAIM_DENIED Event Stream", '#38bdf8')
    draw_box(0.35, 0.78, 0.25, 0.10, "Server-Derived Identity", "X-Fleet-Token Header (app/identity.py)", '#a855f7')
    draw_box(0.68, 0.78, 0.25, 0.10, "Model Armor Guardrails", "Prompt Injection Interceptor (app/guardrails.py)", '#ef4444')

    draw_box(0.35, 0.58, 0.58, 0.12, "Governed Agent Fleet (Google ADK)", "Payer Intelligence Agent | Clinical & Growth Agent | Fleet Coordinator\nAutonomy Grade: drafts_only | read_only", '#38bdf8')

    draw_box(0.05, 0.35, 0.42, 0.15, "Two-Stage Retrieval Boundary", "Stage 1: SQL WHERE allowed_roles Filter (app/retrieval.py)\nStage 2: Vector Cosine Similarity Ranking (pgvector)", '#34d399')
    draw_box(0.53, 0.35, 0.42, 0.15, "Gemini 3.5 Flash (Vertex AI)", "google-genai SDK Model Inference\nMandatory Document Citation Tagging: [PAY-POL-101]", '#6366f1')

    draw_box(0.05, 0.10, 0.28, 0.16, "Isolated Human Approval Gate", "Pending Queue (app/approvals.py)\nDraft HL7 FHIR v4 Bundle", '#f97316')
    draw_box(0.37, 0.10, 0.26, 0.16, "Refusal Interception", "Premature Send Attempt\nHTTP 409 Conflict Refusal", '#ef4444')
    draw_box(0.67, 0.10, 0.28, 0.16, "Human Supervisor Dispatch", "Medical Director Sign-off\nHTTP 200 OK -> External Dispatch", '#34d399')

    # Arrows
    arrow_style = dict(arrowstyle="->", color='#38bdf8', lw=2)
    refusal_arrow = dict(arrowstyle="->", color='#ef4444', lw=2, ls='--')

    ax.annotate("", xy=(0.35, 0.83), xytext=(0.27, 0.83), arrowprops=arrow_style)
    ax.annotate("", xy=(0.68, 0.83), xytext=(0.60, 0.83), arrowprops=arrow_style)
    ax.annotate("", xy=(0.64, 0.70), xytext=(0.80, 0.78), arrowprops=arrow_style)

    ax.annotate("", xy=(0.26, 0.425), xytext=(0.40, 0.58), arrowprops=arrow_style)
    ax.annotate("", xy=(0.53, 0.425), xytext=(0.26, 0.425), arrowprops=arrow_style)
    ax.annotate("", xy=(0.64, 0.58), xytext=(0.64, 0.50), arrowprops=arrow_style)

    ax.annotate("", xy=(0.19, 0.26), xytext=(0.45, 0.58), arrowprops=arrow_style)
    ax.annotate("", xy=(0.37, 0.18), xytext=(0.33, 0.18), arrowprops=refusal_arrow)
    ax.annotate("", xy=(0.67, 0.18), xytext=(0.33, 0.18), arrowprops=arrow_style)

    plt.tight_layout()
    plt.savefig(OUTPUT_PNG, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print(f"[SUCCESS] Rendered architecture diagram PNG to: {os.path.abspath(OUTPUT_PNG)}")

if __name__ == "__main__":
    draw_architecture_diagram()
