"""
Architecture diagram generator using matplotlib.
Creates architecture_diagram.png and component_diagram.png.

Student: Goutham Uppu (25167936)
Module: Cloud Platform Programming, NCI
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


def create_architecture_diagram():
    """Generate the cloud architecture diagram showing all 7 AWS services."""
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 10)
    ax.axis('off')
    ax.set_title('Freelancer Time Tracking & Invoice Generator\nCloud Architecture Diagram',
                 fontsize=16, fontweight='bold', pad=20)

    # Color scheme
    colors = {
        'client': '#4285F4',
        'api': '#0F9D58',
        'compute': '#F4B400',
        'database': '#DB4437',
        'storage': '#FF6D00',
        'auth': '#AB47BC',
        'monitor': '#00ACC1',
        'ml': '#E91E63',
    }

    def draw_box(x, y, w, h, label, sublabel, color, fontsize=10):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                             facecolor=color, edgecolor='white', alpha=0.9, linewidth=2)
        ax.add_patch(box)
        ax.text(x + w/2, y + h/2 + 0.15, label, ha='center', va='center',
                fontsize=fontsize, fontweight='bold', color='white')
        ax.text(x + w/2, y + h/2 - 0.2, sublabel, ha='center', va='center',
                fontsize=7, color='white', alpha=0.9)

    def draw_arrow(x1, y1, x2, y2, label=''):
        ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle='->', color='#555', lw=1.5))
        if label:
            mx, my = (x1+x2)/2, (y1+y2)/2
            ax.text(mx, my+0.15, label, ha='center', va='bottom', fontsize=7, color='#555')

    # Client Layer
    draw_box(5.5, 8.5, 3, 0.9, 'React Frontend', 'Web Browser (SPA)', colors['client'])

    # API Layer
    draw_box(1, 6.5, 3, 0.9, 'API Gateway', 'REST API Endpoints', colors['api'])
    draw_box(5.5, 6.5, 3, 0.9, 'Flask Backend', 'Application Server', colors['api'])
    draw_box(10, 6.5, 3, 0.9, 'Cognito', 'Authentication', colors['auth'])

    # Compute Layer
    draw_box(1, 4.5, 3, 0.9, 'Lambda', 'Invoice Generation', colors['compute'])
    draw_box(5.5, 4.5, 3, 0.9, 'invoicegen Library', 'Custom OOP Library', colors['compute'])

    # Data Layer
    draw_box(1, 2.5, 3, 0.9, 'DynamoDB', 'NoSQL Database', colors['database'])
    draw_box(5.5, 2.5, 3, 0.9, 'S3', 'PDF Storage', colors['storage'])

    # Monitoring Layer
    draw_box(10, 4.5, 3, 0.9, 'CloudWatch', 'Monitoring & Alerts', colors['monitor'])
    draw_box(10, 2.5, 3, 0.9, 'Textract', 'Receipt OCR', colors['ml'])

    # Arrows
    draw_arrow(7, 8.5, 7, 7.4, 'HTTP')
    draw_arrow(5.5, 6.9, 4, 6.9, 'Route')
    draw_arrow(8.5, 6.9, 10, 6.9, 'Auth')
    draw_arrow(7, 6.5, 7, 5.4, 'Uses')
    draw_arrow(2.5, 6.5, 2.5, 5.4, 'Invoke')
    draw_arrow(2.5, 4.5, 2.5, 3.4, 'Query')
    draw_arrow(5.5, 4.9, 4, 4.9, 'Build')
    draw_arrow(7, 4.5, 7, 3.4, 'Store')
    draw_arrow(8.5, 5.0, 10, 5.0, 'Metrics')
    draw_arrow(10, 3.4, 8.5, 4.5, 'OCR Data')

    # Legend
    ax.text(0.5, 1.2, 'Student: Goutham Uppu (25167936) | Module: Cloud Platform Programming | NCI',
            fontsize=9, color='#666')
    ax.text(0.5, 0.7, 'AWS Services: DynamoDB, S3, Lambda, API Gateway, Cognito, CloudWatch, Textract',
            fontsize=8, color='#888')

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'architecture_diagram.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"Saved: {path}")
    return path


def create_component_diagram():
    """Generate the component/module diagram."""
    fig, ax = plt.subplots(1, 1, figsize=(14, 9))
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 9)
    ax.axis('off')
    ax.set_title('Freelancer Time Tracking & Invoice Generator\nComponent Diagram',
                 fontsize=16, fontweight='bold', pad=20)

    colors = {
        'frontend': '#4285F4',
        'backend': '#0F9D58',
        'library': '#F4B400',
        'service': '#DB4437',
        'data': '#FF6D00',
    }

    def draw_component(x, y, w, h, title, items, color):
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                             facecolor=color, edgecolor='white', alpha=0.15, linewidth=2)
        ax.add_patch(box)
        border = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                                facecolor='none', edgecolor=color, alpha=0.8, linewidth=2)
        ax.add_patch(border)
        ax.text(x + w/2, y + h - 0.2, title, ha='center', va='top',
                fontsize=11, fontweight='bold', color=color)
        for i, item in enumerate(items):
            ax.text(x + 0.3, y + h - 0.6 - i*0.3, f"- {item}",
                    fontsize=8, color='#333')

    # Frontend Components
    draw_component(0.3, 5.5, 3.5, 3, 'Frontend (React)',
                   ['Dashboard Page', 'Clients Page', 'Projects Page',
                    'Time Entries Page', 'Invoices Page', 'AWS Status Page',
                    'React Router', 'REST API Client'], colors['frontend'])

    # Backend Components
    draw_component(4.3, 5.5, 3.5, 3, 'Backend (Flask)',
                   ['Client Routes (CRUD)', 'Project Routes (CRUD)',
                    'Time Entry Routes (CRUD)', 'Invoice Routes (CRUD)',
                    'AWS Status Routes', 'SQLite Models',
                    'Application Factory', 'CORS Middleware'], colors['backend'])

    # Custom Library
    draw_component(8.3, 5.5, 5.2, 3, 'invoicegen Library (Custom)',
                   ['models.py - Client, Project, TimeEntry, Invoice',
                    'calculator.py - Time & Billing Calculators',
                    'invoice_builder.py - Builder Pattern',
                    'tax.py - VAT & Multi-rate Tax',
                    'formatter.py - Currency & Display',
                    '20+ Unit Tests'], colors['library'])

    # AWS Services
    draw_component(0.3, 1.5, 6.5, 3.5, 'AWS Service Layer (7 Services)',
                   ['DynamoDB Service - Data persistence',
                    'S3 Service - PDF storage',
                    'Lambda Service - Invoice generation',
                    'API Gateway Service - REST endpoints',
                    'Cognito Service - Authentication',
                    'CloudWatch Service - Monitoring',
                    'Textract Service - Receipt OCR',
                    'All services support local mock mode'], colors['service'])

    # Data Layer
    draw_component(7.3, 1.5, 6.2, 3.5, 'Data Layer',
                   ['SQLite (Local Development)',
                    'DynamoDB Tables (Production)',
                    'S3 Bucket (Invoice PDFs)',
                    'Clients Table', 'Projects Table',
                    'Time Entries Table', 'Invoices Table',
                    'Full CRUD Operations'], colors['data'])

    # Arrows
    ax.annotate('', xy=(4.3, 7), xytext=(3.8, 7),
                arrowprops=dict(arrowstyle='->', color='#555', lw=1.5))
    ax.annotate('', xy=(8.3, 7), xytext=(7.8, 7),
                arrowprops=dict(arrowstyle='->', color='#555', lw=1.5))
    ax.annotate('', xy=(3.5, 5.5), xytext=(3.5, 5.0),
                arrowprops=dict(arrowstyle='->', color='#555', lw=1.5))
    ax.annotate('', xy=(10, 5.5), xytext=(10, 5.0),
                arrowprops=dict(arrowstyle='->', color='#555', lw=1.5))

    ax.text(7, 0.8, 'Student: Goutham Uppu (25167936) | Cloud Platform Programming | NCI',
            ha='center', fontsize=9, color='#666')

    plt.tight_layout()
    path = os.path.join(OUTPUT_DIR, 'component_diagram.png')
    fig.savefig(path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print(f"Saved: {path}")
    return path


if __name__ == "__main__":
    print("Generating architecture diagrams...")
    create_architecture_diagram()
    create_component_diagram()
    print("Done!")
