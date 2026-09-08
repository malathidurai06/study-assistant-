/**
 * StudyDesk PRO — Client Logic & State Manager
 */

const API_BASE = (window.location.origin && window.location.origin.startsWith("http")) 
  ? window.location.origin 
  : "http://localhost:8000";
let SESSION_ID = "session-" + Math.random().toString(36).slice(2, 10);
let currentMode = "general";
let chatHistory = []; // stores all messages for export

// DOM Elements
const sidebar = document.getElementById("sidebar");
const sidebarToggle = document.getElementById("sidebarToggle");
const chatViewport = document.getElementById("chatViewport");
const welcomeHero = document.getElementById("welcomeHero");
const messagesContainer = document.getElementById("messagesContainer");
const chatForm = document.getElementById("chatForm");
const chatInput = document.getElementById("chatInput");
const voiceBtn = document.getElementById("voiceBtn");
const materialsList = document.getElementById("materialsList");
const materialsCount = document.getElementById("materialsCount");
const fileInput = document.getElementById("fileInput");
const topicsCloud = document.getElementById("topicsCloud");
const modeChips = document.querySelectorAll(".mode-chips .chip");
const starterCards = document.querySelectorAll(".starter-card");
const exportBtn = document.getElementById("exportBtn");
const clearChatBtn = document.getElementById("clearChatBtn");
const sessionPill = document.getElementById("sessionPill");
const backendStatus = document.getElementById("backendStatus");

// AI Tools DOM
const quizTopic = document.getElementById("quizTopic");
const quizBtn = document.getElementById("quizBtn");
const planDays = document.getElementById("planDays");
const planBtn = document.getElementById("planBtn");
const flashcardTopic = document.getElementById("flashcardTopic");
const flashcardBtn = document.getElementById("flashcardBtn");

// Configure Marked.js with Highlight.js
if (window.marked && window.hljs) {
  marked.setOptions({
    highlight: function (code, lang) {
      const language = hljs.getLanguage(lang) ? lang : "plaintext";
      return hljs.highlight(code, { language }).value;
    },
    langPrefix: "hljs language-",
    breaks: true,
    gfm: true,
  });
}

// ==========================================================================
// Initialization
// ==========================================================================
document.addEventListener("DOMContentLoaded", () => {
  refreshMaterials();
  refreshTopics();
  setupAutoResize();
  setupVoiceRecognition();
});

// Sidebar Toggle
sidebarToggle?.addEventListener("click", () => {
  sidebar.classList.toggle("collapsed");
});

// Mode Selection
modeChips.forEach((chip) => {
  chip.addEventListener("click", () => {
    modeChips.forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    currentMode = chip.getAttribute("data-mode") || "general";
  });
});

// Starter Cards Clicks
starterCards.forEach((card) => {
  card.addEventListener("click", () => {
    const prompt = card.getAttribute("data-prompt");
    const mode = card.getAttribute("data-mode") || "general";
    
    // Set active mode
    modeChips.forEach((c) => {
      if (c.getAttribute("data-mode") === mode) {
        c.classList.add("active");
        currentMode = mode;
      } else {
        c.classList.remove("active");
      }
    });

    submitMessage(prompt);
  });
});

// ==========================================================================
// Message Rendering
// ==========================================================================
function appendMessage(role, content, sources = [], isHtml = false) {
  if (welcomeHero) {
    welcomeHero.style.display = "none";
  }

  const row = document.createElement("div");
  row.className = `msg-row ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.innerHTML = role === "user" ? "👤" : "⚡";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";

  if (isHtml) {
    bubble.innerHTML = content;
  } else if (role === "assistant") {
    // Render Markdown
    bubble.innerHTML = window.marked ? marked.parse(content) : `<p>${content}</p>`;
    // Attach copy buttons to all pre blocks
    enhanceCodeBlocks(bubble);
  } else {
    // User message (plain text safe)
    const p = document.createElement("p");
    p.textContent = content;
    bubble.appendChild(p);
  }

  // Sources pill container
  if (sources && sources.length > 0) {
    const srcContainer = document.createElement("div");
    srcContainer.className = "sources-container";
    srcContainer.innerHTML = `<span class="source-label">Grounded in:</span>`;
    sources.forEach((s) => {
      const pill = document.createElement("span");
      pill.className = "source-pill";
      pill.textContent = `📄 ${s}`;
      srcContainer.appendChild(pill);
    });
    bubble.appendChild(srcContainer);
  }

  if (role === "assistant") {
    row.appendChild(avatar);
    row.appendChild(bubble);
  } else {
    row.appendChild(bubble);
  }

  messagesContainer.appendChild(row);
  scrollToBottom();

  // Save for session export
  chatHistory.push({ role, content, sources, timestamp: new Date().toLocaleTimeString() });

  return bubble;
}

function showThinking(text = "Analyzing & synthesizing solution…") {
  if (welcomeHero) welcomeHero.style.display = "none";

  const row = document.createElement("div");
  row.className = "msg-row assistant thinking-row";

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.innerHTML = "⚡";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.innerHTML = `
    <div class="thinking-pulse">
      <div class="dot-flashing"></div>
      <span style="margin-left: 16px;">${text}</span>
    </div>
  `;

  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesContainer.appendChild(row);
  scrollToBottom();

  return row;
}

function scrollToBottom() {
  setTimeout(() => {
    chatViewport.scrollTop = chatViewport.scrollHeight;
  }, 50);
}

function enhanceCodeBlocks(container) {
  const preElements = container.querySelectorAll("pre");
  preElements.forEach((pre) => {
    const code = pre.querySelector("code");
    const lang = code ? (code.className.match(/language-([a-z0-9]+)/i) || ["", "code"])[1] : "code";

    const header = document.createElement("div");
    header.className = "code-header";
    header.innerHTML = `
      <span>${lang.toUpperCase()}</span>
      <button class="btn-copy-code" title="Copy code to clipboard">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
        <span>Copy</span>
      </button>
    `;

    const copyBtn = header.querySelector(".btn-copy-code");
    copyBtn.addEventListener("click", () => {
      const rawText = code ? code.innerText : pre.innerText;
      navigator.clipboard.writeText(rawText).then(() => {
        copyBtn.innerHTML = `<span>✓ Copied!</span>`;
        setTimeout(() => {
          copyBtn.innerHTML = `
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
            <span>Copy</span>
          `;
        }, 2000);
      });
    });

    pre.insertBefore(header, pre.firstChild);
  });
}

// ==========================================================================
// Chat Submission
// ==========================================================================
async function submitMessage(message) {
  if (!message || !message.trim()) return;
  const msg = message.trim();

  appendMessage("user", msg);
  chatInput.value = "";
  chatInput.style.height = "auto";

  const thinkingRow = showThinking();

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: SESSION_ID,
        message: msg,
        mode: currentMode,
      }),
    });

    const data = await res.json();
    thinkingRow.remove();

    if (!res.ok) {
      appendMessage("assistant", `⚠️ **Error:** ${data.detail || "Unable to get response."}`);
      return;
    }

    appendMessage("assistant", data.answer, data.sources_used || []);
    refreshTopics();
  } catch (err) {
    thinkingRow.remove();
    appendMessage(
      "assistant",
      "⚠️ **Connection Error:** Could not connect to the backend server. Please verify that uvicorn is running on port 8000."
    );
  }
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  submitMessage(chatInput.value);
});

chatInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    chatForm.dispatchEvent(new Event("submit"));
  }
});

// ==========================================================================
// AI Tools Handlers
// ==========================================================================

// 1. Quiz Tool
quizBtn.addEventListener("click", async () => {
  const topic = quizTopic.value.trim() || "General Computer Science";
  appendMessage("user", `📝 Generate a practice quiz on: **${topic}**`);
  const thinkingRow = showThinking("Crafting customized practice quiz with explanations…");

  try {
    const res = await fetch(`${API_BASE}/quiz`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: SESSION_ID, topic, num_questions: 5 }),
    });
    const data = await res.json();
    thinkingRow.remove();

    if (!res.ok) {
      appendMessage("assistant", `⚠️ **Quiz Error:** ${data.detail || "Failed to generate quiz."}`);
      return;
    }

    appendMessage("assistant", data.quiz);
    quizTopic.value = "";
    refreshTopics();
  } catch (err) {
    thinkingRow.remove();
    appendMessage("assistant", "⚠️ **Connection Error:** Backend not reachable.");
  }
});

// 2. Study Plan Tool
planBtn.addEventListener("click", async () => {
  const days = parseInt(planDays.value) || 5;
  appendMessage("user", `📅 Build my **${days}-Day Personalized Study Roadmap**`);
  const thinkingRow = showThinking("Synthesizing your session topics into an optimal study plan…");

  try {
    const res = await fetch(`${API_BASE}/study-plan`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: SESSION_ID, days, extra_topics: [] }),
    });
    const data = await res.json();
    thinkingRow.remove();

    if (!res.ok) {
      appendMessage("assistant", `⚠️ **Plan Error:** ${data.detail || "Failed to build plan."}`);
      return;
    }

    appendMessage("assistant", data.plan);
  } catch (err) {
    thinkingRow.remove();
    appendMessage("assistant", "⚠️ **Connection Error:** Backend not reachable.");
  }
});

// 3. Flashcards Tool
flashcardBtn.addEventListener("click", async () => {
  const topic = flashcardTopic.value.trim() || "Course Material";
  appendMessage("user", `📇 Create high-yield flashcards for: **${topic}**`);
  const thinkingRow = showThinking("Creating active recall flashcards…");

  try {
    const res = await fetch(`${API_BASE}/flashcards`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: SESSION_ID, topic, count: 5 }),
    });
    const data = await res.json();
    thinkingRow.remove();

    if (!res.ok) {
      appendMessage("assistant", `⚠️ **Flashcard Error:** ${data.detail || "Failed to create flashcards."}`);
      return;
    }

    appendMessage("assistant", data.flashcards);
    flashcardTopic.value = "";
    refreshTopics();
  } catch (err) {
    thinkingRow.remove();
    appendMessage("assistant", "⚠️ **Connection Error:** Backend not reachable.");
  }
});

// ==========================================================================
// Sidebar Data Managers
// ==========================================================================

async function refreshMaterials() {
  try {
    const res = await fetch(`${API_BASE}/materials`);
    const data = await res.json();
    materialsList.innerHTML = "";

    if (!data.materials || data.materials.length === 0) {
      materialsList.innerHTML = `<li class="empty-state">No materials uploaded yet.</li>`;
      materialsCount.textContent = "0";
      return;
    }

    materialsCount.textContent = data.materials.length;
    data.materials.forEach((file) => {
      const li = document.createElement("li");
      li.textContent = file;
      li.title = `Click to ask questions about ${file}`;
      li.style.cursor = "pointer";
      li.addEventListener("click", () => {
        submitMessage(`Explain the key concepts covered in ${file}`);
      });
      materialsList.appendChild(li);
    });

    if (backendStatus) backendStatus.textContent = "Gemini 3.6 Flash Active";
  } catch (e) {
    materialsList.innerHTML = `<li class="empty-state" style="color: #ef4444;">Backend offline</li>`;
    if (backendStatus) backendStatus.textContent = "Backend Disconnected";
  }
}

async function refreshTopics() {
  try {
    const res = await fetch(`${API_BASE}/topics/${SESSION_ID}`);
    const data = await res.json();
    topicsCloud.innerHTML = "";

    if (!data.topics || data.topics.length === 0) {
      topicsCloud.innerHTML = `<span class="empty-hint">Ask questions to build session memory...</span>`;
      return;
    }

    data.topics.forEach((topic) => {
      const chip = document.createElement("span");
      chip.className = "topic-chip";
      chip.textContent = `# ${topic}`;
      chip.addEventListener("click", () => {
        submitMessage(`Give me a deep dive explanation with examples on ${topic}`);
      });
      topicsCloud.appendChild(chip);
    });
  } catch (e) {
    // Ignore silent polling error
  }
}

// File Upload Handler
fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
    const data = await res.json();
    fileInput.value = "";
    refreshMaterials();
    appendMessage("assistant", `✅ Successfully indexed **${file.name}** into course materials! You can now ask questions about it.`);
  } catch (err) {
    alert("Failed to upload note file to backend.");
  }
});

// ==========================================================================
// Utilities: Voice, Export, Clear, Auto-resize
// ==========================================================================

function setupAutoResize() {
  chatInput.addEventListener("input", function () {
    this.style.height = "auto";
    this.style.height = Math.min(this.scrollHeight, 160) + "px";
  });
}

function setupVoiceRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    if (voiceBtn) voiceBtn.style.display = "none";
    return;
  }

  const recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = "en-US";

  let isRecording = false;

  voiceBtn.addEventListener("click", () => {
    if (isRecording) {
      recognition.stop();
      return;
    }
    try {
      recognition.start();
      isRecording = true;
      voiceBtn.classList.add("recording");
      voiceBtn.title = "Listening... Speak now";
    } catch (e) {
      console.error(e);
    }
  });

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    chatInput.value = (chatInput.value + " " + transcript).trim();
    chatInput.focus();
  };

  recognition.onend = () => {
    isRecording = false;
    voiceBtn.classList.remove("recording");
    voiceBtn.title = "Voice Input (Speech-to-text)";
  };

  recognition.onerror = () => {
    isRecording = false;
    voiceBtn.classList.remove("recording");
  };
}

// Export Notes as Markdown
exportBtn.addEventListener("click", () => {
  if (chatHistory.length === 0) {
    alert("No study notes in this session yet!");
    return;
  }

  let mdContent = `# 📚 StudyDesk Learning Session Notes\n*Date: ${new Date().toLocaleDateString()}*\n\n---\n\n`;

  chatHistory.forEach((item) => {
    if (item.role === "user") {
      mdContent += `### ❓ Question / Prompt (${item.timestamp})\n${item.content}\n\n`;
    } else {
      mdContent += `### 💡 AI Solution\n${item.content}\n\n`;
      if (item.sources && item.sources.length) {
        mdContent += `*Sources cited: ${item.sources.join(", ")}*\n\n`;
      }
      mdContent += `---\n\n`;
    }
  });

  const blob = new Blob([mdContent], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `StudyDesk_Notes_${new Date().toISOString().slice(0, 10)}.md`;
  a.click();
  URL.revokeObjectURL(url);
});

// Clear Chat / Reset Session
clearChatBtn.addEventListener("click", async () => {
  if (!confirm("Are you sure you want to clear your current study session?")) return;

  try {
    await fetch(`${API_BASE}/clear/${SESSION_ID}`, { method: "POST" });
  } catch (e) {}

  SESSION_ID = "session-" + Math.random().toString(36).slice(2, 10);
  chatHistory = [];
  messagesContainer.innerHTML = "";
  if (welcomeHero) welcomeHero.style.display = "flex";
  refreshTopics();
});
