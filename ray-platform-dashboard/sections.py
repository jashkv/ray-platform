"""
Sections module for Ray AI Platform & Serverless Interactive Dashboard.
Re-exports all HTML generators for each chapter and UI component.
"""

from styling import CSS_STYLES
from sections_part1 import get_hero, get_app_section, get_config_section
from sections_part2 import get_setup_section, get_tf_section, get_order_section
from sections_part3 import get_pipeline_section, get_cost_section, get_serverless_section
from sections_part4 import get_security_section, get_tools_section, get_footer, get_scripts

def get_head():
    return f"""<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ray AI Platform on AWS EKS & Serverless Alternative — Production Architecture & Implementation Runbook</title>
  
  <!-- Modern Typography: Inter, Plus Jakarta Sans, JetBrains Mono -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Montserrat:wght@600;700;800;900&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
  
  <!-- FontAwesome Icons -->
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  
  <!-- Mermaid.js for Diagrams -->
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  
  <!-- Chart.js for Interactive Charts -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <style>
{CSS_STYLES}
  </style>
</head>
"""

def get_nav():
    return """<!-- Sticky Frosted Navigation Bar -->
<header class="nav-bar">
  <div class="container nav-container">
    <a href="#hero" class="nav-brand">
      <div class="nav-logo-icon">
        <i class="fa-solid fa-cube"></i>
      </div>
      <div class="nav-brand-text">
        Ray AI Platform <span>// AWS EKS & Serverless</span>
      </div>
    </a>

    <div style="display: flex; align-items: center; gap: 12px;">
      <span class="nav-pill">
        <span class="nav-pill-dot"></span>
        Production Ready &bull; Branch: serverless
      </span>
    </div>

    <ul class="nav-links">
      <li><a href="#application" class="nav-link"><i class="fa-solid fa-database"></i> Exact App</a></li>
      <li><a href="#configuration" class="nav-link"><i class="fa-solid fa-sliders"></i> Ray Config</a></li>
      <li><a href="#setup" class="nav-link"><i class="fa-solid fa-terminal"></i> Setup & Install</a></li>
      <li><a href="#terraform" class="nav-link"><i class="fa-solid fa-network-wired"></i> Terraform IaC</a></li>
      <li><a href="#apply-order" class="nav-link"><i class="fa-solid fa-list-ol"></i> Apply Order</a></li>
      <li><a href="#pipeline" class="nav-link"><i class="fa-solid fa-diagram-project"></i> Pipeline Flow</a></li>
      <li><a href="#cost" class="nav-link"><i class="fa-solid fa-file-invoice-dollar"></i> Infra Cost</a></li>
      <li><a href="#serverless" class="nav-link"><i class="fa-solid fa-bolt"></i> Serverless</a></li>
    </ul>

    <div class="nav-actions">
      <button id="themeToggle" class="theme-toggle-btn" title="Toggle Light/Dark Theme" aria-label="Toggle Theme">
        <i class="fa-solid fa-moon"></i>
      </button>
      <a href="#interactive-workbench" class="btn-action-primary">
        <i class="fa-solid fa-calculator"></i> Workbench
      </a>
    </div>
  </div>
</header>

<!-- Secondary Subnav for Quick Chapter Jump -->
<div class="subnav-bar">
  <div class="container subnav-container">
    <a href="#application" class="subnav-item"><i class="fa-solid fa-circle-dot"></i> 1. Exact Application</a>
    <a href="#configuration" class="subnav-item"><i class="fa-solid fa-circle-dot"></i> 2. Runtime & Compute Config</a>
    <a href="#setup" class="subnav-item"><i class="fa-solid fa-circle-dot"></i> 3. Software & File Setup</a>
    <a href="#terraform" class="subnav-item"><i class="fa-solid fa-circle-dot"></i> 4. Terraform IaC Breakdown</a>
    <a href="#apply-order" class="subnav-item"><i class="fa-solid fa-circle-dot"></i> 5. Step-by-Step Apply Order</a>
    <a href="#pipeline" class="subnav-item"><i class="fa-solid fa-circle-dot"></i> 6. Pipeline Flow & ML</a>
    <a href="#cost" class="subnav-item"><i class="fa-solid fa-circle-dot"></i> 7. Infrastructure Cost Architecture</a>
    <a href="#serverless" class="subnav-item"><i class="fa-solid fa-circle-dot"></i> 8. Serverless Alternative</a>
    <a href="#security" class="subnav-item"><i class="fa-solid fa-circle-dot"></i> 9. Security & Observability</a>
    <a href="#interactive-workbench" class="subnav-item"><i class="fa-solid fa-circle-dot"></i> 10. Interactive Tools</a>
  </div>
</div>
"""
