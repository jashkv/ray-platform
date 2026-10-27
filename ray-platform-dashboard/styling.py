"""
CSS Stylesheet module for Ray AI Platform & Serverless Interactive Dashboard.
High-end Obsidian Dark & Clean Light design system.
"""

CSS_STYLES = """
    /* ==========================================================================
       CSS Variables & Design Tokens (Executive Obsidian & Light Theme)
       ========================================================================== */
    :root {
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      --font-mono: 'JetBrains Mono', 'Fira Code', monospace;
      --font-heading: 'Montserrat', 'Plus Jakarta Sans', sans-serif;

      /* Dark Theme (Default) */
      --bg-base: #080c14;
      --bg-surface: #0e1524;
      --bg-card: #131c2e;
      --bg-card-hover: #19253d;
      --bg-glass: rgba(19, 28, 46, 0.75);
      --bg-code: #0b101b;
      
      --border-subtle: #202d46;
      --border-hover: #334466;
      --border-accent: #00f0ff;
      
      --text-main: #f8fafc;
      --text-muted: #94a3b8;
      --text-dim: #64748b;
      
      --cyan: #00f0ff;
      --cyan-dark: #0891b2;
      --cyan-glow: rgba(0, 240, 255, 0.25);
      --emerald: #10b981;
      --emerald-glow: rgba(16, 185, 129, 0.25);
      --purple: #8b5cf6;
      --purple-glow: rgba(139, 92, 246, 0.25);
      --amber: #f59e0b;
      --amber-glow: rgba(245, 158, 11, 0.25);
      --rose: #f43f5e;
      --sky: #0ea5e9;
      --indigo: #6366f1;

      --radius-sm: 6px;
      --radius-md: 10px;
      --radius-lg: 16px;
      --radius-xl: 24px;
      
      --shadow-sm: 0 2px 8px rgba(0,0,0,0.3);
      --shadow-md: 0 6px 20px rgba(0,0,0,0.4);
      --shadow-lg: 0 12px 36px rgba(0,0,0,0.5);
      --shadow-glow: 0 0 25px rgba(0, 240, 255, 0.2);

      --transition-fast: 0.15s ease;
      --transition-normal: 0.25s ease;
      --transition-slow: 0.4s ease;
    }

    [data-theme="light"] {
      --bg-base: #f8fafc;
      --bg-surface: #ffffff;
      --bg-card: #f1f5f9;
      --bg-card-hover: #e2e8f0;
      --bg-glass: rgba(255, 255, 255, 0.85);
      --bg-code: #1e293b;
      
      --border-subtle: #cbd5e1;
      --border-hover: #94a3b8;
      --border-accent: #0284c7;
      
      --text-main: #0f172a;
      --text-muted: #475569;
      --text-dim: #64748b;
      
      --cyan: #0284c7;
      --cyan-glow: rgba(2, 132, 199, 0.2);
      --emerald: #059669;
      --emerald-glow: rgba(5, 150, 105, 0.2);
      --purple: #7c3aed;
      --shadow-sm: 0 2px 6px rgba(0,0,0,0.06);
      --shadow-md: 0 6px 18px rgba(0,0,0,0.08);
      --shadow-lg: 0 12px 28px rgba(0,0,0,0.12);
    }

    /* Reset & Global */
    *, *::before, *::after {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    html {
      scroll-behavior: smooth;
      font-size: 15px;
    }

    body {
      font-family: var(--font-sans);
      background-color: var(--bg-base);
      color: var(--text-main);
      line-height: 1.65;
      overflow-x: hidden;
      background-image: 
        radial-gradient(circle at 15% 10%, rgba(0, 240, 255, 0.04) 0%, transparent 40%),
        radial-gradient(circle at 85% 60%, rgba(139, 92, 246, 0.04) 0%, transparent 40%),
        linear-gradient(to right, rgba(255, 255, 255, 0.015) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(255, 255, 255, 0.015) 1px, transparent 1px);
      background-size: 100% 100%, 100% 100%, 32px 32px, 32px 32px;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }
    ::-webkit-scrollbar-track {
      background: var(--bg-base);
    }
    ::-webkit-scrollbar-thumb {
      background: var(--border-hover);
      border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: var(--cyan);
    }

    /* Container */
    .container {
      max-width: 1380px;
      margin: 0 auto;
      padding: 0 24px;
    }

    /* Typography */
    h1, h2, h3, h4, h5, h6 {
      font-family: var(--font-heading);
      color: var(--text-main);
      font-weight: 700;
      line-height: 1.25;
      letter-spacing: -0.02em;
    }

    h1 { font-size: 2.75rem; }
    h2 { font-size: 2rem; }
    h3 { font-size: 1.35rem; }
    h4 { font-size: 1.15rem; }

    p { margin-bottom: 1rem; color: var(--text-muted); }
    p:last-child { margin-bottom: 0; }
    strong { color: var(--text-main); font-weight: 600; }
    code {
      font-family: var(--font-mono);
      background: rgba(0, 240, 255, 0.08);
      color: var(--cyan);
      padding: 0.15rem 0.4rem;
      border-radius: var(--radius-sm);
      font-size: 0.9em;
      border: 1px solid rgba(0, 240, 255, 0.15);
    }

    /* Sticky Navigation */
    .nav-bar {
      position: sticky;
      top: 0;
      z-index: 1000;
      background: var(--bg-glass);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border-bottom: 1px solid var(--border-subtle);
      transition: var(--transition-normal);
    }
    .nav-container {
      display: flex;
      align-items: center;
      justify-content: space-between;
      height: 70px;
    }
    .nav-brand {
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
      color: var(--text-main);
    }
    .nav-logo-icon {
      width: 38px;
      height: 38px;
      border-radius: var(--radius-sm);
      background: linear-gradient(135deg, var(--cyan), var(--purple));
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
      color: #fff;
      box-shadow: 0 0 15px var(--cyan-glow);
    }
    .nav-brand-text {
      font-family: var(--font-heading);
      font-weight: 800;
      font-size: 1.15rem;
      letter-spacing: -0.01em;
    }
    .nav-brand-text span {
      background: linear-gradient(90deg, var(--cyan), var(--purple));
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .nav-pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      background: rgba(16, 185, 129, 0.12);
      border: 1px solid rgba(16, 185, 129, 0.3);
      color: var(--emerald);
      border-radius: 20px;
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.02em;
    }
    .nav-pill-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--emerald);
      box-shadow: 0 0 8px var(--emerald);
      animation: pulse 2s infinite;
    }
    @keyframes pulse {
      0%, 100% { opacity: 1; transform: scale(1); }
      50% { opacity: 0.4; transform: scale(0.85); }
    }

    .nav-links {
      display: flex;
      align-items: center;
      gap: 6px;
      list-style: none;
    }
    .nav-link {
      padding: 8px 12px;
      color: var(--text-muted);
      text-decoration: none;
      font-size: 0.88rem;
      font-weight: 500;
      border-radius: var(--radius-sm);
      transition: var(--transition-fast);
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .nav-link:hover, .nav-link.active {
      color: var(--cyan);
      background: rgba(0, 240, 255, 0.08);
    }
    .nav-actions {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .theme-toggle-btn {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-main);
      width: 36px;
      height: 36px;
      border-radius: var(--radius-sm);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      transition: var(--transition-fast);
    }
    .theme-toggle-btn:hover {
      border-color: var(--cyan);
      color: var(--cyan);
    }
    .btn-action-primary {
      background: linear-gradient(135deg, var(--cyan), var(--blue));
      color: #050b14;
      font-weight: 700;
      font-size: 0.85rem;
      padding: 8px 16px;
      border-radius: var(--radius-sm);
      text-decoration: none;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: none;
      cursor: pointer;
      box-shadow: 0 0 15px rgba(0, 240, 255, 0.3);
      transition: var(--transition-fast);
    }
    .btn-action-primary:hover {
      transform: translateY(-1px);
      box-shadow: 0 0 25px rgba(0, 240, 255, 0.5);
    }

    /* Sub-nav Jump Bar */
    .subnav-bar {
      background: var(--bg-surface);
      border-bottom: 1px solid var(--border-subtle);
      overflow-x: auto;
      white-space: nowrap;
      padding: 6px 0;
    }
    .subnav-container {
      display: flex;
      gap: 4px;
    }
    .subnav-item {
      padding: 5px 12px;
      font-size: 0.8rem;
      font-weight: 500;
      color: var(--text-dim);
      text-decoration: none;
      border-radius: var(--radius-sm);
      transition: var(--transition-fast);
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .subnav-item:hover, .subnav-item.active {
      color: var(--text-main);
      background: var(--bg-card);
    }
    .subnav-item.active {
      color: var(--cyan);
      font-weight: 600;
    }

    /* Section Headers */
    .section-wrap {
      padding: 70px 0;
      border-bottom: 1px solid var(--border-subtle);
      position: relative;
    }
    .section-header {
      margin-bottom: 36px;
    }
    .section-eyebrow {
      font-size: 0.8rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.1em;
      color: var(--cyan);
      margin-bottom: 8px;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .section-title {
      font-size: 2.2rem;
      font-weight: 800;
      margin-bottom: 12px;
      background: linear-gradient(135deg, #ffffff 40%, #94a3b8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    [data-theme="light"] .section-title {
      background: linear-gradient(135deg, #0f172a 40%, #475569 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .section-desc {
      font-size: 1.05rem;
      max-width: 860px;
      line-height: 1.7;
    }

    /* Cards */
    .card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 24px;
      position: relative;
      transition: var(--transition-normal);
      box-shadow: var(--shadow-sm);
    }
    .card:hover {
      border-color: var(--border-hover);
      box-shadow: var(--shadow-md);
      transform: translateY(-2px);
    }
    .card-accent-top {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      border-top-left-radius: var(--radius-md);
      border-top-right-radius: var(--radius-md);
      background: linear-gradient(90deg, var(--cyan), var(--purple));
    }

    /* Grid Layouts */
    .grid-2 {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 24px;
    }
    .grid-3 {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 24px;
    }
    .grid-4 {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 20px;
    }

    /* Hero Section */
    .hero {
      padding: 80px 0 60px;
      position: relative;
      overflow: hidden;
    }
    .hero-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 20px;
    }
    .badge {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 12px;
      border-radius: 20px;
      font-size: 0.78rem;
      font-weight: 600;
      letter-spacing: 0.02em;
      border: 1px solid var(--border-subtle);
      background: var(--bg-card);
      color: var(--text-muted);
    }
    .badge-cyan { border-color: rgba(0, 240, 255, 0.4); color: var(--cyan); background: rgba(0, 240, 255, 0.08); }
    .badge-emerald { border-color: rgba(16, 185, 129, 0.4); color: var(--emerald); background: rgba(16, 185, 129, 0.08); }
    .badge-purple { border-color: rgba(139, 92, 246, 0.4); color: var(--purple); background: rgba(139, 92, 246, 0.08); }
    .badge-amber { border-color: rgba(245, 158, 11, 0.4); color: var(--amber); background: rgba(245, 158, 11, 0.08); }

    .hero-title {
      font-size: 3.4rem;
      font-weight: 800;
      line-height: 1.15;
      margin-bottom: 18px;
      letter-spacing: -0.03em;
    }
    .hero-title .gradient-text {
      background: linear-gradient(135deg, var(--cyan) 0%, #38bdf8 50%, var(--purple) 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }
    .hero-subtitle {
      font-size: 1.25rem;
      color: var(--text-muted);
      max-width: 920px;
      margin-bottom: 36px;
      line-height: 1.6;
    }

    /* Metric Badges / Stats */
    .hero-kpis {
      display: grid;
      grid-template-columns: repeat(6, 1fr);
      gap: 16px;
      margin-top: 36px;
    }
    .kpi-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 16px;
      text-align: center;
      transition: var(--transition-normal);
      position: relative;
      overflow: hidden;
    }
    .kpi-card:hover {
      border-color: var(--cyan);
      box-shadow: 0 4px 20px rgba(0, 240, 255, 0.15);
      transform: translateY(-2px);
    }
    .kpi-value {
      font-family: var(--font-heading);
      font-size: 1.85rem;
      font-weight: 800;
      color: var(--text-main);
      margin-bottom: 4px;
      line-height: 1.2;
    }
    .kpi-label {
      font-size: 0.78rem;
      color: var(--text-dim);
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    /* Quick Links Box */
    .quick-jump-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 14px;
      margin-top: 24px;
    }
    .quick-jump-card {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 14px 18px;
      text-decoration: none;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 12px;
      transition: var(--transition-fast);
    }
    .quick-jump-card:hover {
      border-color: var(--cyan);
      background: var(--bg-card);
      transform: translateY(-2px);
    }
    .quick-jump-icon {
      font-size: 1.2rem;
      color: var(--cyan);
    }
    .quick-jump-title {
      font-size: 0.88rem;
      font-weight: 600;
    }
    .quick-jump-desc {
      font-size: 0.75rem;
      color: var(--text-dim);
    }

    /* Code Terminal Windows */
    .terminal-window {
      background: var(--bg-code);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      overflow: hidden;
      margin: 20px 0;
      box-shadow: var(--shadow-md);
    }
    .terminal-header {
      background: rgba(255, 255, 255, 0.03);
      border-bottom: 1px solid var(--border-subtle);
      padding: 10px 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .terminal-dots {
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .terminal-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
    }
    .dot-red { background: #ff5f56; }
    .dot-yellow { background: #ffbd2e; }
    .dot-green { background: #27c93f; }
    .terminal-title {
      font-family: var(--font-mono);
      font-size: 0.8rem;
      color: var(--text-dim);
      font-weight: 500;
    }
    .btn-copy {
      background: transparent;
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      border-radius: var(--radius-sm);
      padding: 3px 8px;
      font-size: 0.75rem;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 5px;
      transition: var(--transition-fast);
    }
    .btn-copy:hover {
      color: var(--cyan);
      border-color: var(--cyan);
    }
    .terminal-body {
      padding: 16px 20px;
      font-family: var(--font-mono);
      font-size: 0.88rem;
      line-height: 1.6;
      color: #e2e8f0;
      overflow-x: auto;
    }
    .terminal-body pre {
      margin: 0;
      white-space: pre;
    }
    .prompt {
      color: var(--cyan);
      user-select: none;
    }
    .comment {
      color: #64748b;
      font-style: italic;
    }
    .command {
      color: #f8fafc;
      font-weight: 600;
    }
    .output {
      color: #94a3b8;
    }
    .success-text {
      color: var(--emerald);
      font-weight: 600;
    }

    /* Tabs Component */
    .tab-nav {
      display: flex;
      gap: 4px;
      border-bottom: 1px solid var(--border-subtle);
      margin-bottom: 20px;
    }
    .tab-btn {
      background: transparent;
      border: none;
      border-bottom: 2px solid transparent;
      color: var(--text-muted);
      padding: 10px 18px;
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      transition: var(--transition-fast);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .tab-btn:hover {
      color: var(--text-main);
    }
    .tab-btn.active {
      color: var(--cyan);
      border-bottom-color: var(--cyan);
      background: rgba(0, 240, 255, 0.04);
    }
    .tab-content {
      display: none;
    }
    .tab-content.active {
      display: block;
    }

    /* Mermaid Wrapper */
    .mermaid-wrapper {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 24px;
      margin: 20px 0;
      position: relative;
      overflow: hidden;
    }
    .mermaid-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border-subtle);
    }
    .mermaid-title {
      font-size: 0.92rem;
      font-weight: 700;
      color: var(--text-main);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .mermaid-actions {
      display: flex;
      gap: 8px;
    }
    .mermaid-btn {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      color: var(--text-muted);
      border-radius: var(--radius-sm);
      padding: 4px 10px;
      font-size: 0.78rem;
      cursor: pointer;
      transition: var(--transition-fast);
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .mermaid-btn:hover {
      color: var(--cyan);
      border-color: var(--cyan);
    }
    .mermaid-container {
      overflow-x: auto;
      display: flex;
      justify-content: center;
      min-height: 200px;
      transition: transform 0.2s ease;
    }

    /* Comparison Tables */
    .table-container {
      overflow-x: auto;
      margin: 20px 0;
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      background: var(--bg-card);
    }
    .data-table {
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9rem;
      text-align: left;
    }
    .data-table th {
      background: var(--bg-surface);
      padding: 12px 16px;
      font-weight: 700;
      color: var(--text-main);
      border-bottom: 1px solid var(--border-subtle);
      font-size: 0.82rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }
    .data-table td {
      padding: 12px 16px;
      border-bottom: 1px solid var(--border-subtle);
      color: var(--text-muted);
    }
    .data-table tr:last-child td {
      border-bottom: none;
    }
    .data-table tr:hover td {
      background: rgba(255, 255, 255, 0.02);
      color: var(--text-main);
    }
    .tag-pill {
      display: inline-block;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 0.75rem;
      font-weight: 600;
    }
    .tag-green { background: rgba(16, 185, 129, 0.15); color: var(--emerald); border: 1px solid rgba(16, 185, 129, 0.3); }
    .tag-red { background: rgba(244, 63, 94, 0.15); color: var(--rose); border: 1px solid rgba(244, 63, 94, 0.3); }
    .tag-blue { background: rgba(14, 165, 233, 0.15); color: var(--sky); border: 1px solid rgba(14, 165, 233, 0.3); }
    .tag-purple { background: rgba(139, 92, 246, 0.15); color: var(--purple); border: 1px solid rgba(139, 92, 246, 0.3); }

    /* Alert Boxes */
    .alert {
      padding: 16px 20px;
      border-radius: var(--radius-md);
      margin: 18px 0;
      display: flex;
      gap: 14px;
      align-items: flex-start;
      border: 1px solid transparent;
      font-size: 0.92rem;
      line-height: 1.6;
    }
    .alert-icon {
      font-size: 1.2rem;
      flex-shrink: 0;
      margin-top: 2px;
    }
    .alert-info { background: rgba(14, 165, 233, 0.08); border-color: rgba(14, 165, 233, 0.25); color: #bae6fd; }
    .alert-info .alert-icon { color: var(--sky); }
    .alert-warning { background: rgba(245, 158, 11, 0.08); border-color: rgba(245, 158, 11, 0.25); color: #fde68a; }
    .alert-warning .alert-icon { color: var(--amber); }
    .alert-success { background: rgba(16, 185, 129, 0.08); border-color: rgba(16, 185, 129, 0.25); color: #a7f3d0; }
    .alert-success .alert-icon { color: var(--emerald); }

    /* Interactive Data Visualizer (Before / After Records) */
    .record-card-grid {
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: center;
      gap: 16px;
      margin: 20px 0;
    }
    .record-box {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 18px;
    }
    .record-box-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      margin-bottom: 12px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border-subtle);
    }
    .record-box-title {
      font-weight: 700;
      font-size: 0.9rem;
      color: var(--text-main);
    }
    .record-field {
      display: flex;
      justify-content: space-between;
      margin-bottom: 6px;
      font-size: 0.85rem;
    }
    .record-field-label { color: var(--text-dim); }
    .record-field-val { font-family: var(--font-mono); color: var(--text-main); }
    .record-divider-arrow {
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.5rem;
      color: var(--cyan);
    }

    /* Calculator Widget */
    .calc-card {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      padding: 30px;
      box-shadow: var(--shadow-lg);
    }
    .calc-input-group {
      margin-bottom: 24px;
    }
    .calc-slider-header {
      display: flex;
      justify-content: space-between;
      margin-bottom: 10px;
    }
    .calc-label {
      font-weight: 600;
      font-size: 0.95rem;
      color: var(--text-main);
    }
    .calc-val-pill {
      background: rgba(0, 240, 255, 0.1);
      border: 1px solid var(--cyan);
      color: var(--cyan);
      padding: 3px 12px;
      border-radius: 20px;
      font-family: var(--font-mono);
      font-weight: 700;
      font-size: 0.9rem;
    }
    .calc-range {
      width: 100%;
      height: 8px;
      border-radius: 4px;
      background: var(--bg-surface);
      outline: none;
      -webkit-appearance: none;
    }
    .calc-range::-webkit-slider-thumb {
      -webkit-appearance: none;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: var(--cyan);
      cursor: pointer;
      box-shadow: 0 0 10px var(--cyan-glow);
    }
    .calc-results-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-top: 24px;
      padding-top: 24px;
      border-top: 1px solid var(--border-subtle);
    }
    .calc-result-box {
      padding: 20px;
      border-radius: var(--radius-md);
      text-align: center;
    }
    .calc-result-box.eks {
      background: rgba(14, 165, 233, 0.08);
      border: 1px solid rgba(14, 165, 233, 0.25);
    }
    .calc-result-box.serverless {
      background: rgba(16, 185, 129, 0.08);
      border: 1px solid rgba(16, 185, 129, 0.3);
    }
    .calc-res-title {
      font-size: 0.82rem;
      text-transform: uppercase;
      font-weight: 700;
      letter-spacing: 0.05em;
      margin-bottom: 8px;
    }
    .calc-res-price {
      font-family: var(--font-heading);
      font-size: 2.2rem;
      font-weight: 800;
      margin-bottom: 4px;
    }
    .calc-res-sub {
      font-size: 0.78rem;
      color: var(--text-dim);
    }

    /* Checklist Widget */
    .checklist-container {
      background: var(--bg-card);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-md);
      padding: 24px;
    }
    .check-item {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 12px 0;
      border-bottom: 1px solid var(--border-subtle);
      cursor: pointer;
    }
    .check-item:last-child {
      border-bottom: none;
    }
    .check-box-custom {
      width: 20px;
      height: 20px;
      border-radius: 4px;
      border: 2px solid var(--border-hover);
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      margin-top: 2px;
      transition: var(--transition-fast);
    }
    .check-item.checked .check-box-custom {
      background: var(--cyan);
      border-color: var(--cyan);
      color: #050b14;
    }
    .check-item.checked .check-text-title {
      text-decoration: line-through;
      color: var(--text-dim);
    }
    .check-text-title {
      font-weight: 600;
      color: var(--text-main);
      font-size: 0.92rem;
      margin-bottom: 2px;
    }
    .check-text-desc {
      font-size: 0.8rem;
      color: var(--text-dim);
    }
    .progress-bar-wrap {
      margin-bottom: 20px;
    }
    .progress-bar-header {
      display: flex;
      justify-content: space-between;
      font-size: 0.85rem;
      font-weight: 600;
      margin-bottom: 6px;
    }
    .progress-bar-track {
      height: 8px;
      background: var(--bg-surface);
      border-radius: 4px;
      overflow: hidden;
    }
    .progress-bar-fill {
      height: 100%;
      background: linear-gradient(90deg, var(--cyan), var(--emerald));
      width: 0%;
      transition: width 0.3s ease;
    }

    /* Modal for Fullscreen Diagrams */
    .modal-overlay {
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(8, 12, 20, 0.95);
      backdrop-filter: blur(8px);
      z-index: 2000;
      align-items: center;
      justify-content: center;
      padding: 30px;
    }
    .modal-overlay.active {
      display: flex;
    }
    .modal-content {
      background: var(--bg-surface);
      border: 1px solid var(--border-subtle);
      border-radius: var(--radius-lg);
      width: 95%;
      height: 90%;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      box-shadow: var(--shadow-lg);
    }
    .modal-header {
      padding: 16px 24px;
      border-bottom: 1px solid var(--border-subtle);
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .modal-body {
      flex: 1;
      padding: 30px;
      overflow: auto;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .modal-close-btn {
      background: transparent;
      border: none;
      color: var(--text-muted);
      font-size: 1.4rem;
      cursor: pointer;
    }
    .modal-close-btn:hover { color: var(--cyan); }

    /* Footer */
    .footer {
      background: var(--bg-surface);
      border-top: 1px solid var(--border-subtle);
      padding: 50px 0 30px;
      margin-top: 80px;
    }
    .footer-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 20px;
      margin-bottom: 30px;
    }
    .footer-copy {
      font-size: 0.85rem;
      color: var(--text-dim);
    }

    /* Responsive */
    @media (max-width: 1024px) {
      .hero-kpis { grid-template-columns: repeat(3, 1fr); }
      .grid-3 { grid-template-columns: 1fr; }
      .grid-2 { grid-template-columns: 1fr; }
      .quick-jump-grid { grid-template-columns: repeat(2, 1fr); }
      .record-card-grid { grid-template-columns: 1fr; }
      .record-divider-arrow { transform: rotate(90deg); margin: 10px 0; }
    }
    @media (max-width: 768px) {
      .nav-links { display: none; }
      .hero-title { font-size: 2.2rem; }
      .hero-kpis { grid-template-columns: repeat(2, 1fr); }
      .quick-jump-grid { grid-template-columns: 1fr; }
      .calc-results-grid { grid-template-columns: 1fr; }
    }
"""
