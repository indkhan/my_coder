// UI logic for my_operator Electron app

const chatLog = document.getElementById("chat-log");
const planPanel = document.getElementById("plan-panel");
const logsPanel = document.getElementById("logs-panel");
const commandInput = document.getElementById("command-input");
const sendBtn = document.getElementById("send-btn");
const settingsBtn = document.getElementById("settings-btn");
const settingsModal = document.getElementById("settings-modal");
const settingsClose = document.getElementById("settings-close");

let currentPlanId = null;

// --- WebSocket ---
function connectWS() {
  window.api.connectWebSocket((event) => {
    addLog(event);
    if (event.type === "plan_completed" || event.type === "plan_failed") {
      refreshPlan();
    }
  });
}

// --- Chat ---
function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `message ${role}`;
  div.textContent = text;
  chatLog.appendChild(div);
  chatLog.scrollTop = chatLog.scrollHeight;
}

function addLog(event) {
  const div = document.createElement("div");
  div.className = "log-entry";
  div.textContent = `[${event.type}] ${JSON.stringify(event)}`;
  logsPanel.appendChild(div);
  logsPanel.scrollTop = logsPanel.scrollHeight;
}

// --- Plan rendering ---
function renderPlan(plan) {
  currentPlanId = plan.plan_id;
  planPanel.innerHTML = "";

  const header = document.createElement("h3");
  header.textContent = `Plan: ${plan.status}`;
  planPanel.appendChild(header);

  if (plan.reasoning) {
    const reasoning = document.createElement("p");
    reasoning.className = "reasoning";
    reasoning.textContent = plan.reasoning;
    planPanel.appendChild(reasoning);
  }

  const stepsList = document.createElement("div");
  stepsList.className = "steps-list";

  plan.steps.forEach((step, i) => {
    const stepDiv = document.createElement("div");
    stepDiv.className = `step ${step.status.toLowerCase()}`;
    stepDiv.innerHTML = `
      <span class="step-num">${i + 1}</span>
      <span class="risk risk-${step.risk_level.toLowerCase()}">${step.risk_level}</span>
      <span class="step-desc">${step.description}</span>
      <span class="step-tool">${step.tool_name}</span>
      <span class="step-status">${step.status}</span>
      ${step.result ? `<div class="step-result">${step.result.substring(0, 300)}</div>` : ""}
      ${step.error ? `<div class="step-error">${step.error}</div>` : ""}
    `;
    stepsList.appendChild(stepDiv);
  });

  planPanel.appendChild(stepsList);

  if (plan.status === "AWAITING_APPROVAL") {
    const actions = document.createElement("div");
    actions.className = "plan-actions";

    const approveBtn = document.createElement("button");
    approveBtn.className = "btn approve";
    approveBtn.textContent = "Approve";
    approveBtn.onclick = () => approvePlan();

    const rejectBtn = document.createElement("button");
    rejectBtn.className = "btn reject";
    rejectBtn.textContent = "Reject";
    rejectBtn.onclick = () => rejectPlan();

    actions.appendChild(approveBtn);
    actions.appendChild(rejectBtn);
    planPanel.appendChild(actions);
  }
}

// --- Actions ---
async function submitCommand() {
  const msg = commandInput.value.trim();
  if (!msg) return;
  commandInput.value = "";
  addMessage("user", msg);
  sendBtn.disabled = true;

  try {
    const plan = await window.api.submitCommand(msg);
    addMessage("assistant", `Plan generated (${plan.steps.length} steps) — ${plan.status}`);
    renderPlan(plan);
  } catch (e) {
    addMessage("error", `Error: ${e.message}`);
  } finally {
    sendBtn.disabled = false;
  }
}

async function approvePlan() {
  if (!currentPlanId) return;
  try {
    const plan = await window.api.approvePlan(currentPlanId);
    addMessage("assistant", `Plan approved and executing...`);
    renderPlan(plan);
  } catch (e) {
    addMessage("error", `Error: ${e.message}`);
  }
}

async function rejectPlan() {
  if (!currentPlanId) return;
  try {
    const plan = await window.api.rejectPlan(currentPlanId);
    addMessage("assistant", `Plan rejected.`);
    renderPlan(plan);
  } catch (e) {
    addMessage("error", `Error: ${e.message}`);
  }
}

async function refreshPlan() {
  if (!currentPlanId) return;
  try {
    const plan = await window.api.getPlan(currentPlanId);
    renderPlan(plan);
  } catch (e) {
    /* ignore */
  }
}

// --- Settings ---
settingsBtn.addEventListener("click", () => {
  settingsModal.classList.toggle("hidden");
});
settingsClose.addEventListener("click", () => {
  settingsModal.classList.add("hidden");
});

// --- Events ---
sendBtn.addEventListener("click", submitCommand);
commandInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    submitCommand();
  }
});

// --- Init ---
connectWS();
