const state = {
  token: localStorage.getItem("epe_token") || "",
  currentView: "summary",
  version: "v0.3.0",
  build: "2026.02.25-local-02",
};

const endpoints = {
  summary: "/api/v1/dashboard/summary",
  usage: "/api/v1/dashboard/usage",
  emails: "/api/v1/emails",
  documents: "/api/v1/documents",
  review: "/api/v1/review",
};

const versionLine = document.getElementById("versionLine");
const buildLine = document.getElementById("buildLine");
const loginCard = document.getElementById("loginCard");
const panelCard = document.getElementById("panelCard");
const panelTitle = document.getElementById("panelTitle");
const panelBody = document.getElementById("panelBody");
const loginBtn = document.getElementById("loginBtn");
const loginStatus = document.getElementById("loginStatus");
const refreshBtn = document.getElementById("refreshBtn");
const logoutBtn = document.getElementById("logoutBtn");

function statusBadge(status) {
  const s = (status || "").toLowerCase();
  if (s.includes("done")) return `<span class="badge done">${status}</span>`;
  if (s.includes("fail")) return `<span class="badge failed">${status}</span>`;
  if (s.includes("review")) return `<span class="badge review">${status}</span>`;
  return `<span class="badge processing">${status || "-"}</span>`;
}

function renderTable(columns, rows) {
  if (!rows || rows.length === 0) return `<div class="empty">Sem dados para exibir.</div>`;
  const head = columns.map((c) => `<th>${c.label}</th>`).join("");
  const body = rows
    .map((row) => {
      const tds = columns
        .map((c) => {
          const value = row[c.key];
          if (c.key === "status") return `<td>${statusBadge(value)}</td>`;
          return `<td>${value ?? "-"}</td>`;
        })
        .join("");
      return `<tr>${tds}</tr>`;
    })
    .join("");
  return `<div class="table-card"><table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table></div>`;
}

function renderSummary(data) {
  return `
    <div class="cards-grid">
      <div class="metric"><h4>Emails</h4><div class="value">${data.emails ?? 0}</div></div>
      <div class="metric"><h4>Documentos</h4><div class="value">${data.documents ?? 0}</div></div>
      <div class="metric"><h4>Precisa Revisão</h4><div class="value">${data.needs_review ?? 0}</div></div>
    </div>
  `;
}

function renderUsage(data) {
  return `
    <div class="cards-grid">
      <div class="metric"><h4>Período</h4><div class="value" style="font-size:18px;">${data.period ?? "-"}</div></div>
      <div class="metric"><h4>Emails Processados</h4><div class="value">${data.emails_processed ?? 0}</div></div>
      <div class="metric"><h4>Chamadas LLM</h4><div class="value">${data.llm_calls ?? 0}</div></div>
    </div>
  `;
}

function renderView(view, data) {
  if (view === "summary") return renderSummary(data);
  if (view === "usage") return renderUsage(data);
  if (view === "emails") {
    return renderTable(
      [
        { key: "id", label: "ID" },
        { key: "subject", label: "Assunto" },
        { key: "sender", label: "Remetente" },
        { key: "status", label: "Status" },
      ],
      data,
    );
  }
  if (view === "documents") {
    return renderTable(
      [
        { key: "id", label: "ID" },
        { key: "doc_type", label: "Tipo" },
        { key: "status", label: "Status" },
        { key: "needs_review", label: "Revisão" },
      ],
      data,
    );
  }
  return renderTable(
    [
      { key: "id", label: "ID" },
      { key: "status", label: "Status" },
      { key: "trace_id", label: "Trace" },
    ],
    data,
  );
}

function paintVersion() {
  versionLine.textContent = `version: ${state.version}`;
  buildLine.textContent = `build: ${state.build}`;
}

async function apiGet(path) {
  const res = await fetch(path, {
    headers: { Authorization: `Bearer ${state.token}` },
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status} - ${text}`);
  }
  return await res.json();
}

async function loadView() {
  if (!state.token) return;
  panelTitle.textContent = state.currentView[0].toUpperCase() + state.currentView.slice(1);
  panelBody.innerHTML = `<div class="empty">Carregando...</div>`;
  try {
    const data = await apiGet(endpoints[state.currentView]);
    panelBody.innerHTML = renderView(state.currentView, data);
  } catch (err) {
    panelBody.innerHTML = `<div class="empty">Erro: ${err.message}</div>`;
  }
}

function setAuthenticatedUI(authenticated) {
  loginCard.hidden = authenticated;
  panelCard.hidden = !authenticated;
}

async function login() {
  const email = document.getElementById("emailInput").value.trim();
  const password = document.getElementById("passwordInput").value;
  if (!email || !password) {
    loginStatus.textContent = "Preencha email e senha.";
    return;
  }

  const body = new URLSearchParams({ username: email, password });
  const res = await fetch("/api/v1/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) {
    loginStatus.textContent = "Falha de login.";
    return;
  }

  const data = await res.json();
  state.token = data.access_token;
  localStorage.setItem("epe_token", state.token);
  setAuthenticatedUI(true);
  loginStatus.textContent = "";
  await loadView();
}

function logout() {
  state.token = "";
  localStorage.removeItem("epe_token");
  setAuthenticatedUI(false);
  panelBody.innerHTML = "";
}

function bindMenu() {
  document.querySelectorAll(".menu-item").forEach((btn) => {
    btn.addEventListener("click", async () => {
      document.querySelectorAll(".menu-item").forEach((el) => el.classList.remove("active"));
      btn.classList.add("active");
      state.currentView = btn.dataset.view;
      await loadView();
    });
  });
}

loginBtn.addEventListener("click", login);
refreshBtn.addEventListener("click", loadView);
logoutBtn.addEventListener("click", logout);
paintVersion();
bindMenu();
setAuthenticatedUI(Boolean(state.token));
if (state.token) loadView();
