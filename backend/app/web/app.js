const state = {
  token: localStorage.getItem("epe_token") || "",
  currentView: "summary",
  version: "v0.5.1",
  build: "2026.02.25-local-05",
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

const viewTitle = {
  summary: "Resumo",
  usage: "Uso",
  emails: "Emails",
  documents: "Documentos",
  review: "Revisão",
  configs: "Configurações",
  "test-ai": "Teste IA",
};

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
          if (typeof value === "boolean") return `<td>${value ? "Sim" : "Não"}</td>`;
          if (typeof value === "object" && value !== null) return `<td><pre class="json-mini">${escapeHtml(JSON.stringify(value, null, 2))}</pre></td>`;
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

function renderConfigs(data) {
  return `
    <div class="configs-grid">
      <section class="card-lite">
        <h3>Regras</h3>
        <div class="field"><label>Nome da regra</label><input id="ruleName" type="text" placeholder="ex: nota_fiscal_regra" /></div>
        <div class="field"><label>Definição (JSON)</label><textarea id="ruleDefinition" rows="5" placeholder='{"contains": ["nota fiscal"]}'></textarea></div>
        <button id="saveRuleBtn" class="primary-btn">Salvar regra</button>
        <p id="ruleStatus" class="status ok"></p>
        ${renderTable(
          [
            { key: "id", label: "ID" },
            { key: "rule_name", label: "Nome" },
            { key: "is_active", label: "Ativa" },
            { key: "definition", label: "Definição" },
          ],
          data.rules,
        )}
      </section>

      <section class="card-lite">
        <h3>Prompts</h3>
        <div class="field"><label>Nome do prompt</label><input id="promptName" type="text" placeholder="ex: classificacao_base" /></div>
        <div class="field"><label>Prompt</label><textarea id="promptBody" rows="5" placeholder="Texto do prompt"></textarea></div>
        <button id="savePromptBtn" class="primary-btn">Salvar prompt</button>
        <p id="promptStatus" class="status ok"></p>
        ${renderTable(
          [
            { key: "id", label: "ID" },
            { key: "name", label: "Nome" },
            { key: "is_active", label: "Ativo" },
            { key: "prompt", label: "Prompt" },
          ],
          data.prompts,
        )}
      </section>

      <section class="card-lite">
        <h3>Schemas</h3>
        <div class="field"><label>Tipo de documento</label><input id="schemaDocType" type="text" placeholder="ex: invoice" /></div>
        <div class="field"><label>Schema (JSON)</label><textarea id="schemaBody" rows="5" placeholder='{"type":"object","properties":{}}'></textarea></div>
        <button id="saveSchemaBtn" class="primary-btn">Salvar schema</button>
        <p id="schemaStatus" class="status ok"></p>
        ${renderTable(
          [
            { key: "id", label: "ID" },
            { key: "doc_type", label: "Tipo" },
            { key: "is_active", label: "Ativo" },
            { key: "schema", label: "Schema" },
          ],
          data.schemas,
        )}
      </section>
    </div>
  `;
}

function renderTestAi() {
  return `
    <div class="card-lite">
      <h3>Teste de Classificação e Extração</h3>
      <div class="field"><label>Arquivo (PDF / imagem / texto)</label><input id="testFile" type="file" /></div>
      <div class="field"><label>Assunto</label><input id="testSubject" type="text" placeholder="ex: NF-e 1234 fornecedor X" /></div>
      <div class="field"><label>Remetente</label><input id="testSender" type="text" placeholder="ex: financeiro@fornecedor.com" /></div>
      <div class="field"><label>Corpo do email (opcional)</label><textarea id="testBody" rows="4" placeholder="Texto adicional do email"></textarea></div>
      <button id="runTestAiBtn" class="primary-btn">Analisar Arquivo</button>
      <p id="testAiStatus" class="status"></p>
      <div id="testAiResult"></div>
      <h3 style="margin-top:20px;">Histórico de Testes</h3>
      <div id="testAiHistory"></div>
    </div>
  `;
}

function renderTestAiResult(data) {
  return `
    <div class="test-result-grid">
      <div class="metric"><h4>Arquivo</h4><div class="value test-small">${data.filename || "-"}</div></div>
      <div class="metric"><h4>Tipo</h4><div class="value test-small">${data.doc_type || "-"}</div></div>
      <div class="metric"><h4>Revisão</h4><div class="value test-small">${data.needs_review ? "Sim" : "Não"}</div></div>
      <div class="metric"><h4>Válido</h4><div class="value test-small">${data.valid ? "Sim" : "Não"}</div></div>
    </div>
    <div class="table-card">
      <table>
        <tbody>
          <tr><th>Classificação</th><td><pre class="json-mini">${escapeHtml(JSON.stringify(data.classification || {}, null, 2))}</pre></td></tr>
          <tr><th>Extração</th><td><pre class="json-mini">${escapeHtml(JSON.stringify(data.extraction || {}, null, 2))}</pre></td></tr>
          <tr><th>Erros</th><td><pre class="json-mini">${escapeHtml(JSON.stringify(data.errors || [], null, 2))}</pre></td></tr>
          <tr><th>Texto extraído (preview)</th><td><pre class="json-mini">${escapeHtml(data.text_preview || "")}</pre></td></tr>
        </tbody>
      </table>
    </div>
  `;
}

function renderTestAiHistory(items) {
  return renderTable(
    [
      { key: "created_at", label: "Data/Hora" },
      { key: "filename", label: "Arquivo" },
      { key: "doc_type", label: "Tipo" },
      { key: "category", label: "Categoria" },
      { key: "confidence", label: "Confiança" },
      { key: "status", label: "Status" },
      { key: "valid", label: "Válido" },
    ],
    items || [],
  );
}

function renderView(view, data) {
  if (view === "summary") return renderSummary(data);
  if (view === "usage") return renderUsage(data);
  if (view === "configs") return renderConfigs(data);
  if (view === "test-ai") return renderTestAi();
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

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
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

async function apiPost(path, payload) {
  const res = await fetch(path, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${state.token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status} - ${text}`);
  }
  return await res.json();
}

async function apiPostForm(path, formData) {
  const res = await fetch(path, {
    method: "POST",
    headers: { Authorization: `Bearer ${state.token}` },
    body: formData,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status} - ${text}`);
  }
  return await res.json();
}

async function loadView() {
  if (!state.token) return;
  panelTitle.textContent = viewTitle[state.currentView] || state.currentView;
  panelBody.innerHTML = `<div class="empty">Carregando...</div>`;
  try {
    let data;
    if (state.currentView === "configs") {
      const [rules, prompts, schemas] = await Promise.all([
        apiGet("/api/v1/configs/rules?limit=20"),
        apiGet("/api/v1/configs/prompts?limit=20"),
        apiGet("/api/v1/configs/schemas?limit=20"),
      ]);
      data = { rules, prompts, schemas };
    } else if (state.currentView === "test-ai") {
      data = {};
    } else {
      data = await apiGet(endpoints[state.currentView]);
    }
    panelBody.innerHTML = renderView(state.currentView, data);
    if (state.currentView === "configs") bindConfigActions();
    if (state.currentView === "test-ai") bindTestAiActions();
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

function parseJsonField(text, statusEl) {
  try {
    return JSON.parse(text);
  } catch (_err) {
    statusEl.textContent = "JSON inválido.";
    statusEl.classList.remove("ok");
    return null;
  }
}

function bindConfigActions() {
  const ruleBtn = document.getElementById("saveRuleBtn");
  const promptBtn = document.getElementById("savePromptBtn");
  const schemaBtn = document.getElementById("saveSchemaBtn");

  if (!ruleBtn || !promptBtn || !schemaBtn) return;

  ruleBtn.addEventListener("click", async () => {
    const status = document.getElementById("ruleStatus");
    status.textContent = "";
    status.classList.add("ok");

    const rule_name = document.getElementById("ruleName").value.trim();
    const definitionText = document.getElementById("ruleDefinition").value.trim();
    if (!rule_name || !definitionText) {
      status.textContent = "Preencha os campos da regra.";
      status.classList.remove("ok");
      return;
    }

    const definition = parseJsonField(definitionText, status);
    if (!definition) return;

    try {
      await apiPost("/api/v1/configs/rules", { rule_name, definition });
      status.textContent = "Regra salva com sucesso.";
      status.classList.add("ok");
      await loadView();
    } catch (err) {
      status.textContent = `Erro ao salvar regra: ${err.message}`;
      status.classList.remove("ok");
    }
  });

  promptBtn.addEventListener("click", async () => {
    const status = document.getElementById("promptStatus");
    status.textContent = "";
    status.classList.add("ok");

    const name = document.getElementById("promptName").value.trim();
    const prompt = document.getElementById("promptBody").value.trim();
    if (!name || !prompt) {
      status.textContent = "Preencha os campos do prompt.";
      status.classList.remove("ok");
      return;
    }

    try {
      await apiPost("/api/v1/configs/prompts", { name, prompt });
      status.textContent = "Prompt salvo com sucesso.";
      status.classList.add("ok");
      await loadView();
    } catch (err) {
      status.textContent = `Erro ao salvar prompt: ${err.message}`;
      status.classList.remove("ok");
    }
  });

  schemaBtn.addEventListener("click", async () => {
    const status = document.getElementById("schemaStatus");
    status.textContent = "";
    status.classList.add("ok");

    const doc_type = document.getElementById("schemaDocType").value.trim();
    const schemaText = document.getElementById("schemaBody").value.trim();
    if (!doc_type || !schemaText) {
      status.textContent = "Preencha os campos do schema.";
      status.classList.remove("ok");
      return;
    }

    const schema = parseJsonField(schemaText, status);
    if (!schema) return;

    try {
      await apiPost("/api/v1/configs/schemas", { doc_type, schema });
      status.textContent = "Schema salvo com sucesso.";
      status.classList.add("ok");
      await loadView();
    } catch (err) {
      status.textContent = `Erro ao salvar schema: ${err.message}`;
      status.classList.remove("ok");
    }
  });
}

function bindTestAiActions() {
  const button = document.getElementById("runTestAiBtn");
  if (!button) return;

  loadTestAiHistory();

  button.addEventListener("click", async () => {
    const status = document.getElementById("testAiStatus");
    const result = document.getElementById("testAiResult");
    const fileInput = document.getElementById("testFile");
    const subject = document.getElementById("testSubject").value.trim();
    const sender = document.getElementById("testSender").value.trim();
    const body_text = document.getElementById("testBody").value.trim();

    status.textContent = "";
    status.classList.remove("ok");
    result.innerHTML = "";

    if (!fileInput.files || !fileInput.files[0]) {
      status.textContent = "Selecione um arquivo para análise.";
      return;
    }

    const form = new FormData();
    form.append("file", fileInput.files[0]);
    form.append("subject", subject);
    form.append("sender", sender);
    form.append("body_text", body_text);

    try {
      status.textContent = "Processando...";
      status.classList.add("ok");
      const data = await apiPostForm("/api/v1/documents/test-analyze", form);
      status.textContent = "Análise concluída.";
      result.innerHTML = renderTestAiResult(data);
      await loadTestAiHistory();
    } catch (err) {
      status.textContent = `Erro na análise: ${err.message}`;
      status.classList.remove("ok");
    }
  });
}

async function loadTestAiHistory() {
  const target = document.getElementById("testAiHistory");
  if (!target) return;
  try {
    const items = await apiGet("/api/v1/documents/test-history?limit=20");
    target.innerHTML = renderTestAiHistory(
      (items || []).map((i) => ({
        ...i,
        created_at: i.created_at ? new Date(i.created_at).toLocaleString("pt-BR") : "-",
        confidence: i.confidence ?? "-",
      })),
    );
  } catch (err) {
    target.innerHTML = `<div class="empty">Erro ao carregar histórico: ${err.message}</div>`;
  }
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
