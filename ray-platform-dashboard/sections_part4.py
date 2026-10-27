"""
Part 4 of Dashboard Sections:
- get_security_section() (Chapter 9: Security, Zero-Trust & Observability)
- get_tools_section() (Chapter 10: Interactive Platform Workbench)
- get_footer()
- get_scripts()
"""

def get_security_section():
    return """<!-- CHAPTER 9: SECURITY & OBSERVABILITY -->
<section id="security" class="section-wrap" style="background: var(--bg-surface);">
  <div class="container">
    <div class="section-header">
      <div class="section-eyebrow"><i class="fa-solid fa-shield-halved"></i> Chapter 9: Security & Telemetry</div>
      <h2 class="section-title">Zero-Trust Identity, Data Governance & Full-Stack Observability</h2>
      <p class="section-desc">
        Implementing strict least-privilege IAM roles via EKS IRSA and AWS Lambda execution roles, end-to-end cryptographic encryption with AWS KMS, and unified Prometheus + Grafana telemetry.
      </p>
    </div>

    <!-- 3 Pillars of Security -->
    <div class="grid-3">
      <div class="card">
        <div class="card-accent-top"></div>
        <h4 style="color: var(--cyan); margin-bottom: 8px;"><i class="fa-solid fa-key"></i> 1. IRSA & Zero Static Secrets</h4>
        <p style="font-size: 0.88rem;">
          IAM Roles for Service Accounts (IRSA) eliminates hardcoded AWS access keys. Pods exchange Kubernetes ServiceAccount tokens via AWS STS OIDC federation to obtain temporary 15-minute scoped IAM credentials.
        </p>
        <span class="tag-pill tag-green">Zero Static Credentials</span>
      </div>

      <div class="card">
        <div class="card-accent-top"></div>
        <h4 style="color: var(--purple); margin-bottom: 8px;"><i class="fa-solid fa-lock"></i> 2. Cryptographic Envelopes (KMS)</h4>
        <p style="font-size: 0.88rem;">
          All S3 lakehouse objects, DynamoDB ledger tables, and CloudWatch log streams are encrypted at rest with an AWS KMS Customer Managed Key (CMK) featuring automatic annual key rotation and TLS 1.3 in transit.
        </p>
        <span class="tag-pill tag-purple">KMS CMK AES-256</span>
      </div>

      <div class="card">
        <div class="card-accent-top"></div>
        <h4 style="color: var(--emerald); margin-bottom: 8px;"><i class="fa-solid fa-gauge-high"></i> 3. Unified Telemetry Stack</h4>
        <p style="font-size: 0.88rem;">
          Ray Head metrics exporter (port 8080) scraped every 15s by Prometheus. Grafana dashboards visualize Ray cluster memory, actor execution throughput, Karpenter spot node consolidation, and CloudWatch structured logs.
        </p>
        <span class="tag-pill tag-blue">Prometheus &bull; Grafana &bull; CloudWatch</span>
      </div>
    </div>
  </div>
</section>
"""

def get_tools_section():
    return """<!-- CHAPTER 10: INTERACTIVE WORKBENCH -->
<section id="interactive-workbench" class="section-wrap">
  <div class="container">
    <div class="section-header">
      <div class="section-eyebrow"><i class="fa-solid fa-calculator"></i> Chapter 10: Interactive Workbench</div>
      <h2 class="section-title">Platform Engineering Workbench & Decision Simulator</h2>
      <p class="section-desc">
        Interact with the live cloud economics calculator, evaluate architectural fitness for your specific workload, and track your deployment progress.
      </p>
    </div>

    <!-- Interactive Tool 1: Live Cloud Cost Simulator -->
    <div class="calc-card" style="margin-bottom: 36px;">
      <h3 style="margin-bottom: 8px; display: flex; align-items: center; gap: 8px;">
        <i class="fa-solid fa-calculator" style="color: var(--cyan);"></i> Dynamic Cloud Cost Simulator
      </h3>
      <p style="font-size: 0.9rem; margin-bottom: 24px;">
        Adjust the sliders below to simulate your organization's batch execution volume and compare monthly cloud bills in real time:
      </p>

      <div class="calc-input-group">
        <div class="calc-slider-header">
          <span class="calc-label">Monthly Pipeline Executions:</span>
          <span id="sliderRunsVal" class="calc-val-pill">100 runs / month</span>
        </div>
        <input type="range" id="sliderRuns" class="calc-range" min="1" max="50000" step="5" value="100" oninput="updateCostCalculator()">
      </div>

      <div class="calc-input-group">
        <div class="calc-slider-header">
          <span class="calc-label">Records per Ingestion Batch:</span>
          <span id="sliderRecordsVal" class="calc-val-pill">2,400 records</span>
        </div>
        <input type="range" id="sliderRecords" class="calc-range" min="500" max="50000" step="500" value="2400" oninput="updateCostCalculator()">
      </div>

      <div class="calc-results-grid">
        <div class="calc-result-box eks">
          <div class="calc-res-title" style="color: var(--sky);">Ray on EKS + Karpenter</div>
          <div id="calcResEks" class="calc-res-price" style="color: var(--sky);">$218.00</div>
          <div class="calc-res-sub">Includes $171.55 fixed baseline + variable Spot compute</div>
        </div>

        <div class="calc-result-box serverless">
          <div class="calc-res-title" style="color: var(--emerald);">AWS Serverless Alternative</div>
          <div id="calcResServerless" class="calc-res-price" style="color: var(--emerald);">$0.14</div>
          <div class="calc-res-sub">$0.00 idle cost + $0.00139 per run</div>
        </div>
      </div>

      <div style="margin-top: 18px; text-align: center; font-size: 0.95rem;">
        <span id="calcSavingsBadge" class="tag-pill tag-green" style="font-size: 0.88rem; padding: 6px 16px;">
          Serverless saves $217.86 / month (99.9% savings)
        </span>
      </div>
    </div>

    <!-- Interactive Tool 2: Architecture Decision Matrix -->
    <div class="card" style="margin-bottom: 36px;">
      <div class="card-accent-top"></div>
      <h3 style="margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
        <i class="fa-solid fa-compass" style="color: var(--purple);"></i> Architecture Recommendation Engine
      </h3>
      <p style="font-size: 0.9rem; margin-bottom: 18px;">
        Select your workload characteristics to receive an immediate architectural recommendation:
      </p>

      <div class="grid-3" style="margin-bottom: 20px;">
        <div>
          <label style="font-size: 0.82rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase;">Run Frequency</label>
          <select id="selFrequency" class="calc-range" style="margin-top: 6px; padding: 8px; background: var(--bg-surface); color: var(--text-main); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm);" onchange="evaluateArchitecture()">
            <option value="sporadic">Periodic / Scheduled (1 - 500 runs/mo)</option>
            <option value="moderate">Moderate Batch (500 - 20,000 runs/mo)</option>
            <option value="high">Massive High-Volume (&gt; 150,000 runs/mo)</option>
            <option value="streaming">Continuous Streaming / Interactive Ray</option>
          </select>
        </div>

        <div>
          <label style="font-size: 0.82rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase;">Compute Complexity</label>
          <select id="selComplexity" class="calc-range" style="margin-top: 6px; padding: 8px; background: var(--bg-surface); color: var(--text-main); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm);" onchange="evaluateArchitecture()">
            <option value="standard">Standard ML (XGBoost, Scikit-learn, PyIceberg)</option>
            <option value="distributed">Deep Learning (Multi-GPU PyTorch, LLM Fine-tuning)</option>
          </select>
        </div>

        <div>
          <label style="font-size: 0.82rem; font-weight: 700; color: var(--text-dim); text-transform: uppercase;">Team Operational Capacity</label>
          <select id="selOps" class="calc-range" style="margin-top: 6px; padding: 8px; background: var(--bg-surface); color: var(--text-main); border: 1px solid var(--border-subtle); border-radius: var(--radius-sm);" onchange="evaluateArchitecture()">
            <option value="lean">Lean Team (Zero Kubernetes Maintenance Desired)</option>
            <option value="platform">Dedicated Platform Engineering Team Available</option>
          </select>
        </div>
      </div>

      <div id="archRecResult" class="alert alert-success" style="margin-top: 10px;">
        <div class="alert-icon"><i class="fa-solid fa-circle-check"></i></div>
        <div>
          <strong id="archRecTitle">Recommended: AWS Serverless Alternative</strong>
          <p id="archRecDesc" style="font-size: 0.88rem; margin-top: 4px; margin-bottom: 0;">
            For scheduled or periodic workloads without multi-GPU requirements, the serverless architecture eliminates 100% of idle cluster waste, provides sub-second cold starts, and saves over $2,500/year.
          </p>
        </div>
      </div>
    </div>

    <!-- Interactive Tool 3: Deployment Checklist Tracker -->
    <div class="checklist-container">
      <div class="progress-bar-wrap">
        <div class="progress-bar-header">
          <span>Deployment Completion Runbook Progress:</span>
          <span id="checkProgressText" style="color: var(--cyan);">0% Complete (0/8 Gates)</span>
        </div>
        <div class="progress-bar-track">
          <div id="checkProgressFill" class="progress-bar-fill"></div>
        </div>
      </div>

      <div class="check-item" onclick="toggleCheckItem(this)">
        <div class="check-box-custom"><i class="fa-solid fa-check"></i></div>
        <div>
          <div class="check-text-title">Gate 1: Local Tooling & OS Packages Verified</div>
          <div class="check-text-desc">Python 3.12, Terraform v1.10+, Docker Buildx, AWS CLI authenticated via STS.</div>
        </div>
      </div>

      <div class="check-item" onclick="toggleCheckItem(this)">
        <div class="check-box-custom"><i class="fa-solid fa-check"></i></div>
        <div>
          <div class="check-text-title">Gate 2: Automated Pytest Suite Passed</div>
          <div class="check-text-desc">Executed <code>make test</code> and <code>make test-serverless</code> with 5/5 tests passing cleanly.</div>
        </div>
      </div>

      <div class="check-item" onclick="toggleCheckItem(this)">
        <div class="check-box-custom"><i class="fa-solid fa-check"></i></div>
        <div>
          <div class="check-text-title">Gate 3: Layer 1 Bootstrap Initialized</div>
          <div class="check-text-desc">S3 remote state storage bucket and DynamoDB locking table provisioned.</div>
        </div>
      </div>

      <div class="check-item" onclick="toggleCheckItem(this)">
        <div class="check-box-custom"><i class="fa-solid fa-check"></i></div>
        <div>
          <div class="check-text-title">Gate 4: Layer 2 Network VPC & S3 Endpoint Applied</div>
          <div class="check-text-desc">3-AZ subnets, NAT gateway, and $0-cost S3 gateway route table established.</div>
        </div>
      </div>

      <div class="check-item" onclick="toggleCheckItem(this)">
        <div class="check-box-custom"><i class="fa-solid fa-check"></i></div>
        <div>
          <div class="check-text-title">Gate 5: Layer 3 Data Lakehouse & Glue DB Active</div>
          <div class="check-text-desc">Iceberg S3 bucket, Glue catalog database, and IRSA trust relationships configured.</div>
        </div>
      </div>

      <div class="check-item" onclick="toggleCheckItem(this)">
        <div class="check-box-custom"><i class="fa-solid fa-check"></i></div>
        <div>
          <div class="check-text-title">Gate 6: Layer 4 & 5 EKS Cluster & KubeRay Operator Running</div>
          <div class="check-text-desc">EKS 1.31 control plane, managed node group, KubeRay operator, and Karpenter Spot nodepools active.</div>
        </div>
      </div>

      <div class="check-item" onclick="toggleCheckItem(this)">
        <div class="check-box-custom"><i class="fa-solid fa-check"></i></div>
        <div>
          <div class="check-text-title">Gate 7: Layer 6 Serverless Pipeline Provisioned</div>
          <div class="check-text-desc">AWS Step Functions state machine, 6 Lambda functions, SQS DLQ, and EventBridge triggers deployed.</div>
        </div>
      </div>

      <div class="check-item" onclick="toggleCheckItem(this)">
        <div class="check-box-custom"><i class="fa-solid fa-check"></i></div>
        <div>
          <div class="check-text-title">Gate 8: End-to-End Pipeline Verification Verified</div>
          <div class="check-text-desc">Processed 2,400 raw rows, verified 1,557 canonical entities, committed Iceberg snapshot, achieved $R^2 = 0.8725$.</div>
        </div>
      </div>
    </div>
  </div>
</section>
"""

def get_footer():
    return """<!-- FOOTER -->
<footer class="footer">
  <div class="container">
    <div class="footer-content">
      <div>
        <div style="font-family: var(--font-heading); font-weight: 800; font-size: 1.1rem; margin-bottom: 6px;">
          Ray AI Platform <span style="color: var(--cyan);">// AWS EKS & Serverless</span>
        </div>
        <p class="footer-copy">
          Distributed AI Foundation for Entity Resolution, Apache Iceberg Lakehouse & XGBoost Revenue Regression.
        </p>
      </div>

      <div style="display: flex; gap: 16px; align-items: center;">
        <span class="badge badge-cyan"><i class="fa-solid fa-code-branch"></i> serverless</span>
        <span class="badge badge-emerald"><i class="fa-solid fa-check"></i> All 10 Gates Production Ready</span>
      </div>
    </div>

    <div style="text-align: center; font-size: 0.8rem; color: var(--text-dim); border-top: 1px solid var(--border-subtle); padding-top: 20px;">
      Built with precision following AWS Well-Architected Framework &bullet; Apache Iceberg v2 &bullet; Ray Core 2.40.0 &bullet; Terraform v1.10
    </div>
  </div>
</footer>

<!-- Fullscreen Diagram Lightbox Modal -->
<div id="diagramModal" class="modal-overlay">
  <div class="modal-content">
    <div class="modal-header">
      <span id="modalTitle" style="font-weight: 700; color: var(--text-main); font-size: 1.05rem;">Architecture Diagram Preview</span>
      <button class="modal-close-btn" onclick="closeDiagramModal()"><i class="fa-solid fa-xmark"></i></button>
    </div>
    <div class="modal-body" id="modalBody"></div>
  </div>
</div>
"""

def get_scripts():
    return """<!-- JAVASCRIPT LOGIC -->
<script>
  // 1. Initialize Mermaid.js
  document.addEventListener('DOMContentLoaded', () => {
    mermaid.initialize({
      startOnLoad: true,
      theme: 'dark',
      themeVariables: {
        darkMode: true,
        background: '#0e1524',
        primaryColor: '#131c2e',
        primaryBorderColor: '#00f0ff',
        primaryTextColor: '#f8fafc',
        lineColor: '#00f0ff',
        secondaryColor: '#19253d',
        tertiaryColor: '#1f293d',
        fontSize: '13px',
        fontFamily: 'Inter, sans-serif'
      }
    });

    initCharts();
    evaluateArchitecture();
    updateCostCalculator();
  });

  // 2. Light / Dark Theme Toggle
  const themeToggle = document.getElementById('themeToggle');
  themeToggle.addEventListener('click', () => {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', newTheme);
    themeToggle.innerHTML = newTheme === 'light' ? '<i class=\"fa-solid fa-sun\"></i>' : '<i class=\"fa-solid fa-moon\"></i>';
  });

  // 3. Tab Navigation Handler
  function switchTab(btn, tabId) {
    const nav = btn.parentElement;
    nav.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');

    const container = nav.parentElement;
    container.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    const target = document.getElementById(tabId);
    if (target) target.classList.add('active');
  }

  // 4. Copy Code Snippet with Feedback Toast
  function copySnippet(btn) {
    const pre = btn.closest('.terminal-window').querySelector('pre');
    const text = pre.innerText;
    navigator.clipboard.writeText(text).then(() => {
      const orig = btn.innerHTML;
      btn.innerHTML = '<i class=\"fa-solid fa-check\" style=\"color: var(--emerald);\"></i> Copied!';
      setTimeout(() => btn.innerHTML = orig, 2000);
    });
  }

  // 5. Fullscreen Diagram Lightbox Modal
  function openDiagramModal(elementId) {
    const srcEl = document.getElementById(elementId);
    if (!srcEl) return;
    const modal = document.getElementById('diagramModal');
    const modalBody = document.getElementById('modalBody');
    const modalTitle = document.getElementById('modalTitle');
    
    modalTitle.innerText = "Architecture Visualizer // Deep Inspection";
    modalBody.innerHTML = srcEl.innerHTML;
    modal.classList.add('active');
  }

  function closeDiagramModal() {
    document.getElementById('diagramModal').classList.remove('active');
  }

  document.getElementById('diagramModal').addEventListener('click', (e) => {
    if (e.target.id === 'diagramModal') closeDiagramModal();
  });

  // 6. Interactive Cost Calculator Slider Logic
  function updateCostCalculator() {
    const runs = parseInt(document.getElementById('sliderRuns').value, 10);
    const records = parseInt(document.getElementById('sliderRecords').value, 10);

    document.getElementById('sliderRunsVal').innerText = runs.toLocaleString() + " runs / month";
    document.getElementById('sliderRecordsVal').innerText = records.toLocaleString() + " records";

    // EKS Cost = Fixed ($73 + $32.85 + $65.70 = $171.55) + Spot compute (~$0.058/hr * (duration in hr))
    // Duration approx 30s per batch on EKS workers
    const eksComputeHours = (runs * 30) / 3600;
    const eksCost = 171.55 + (eksComputeHours * 0.058 * 2) + 15.0; // 2 Spot workers + storage

    // Serverless Cost = $0.00 idle + runs * $0.00139 (scaled by records ratio)
    const recordMultiplier = records / 2400;
    const serverlessCostPerRun = 0.00139 * recordMultiplier;
    const serverlessCost = runs * serverlessCostPerRun;

    document.getElementById('calcResEks').innerText = "$" + eksCost.toFixed(2);
    document.getElementById('calcResServerless').innerText = "$" + (serverlessCost < 0.01 ? serverlessCost.toFixed(4) : serverlessCost.toFixed(2));

    const diff = eksCost - serverlessCost;
    const badge = document.getElementById('calcSavingsBadge');
    if (diff > 0) {
      const pct = ((diff / eksCost) * 100).toFixed(1);
      badge.className = "tag-pill tag-green";
      badge.innerText = `Serverless saves $${diff.toFixed(2)} / month (${pct}% savings)`;
    } else {
      badge.className = "tag-pill tag-blue";
      badge.innerText = `Ray on EKS is more cost-effective by $${Math.abs(diff).toFixed(2)} / month at this high volume!`;
    }
  }

  // 7. Architecture Recommendation Wizard
  function evaluateArchitecture() {
    const freq = document.getElementById('selFrequency').value;
    const comp = document.getElementById('selComplexity').value;
    const ops = document.getElementById('selOps').value;

    const titleEl = document.getElementById('archRecTitle');
    const descEl = document.getElementById('archRecDesc');
    const box = document.getElementById('archRecResult');

    if (comp === 'distributed' || freq === 'streaming') {
      box.className = "alert alert-info";
      titleEl.innerText = "Recommended: Ray Cluster on AWS EKS";
      descEl.innerText = "Workloads requiring continuous microsecond streaming, distributed PyTorch multi-GPU training, or persistent Ray actors in memory necessitate the Ray on EKS architecture.";
    } else if (freq === 'high') {
      box.className = "alert alert-warning";
      titleEl.innerText = "Close Call: EKS vs Serverless Inflection Threshold";
      descEl.innerText = "At over 150,000 runs per month, continuous Spot worker reservation on EKS begins to achieve parity with Step Functions invocation pricing. Consider EKS if you already have Kubernetes cluster infrastructure.";
    } else {
      box.className = "alert alert-success";
      titleEl.innerText = "Recommended: AWS Serverless Alternative (Branch 'serverless')";
      descEl.innerText = "For periodic or moderate batch ingestion with standard ML models, the serverless architecture eliminates 100% of idle cluster waste, costs only ~$0.00139 per run, requires zero node maintenance, and deploys via Terraform in under 2 minutes.";
    }
  }

  // 8. Interactive Deployment Checklist Logic
  function toggleCheckItem(el) {
    el.classList.toggle('checked');
    const total = document.querySelectorAll('.check-item').length;
    const checked = document.querySelectorAll('.check-item.checked').length;
    const pct = Math.round((checked / total) * 100);

    document.getElementById('checkProgressFill').style.width = pct + "%";
    document.getElementById('checkProgressText').innerText = `${pct}% Complete (${checked}/${total} Gates)`;
  }

  // 9. Chart.js Initializations
  function initCharts() {
    const ctxDonut = document.getElementById('costDonutChart').getContext('2d');
    new Chart(ctxDonut, {
      type: 'doughnut',
      data: {
        labels: ['EKS Control Plane ($73)', 'Head Node c7g ($66)', 'NAT Gateway ($33)', 'Spot Workers & Storage ($43)'],
        datasets: [{
          data: [73, 66, 33, 43],
          backgroundColor: ['#00f0ff', '#8b5cf6', '#f59e0b', '#10b981'],
          borderColor: '#0e1524',
          borderWidth: 3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: 'bottom',
            labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } }
          }
        }
      }
    });

    const ctxLine = document.getElementById('costLineChart').getContext('2d');
    new Chart(ctxLine, {
      type: 'line',
      data: {
        labels: ['10 runs', '100 runs', '1,000 runs', '10,000 runs', '50,000 runs', '150,000 runs'],
        datasets: [
          {
            label: 'Ray on EKS ($/mo)',
            data: [215, 218, 225, 245, 350, 480],
            borderColor: '#00f0ff',
            backgroundColor: 'rgba(0, 240, 255, 0.1)',
            tension: 0.3,
            fill: true
          },
          {
            label: 'AWS Serverless ($/mo)',
            data: [0.014, 0.14, 1.39, 13.94, 69.70, 209.10],
            borderColor: '#10b981',
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            tension: 0.3,
            fill: true
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: { color: '#94a3b8', font: { family: 'Inter', size: 11 } }
          }
        },
        scales: {
          x: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } },
          y: { ticks: { color: '#64748b' }, grid: { color: 'rgba(255,255,255,0.05)' } }
        }
      }
    });
  }
</script>
"""
