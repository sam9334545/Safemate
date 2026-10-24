/**
 * Safemate Safety Assistant — Client Application
 * Connects directly to Safemate Backend API (/api/v1/chatbot/*)
 */

(function () {
  "use strict";

  // Application State
  const state = {
    sessionId: "sess_" + Math.random().toString(36).substring(2, 12),
    currentFlowId: null,
    currentStepId: null,
    country: "IN",
    flows: [],
    isLoading: false,
  };

  // DOM Elements
  const elements = {
    chatMain: document.getElementById("chatMain"),
    messagesContainer: document.getElementById("messagesContainer"),
    welcomeHero: document.getElementById("welcomeHero"),
    cardsGrid: document.getElementById("cardsGrid"),
    composerForm: document.getElementById("composerForm"),
    composerInput: document.getElementById("composerInput"),
    btnSend: document.getElementById("btnSend"),
    btnReset: document.getElementById("btnReset"),
    btnEmergencyHeader: document.getElementById("btnEmergencyHeader"),
    emergencyModal: document.getElementById("emergencyModal"),
    btnCloseModal: document.getElementById("btnCloseModal"),
    feedbackModal: document.getElementById("feedbackModal"),
    btnCloseFeedback: document.getElementById("btnCloseFeedback"),
    btnOpenFeedback: document.getElementById("btnOpenFeedback"),
    feedbackForm: document.getElementById("feedbackForm"),
    feedbackComment: document.getElementById("feedbackComment"),
    feedbackRating: document.getElementById("feedbackRating"),
  };

  // Fallback Quick Action Cards (used while API loads or if offline)
  const FALLBACK_FLOWS = [
    { flow_id: "immediate_danger", title: "Immediate Danger", subtitle: "Active physical threat, being followed, or urgent crisis", icon: "🚨", is_emergency: true },
    { flow_id: "online_harassment", title: "Online Harassment", subtitle: "Cyberstalking, trolling, abusive messages, or threats", icon: "💬" },
    { flow_id: "blackmail_threats", title: "Blackmail or Threats", subtitle: "Extortion, sextortion, or monetary coercion", icon: "⚠️" },
    { flow_id: "intimate_image_abuse", title: "Non-consensual Images", subtitle: "Unauthorized photo/video sharing or AI deepfakes", icon: "🛑" },
    { flow_id: "impersonation_fake_profile", title: "Fake Profile / Impersonation", subtitle: "Cloned accounts or identity theft", icon: "👤" },
    { flow_id: "physical_harassment", title: "Physical Harassment", subtitle: "Street stalking, eve-teasing, or workplace safety", icon: "🛡️" },
    { flow_id: "report_cybercrime_india", title: "Report Cybercrime in India", subtitle: "Walkthrough for cybercrime.gov.in & 1930", icon: "📋" },
    { flow_id: "preserve_evidence", title: "Preserve Evidence Safely", subtitle: "Screenshot best practices & Safemate Evidence Vault", icon: "📦" },
    { flow_id: "understand_options", title: "Understand My Options", subtitle: "Legal rights under Indian law & support pathways", icon: "🧭" },
  ];

  // Initialize
  async function init() {
    setupEventListeners();
    await fetchFlows();
  }

  function setupEventListeners() {
    // Form submission
    elements.composerForm.addEventListener("submit", handleUserSubmit);

    // Reset button
    elements.btnReset.addEventListener("click", resetConversation);

    // Emergency header action
    elements.btnEmergencyHeader.addEventListener("click", () => {
      elements.emergencyModal.classList.add("active");
    });
    elements.btnCloseModal.addEventListener("click", () => {
      elements.emergencyModal.classList.remove("active");
    });

    // Feedback modal
    if (elements.btnOpenFeedback) {
      elements.btnOpenFeedback.addEventListener("click", () => {
        elements.feedbackModal.classList.add("active");
      });
    }
    if (elements.btnCloseFeedback) {
      elements.btnCloseFeedback.addEventListener("click", () => {
        elements.feedbackModal.classList.remove("active");
      });
    }
    if (elements.feedbackForm) {
      elements.feedbackForm.addEventListener("submit", handleFeedbackSubmit);
    }

    // Close modal on click outside
    window.addEventListener("click", (e) => {
      if (e.target === elements.emergencyModal) elements.emergencyModal.classList.remove("active");
      if (e.target === elements.feedbackModal) elements.feedbackModal.classList.remove("active");
    });
  }

  // Fetch available flows from API
  async function fetchFlows() {
    try {
      const res = await fetch("/api/v1/chatbot/flows");
      if (res.ok) {
        const data = await res.json();
        state.flows = data.flows || [];
      } else {
        state.flows = FALLBACK_FLOWS;
      }
    } catch (e) {
      state.flows = FALLBACK_FLOWS;
    }
    renderCards(state.flows);
  }

  // Render Initial Quick Action Cards
  function renderCards(flows) {
    elements.cardsGrid.innerHTML = "";
    flows.forEach((flow) => {
      const card = document.createElement("button");
      card.className = `action-card ${flow.flow_id === "immediate_danger" ? "card-emergency" : ""}`;
      card.setAttribute("type", "button");
      card.innerHTML = `
        <div class="card-title">
          <span>${flow.flow_id === "immediate_danger" ? "🚨" : "🛡️"}</span>
          <span>${escapeHtml(flow.title)}</span>
        </div>
        <div class="card-desc">${escapeHtml(flow.subtitle)}</div>
      `;
      card.addEventListener("click", () => startFlow(flow.flow_id));
      elements.cardsGrid.appendChild(card);
    });
  }

  // Start Flow via API
  async function startFlow(flowId) {
    setLoading(true);
    elements.welcomeHero.style.display = "none";
    try {
      const res = await fetch("/api/v1/chatbot/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          flow_id: flowId,
          country: state.country,
          session_id: state.sessionId,
        }),
      });

      if (!res.ok) throw new Error("Failed to start flow");

      const data = await res.json();
      state.currentFlowId = data.flow_id;
      state.currentStepId = data.step_id;
      renderAssistantMessage(data);
    } catch (err) {
      renderErrorMessage("Could not load guided guidance. Please use emergency helplines below if urgent.");
    } finally {
      setLoading(false);
      scrollToBottom();
    }
  }

  // Send message or selection to API
  async function sendMessage({ choiceId = null, messageText = null }) {
    setLoading(true);
    try {
      const res = await fetch("/api/v1/chatbot/message", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: state.sessionId,
          flow_id: state.currentFlowId,
          step_id: state.currentStepId,
          choice_id: choiceId,
          message: messageText,
          country: state.country,
        }),
      });

      if (!res.ok) throw new Error("API call failed");

      const data = await res.json();
      state.currentFlowId = data.flow_id || state.currentFlowId;
      state.currentStepId = data.step_id || state.currentStepId;
      renderAssistantMessage(data);
    } catch (err) {
      renderErrorMessage("An error occurred while contacting the safety engine. In an emergency, dial 112 immediately.");
    } finally {
      setLoading(false);
      scrollToBottom();
    }
  }

  // Handle User Input Submission
  function handleUserSubmit(e) {
    e.preventDefault();
    const text = elements.composerInput.value.trim();
    if (!text || state.isLoading) return;

    elements.welcomeHero.style.display = "none";
    renderUserMessage(text);
    elements.composerInput.value = "";

    sendMessage({ messageText: text });
  }

  // Render User Message
  function renderUserMessage(text) {
    const row = document.createElement("div");
    row.className = "message-row user";
    row.innerHTML = `<div class="bubble">${escapeHtml(text)}</div>`;
    elements.messagesContainer.appendChild(row);
    scrollToBottom();
  }

  // Render Assistant Message with Choices and Resources
  function renderAssistantMessage(data) {
    const row = document.createElement("div");
    row.className = `message-row assistant ${data.is_emergency_priority ? "is-emergency" : ""}`;

    let html = `<div class="bubble">`;

    // Title
    if (data.title) {
      html += `<div class="bubble-title">${escapeHtml(data.title)}</div>`;
    }

    // Guidance text
    const textContent = data.guidance || data.text || "";
    if (textContent) {
      html += `<div class="bubble-text">${escapeHtml(textContent)}</div>`;
    }

    // Numbered steps
    if (data.numbered_steps && data.numbered_steps.length > 0) {
      const stepsId = "steps_" + Math.random().toString(36).substring(2, 9);
      html += `<div class="steps-list" id="${stepsId}">`;
      html += `<ol>`;
      data.numbered_steps.forEach((step) => {
        html += `<li>${escapeHtml(step)}</li>`;
      });
      html += `</ol>`;
      html += `<button type="button" class="copy-steps-btn" data-target="${stepsId}">📋 Copy these steps</button>`;
      html += `</div>`;
    }

    // Technical feature banner
    if (data.safemate_feature_link) {
      html += `
        <div class="feature-banner">
          <div class="feature-info">
            <span class="feature-title">🔗 ${escapeHtml(data.safemate_feature_name || "Safemate Feature")}</span>
            <span class="feature-note">${escapeHtml(data.safemate_feature_note || "Available feature endpoint")}</span>
          </div>
          <a href="${escapeHtml(data.safemate_feature_link)}" class="feature-btn" target="_blank" rel="noopener noreferrer">View Feature</a>
        </div>
      `;
    }

    // Resources list
    if (data.resources && data.resources.length > 0) {
      html += `<div class="resources-section">`;
      html += `<div class="resources-heading">Verified Support & Reporting Resources:</div>`;
      data.resources.forEach((r) => {
        html += `
          <div class="resource-card">
            <div class="resource-header">
              <span class="resource-name">${escapeHtml(r.display_name)}</span>
              ${r.is_emergency ? '<span class="resource-badge" style="background:#FCE8E6;color:#C5221F;">Emergency</span>' : '<span class="resource-badge">Verified Official</span>'}
            </div>
            <div class="resource-desc">${escapeHtml(r.description)}</div>
            <div class="resource-actions">
              ${r.phone_number ? `<a href="tel:${escapeHtml(r.phone_number)}" class="btn-tel">📞 Call ${escapeHtml(r.phone_number)}</a>` : ""}
              ${r.action_url ? `<a href="${escapeHtml(r.action_url)}" class="btn-url" target="_blank" rel="noopener noreferrer">Visit Official Portal ↗</a>` : ""}
            </div>
          </div>
        `;
      });
      html += `</div>`;
    }

    // Disclaimer
    if (data.disclaimer) {
      html += `<div class="disclaimer-text">ℹ️ ${escapeHtml(data.disclaimer)}</div>`;
    }

    // Choices Container
    if (data.choices && data.choices.length > 0) {
      html += `<div class="choices-container">`;
      data.choices.forEach((c) => {
        const isEmerg = c.is_emergency ? "chip-emergency" : "";
        html += `<button type="button" class="choice-chip ${isEmerg}" data-choice-id="${escapeHtml(c.choice_id)}">${escapeHtml(c.label)}</button>`;
      });
      html += `</div>`;
    }

    html += `</div>`;
    row.innerHTML = html;

    // Attach choice chip event listeners
    const chips = row.querySelectorAll(".choice-chip");
    chips.forEach((chip) => {
      chip.addEventListener("click", () => {
        const choiceId = chip.getAttribute("data-choice-id");
        renderUserMessage(chip.textContent);
        sendMessage({ choiceId });
      });
    });

    // Attach copy button listeners
    const copyBtn = row.querySelector(".copy-steps-btn");
    if (copyBtn) {
      copyBtn.addEventListener("click", () => {
        const targetId = copyBtn.getAttribute("data-target");
        const listElem = document.getElementById(targetId);
        if (listElem) {
          const textToCopy = Array.from(listElem.querySelectorAll("li"))
            .map((li, idx) => `${idx + 1}. ${li.textContent}`)
            .join("\n");
          navigator.clipboard.writeText(textToCopy).then(() => {
            copyBtn.textContent = "✓ Steps copied to clipboard!";
            setTimeout(() => { copyBtn.textContent = "📋 Copy these steps"; }, 2500);
          });
        }
      });
    }

    elements.messagesContainer.appendChild(row);
    scrollToBottom();
  }

  // Render Error Message
  function renderErrorMessage(msg) {
    const row = document.createElement("div");
    row.className = "message-row assistant is-emergency";
    row.innerHTML = `
      <div class="bubble">
        <div class="bubble-title">System Notice</div>
        <div class="bubble-text">${escapeHtml(msg)}</div>
        <div class="resources-section">
          <div class="resource-card">
            <div class="resource-header">
              <span class="resource-name">National Emergency Response (112)</span>
              <span class="resource-badge" style="background:#FCE8E6;color:#C5221F;">Emergency</span>
            </div>
            <div class="resource-actions">
              <a href="tel:112" class="btn-tel">📞 Call 112</a>
            </div>
          </div>
          <div class="resource-card">
            <div class="resource-header">
              <span class="resource-name">Women Helpline (181)</span>
              <span class="resource-badge">Crisis Line</span>
            </div>
            <div class="resource-actions">
              <a href="tel:181" class="btn-tel">📞 Call 181</a>
            </div>
          </div>
        </div>
      </div>
    `;
    elements.messagesContainer.appendChild(row);
    scrollToBottom();
  }

  // Handle Feedback Submission
  async function handleFeedbackSubmit(e) {
    e.preventDefault();
    const comment = elements.feedbackComment ? elements.feedbackComment.value.trim() : "";
    const rating = elements.feedbackRating ? elements.feedbackRating.value : "feedback";
    try {
      await fetch("/api/v1/chatbot/feedback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          flow_id: state.currentFlowId,
          step_id: state.currentStepId,
          rating: rating,
          comment: comment,
        }),
      });
      alert("Thank you for your feedback. We review reports to maintain resource accuracy.");
      elements.feedbackModal.classList.remove("active");
      if (elements.feedbackForm) elements.feedbackForm.reset();
    } catch (err) {
      elements.feedbackModal.classList.remove("active");
    }
  }

  // Reset Conversation
  function resetConversation() {
    state.sessionId = "sess_" + Math.random().toString(36).substring(2, 12);
    state.currentFlowId = null;
    state.currentStepId = null;
    elements.messagesContainer.innerHTML = "";
    elements.welcomeHero.style.display = "block";
    renderCards(state.flows.length > 0 ? state.flows : FALLBACK_FLOWS);
    scrollToBottom();
  }

  // Utilities
  function setLoading(loading) {
    state.isLoading = loading;
    elements.btnSend.disabled = loading;
    elements.btnSend.textContent = loading ? "..." : "Send";
  }

  function scrollToBottom() {
    setTimeout(() => {
      elements.chatMain.scrollTop = elements.chatMain.scrollHeight;
    }, 50);
  }

  function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  // Run on page load
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
