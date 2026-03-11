const { contextBridge } = require("electron");

const API_BASE = "http://127.0.0.1:8000";

contextBridge.exposeInMainWorld("api", {
  submitCommand: async (message) => {
    const res = await fetch(`${API_BASE}/command`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });
    return res.json();
  },

  getPlan: async (planId) => {
    const res = await fetch(`${API_BASE}/plan/${planId}`);
    return res.json();
  },

  approvePlan: async (planId, stepIds = null) => {
    const body = stepIds ? { step_ids: stepIds } : {};
    const res = await fetch(`${API_BASE}/plan/${planId}/approve`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return res.json();
  },

  rejectPlan: async (planId) => {
    const res = await fetch(`${API_BASE}/plan/${planId}/reject`, {
      method: "POST",
    });
    return res.json();
  },

  getTools: async () => {
    const res = await fetch(`${API_BASE}/tools`);
    return res.json();
  },

  connectWebSocket: (onMessage) => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws");
    ws.onmessage = (event) => onMessage(JSON.parse(event.data));
    ws.onclose = () => setTimeout(() => contextBridge, 3000);
    return ws;
  },
});
