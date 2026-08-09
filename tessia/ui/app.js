// TESSIA Hybrid HUD & Error Diagnostic Controller

const canvas = document.getElementById('neural-canvas');
const ctx = canvas.getContext('2d');
const coreBlob = document.getElementById('core-blob');
const chatFeed = document.getElementById('chat-feed');
const userInput = document.getElementById('user-input');
const micBtn = document.getElementById('mic-btn');
const toastBanner = document.getElementById('error-toast');
const toastMessage = document.getElementById('toast-message');

let isThinking = false;
let isSpeaking = false;
let isErrorState = false;
let recognition = null;

// ==========================================
// 1. NEURAL VISUALIZER ENGINE
// ==========================================

function resizeCanvas() {
  if (!canvas) return;
  canvas.width = canvas.clientWidth;
  canvas.height = canvas.clientHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

const numNodes = 22;
const nodes = [];

for (let i = 0; i < numNodes; i++) {
  nodes.push({
    x: Math.random() * (canvas.width || 300),
    y: Math.random() * (canvas.height || 300),
    vx: (Math.random() - 0.5) * 0.8,
    vy: (Math.random() - 0.5) * 0.8,
    radius: Math.random() * 2.5 + 2
  });
}

function animateNeuralNetwork() {
  if (!canvas || !ctx) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  const speedMultiplier = isErrorState ? 0.4 : isThinking ? 2.6 : isSpeaking ? 1.8 : 1.0;

  // Connection Edges
  for (let i = 0; i < nodes.length; i++) {
    for (let j = i + 1; j < nodes.length; j++) {
      const dx = nodes[i].x - nodes[j].x;
      const dy = nodes[i].y - nodes[j].y;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist < 115) {
        ctx.beginPath();
        ctx.moveTo(nodes[i].x, nodes[i].y);
        ctx.lineTo(nodes[j].x, nodes[j].y);
        
        const alpha = (1 - dist / 115) * (isSpeaking ? 0.95 : 0.7);
        ctx.strokeStyle = isErrorState
          ? `rgba(255, 51, 102, ${alpha})`
          : isThinking 
            ? `rgba(220, 100, 255, ${alpha})` 
            : `rgba(0, 242, 255, ${alpha})`;
        ctx.lineWidth = isSpeaking ? 1.4 : 0.9;
        ctx.stroke();
      }
    }
  }

  // Nodes
  nodes.forEach(node => {
    ctx.beginPath();
    ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
    ctx.fillStyle = isErrorState ? '#ff3366' : isThinking ? '#e066ff' : '#00f2ff';
    ctx.shadowBlur = 10;
    ctx.shadowColor = ctx.fillStyle;
    ctx.fill();
    ctx.shadowBlur = 0;

    node.x += node.vx * speedMultiplier;
    node.y += node.vy * speedMultiplier;

    if (node.x < 0 || node.x > canvas.width) node.vx *= -1;
    if (node.y < 0 || node.y > canvas.height) node.vy *= -1;
  });

  requestAnimationFrame(animateNeuralNetwork);
}

animateNeuralNetwork();


// ==========================================
// 2. ERROR & STATUS REPORTING SYSTEM
// ==========================================

function showError(message, inlineMsg = null) {
  isErrorState = true;
  updateVisualizerState();

  // Show floating toast banner
  if (toastBanner && toastMessage) {
    toastMessage.innerText = message;
    toastBanner.classList.add('visible');
  }

  // Update status badge
  const statusIndicator = document.getElementById('status-indicator');
  const statusText = document.getElementById('status-text');
  if (statusIndicator && statusText) {
    statusIndicator.classList.add('error');
    statusText.innerText = "OFFLINE / ERROR";
  }

  // Append system error message bubble in chat feed
  appendMessage('system-error', inlineMsg || `⚠️ ${message}`);
}

function dismissToast() {
  if (toastBanner) {
    toastBanner.classList.remove('visible');
  }
}

function clearErrorState() {
  isErrorState = false;
  dismissToast();

  const statusIndicator = document.getElementById('status-indicator');
  const statusText = document.getElementById('status-text');
  if (statusIndicator && statusText) {
    statusIndicator.classList.remove('error');
    statusText.innerText = "OLLAMA LIVE";
  }
  updateVisualizerState();
}

function updateVisualizerState() {
  if (!coreBlob) return;
  coreBlob.classList.remove('thinking', 'speaking', 'error');

  if (isErrorState) {
    coreBlob.classList.add('error');
  } else if (isThinking) {
    coreBlob.classList.add('thinking');
  } else if (isSpeaking) {
    coreBlob.classList.add('speaking');
  }
}


// ==========================================
// 3. API COMMUNICATION & CHAT LOGIC
// ==========================================

async function sendQuery(overrideText = null) {
  const queryText = overrideText || userInput.value.trim();
  if (!queryText) return;

  if (!overrideText) userInput.value = '';

  clearErrorState();
  appendMessage('user', queryText);
  setThinkingState(true);

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: queryText })
    });

    if (!res.ok) {
      throw new Error(`Server returned status code ${res.status}`);
    }

    const data = await res.json();
    setThinkingState(false);

    const reply = data.reply || "I couldn't generate a response.";
    
    // Check if server returned connection failure message
    if (reply.includes("Unable to reach local Ollama")) {
      showError("Ollama Service Offline", reply);
      return;
    }

    appendMessage('assistant', reply);
    playSpeech(reply);

  } catch (err) {
    setThinkingState(false);
    showError("Connection Failed", "Unable to reach TESSIA backend. Ensure `python3 agent/main.py` is running.");
  }
}

function appendMessage(role, text) {
  const bubble = document.createElement('div');
  bubble.className = `chat-bubble ${role}`;
  bubble.innerText = text;
  chatFeed.appendChild(bubble);
  chatFeed.scrollTop = chatFeed.scrollHeight;
}

function setThinkingState(state) {
  isThinking = state;
  updateVisualizerState();

  const statusText = document.getElementById('status-text');
  if (statusText && !isErrorState) {
    statusText.innerText = state ? "THINKING..." : "OLLAMA LIVE";
  }
}

async function triggerBriefing() {
  clearErrorState();
  setThinkingState(true);
  try {
    const res = await fetch('/api/brief');
    const data = await res.json();
    setThinkingState(false);
    if (data.summary) {
      appendMessage('assistant', data.summary);
      playSpeech(data.summary);
    }
  } catch (err) {
    setThinkingState(false);
    showError("Briefing Failed", "Could not fetch morning brief. Check server logs.");
  }
}


// ==========================================
// 4. AUDIO & SPEECH SYNTHESIS
// ==========================================

async function playSpeech(text) {
  try {
    isSpeaking = true;
    updateVisualizerState();

    const res = await fetch('/api/speak', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text })
    });

    if (res.ok) {
      const blob = await res.blob();
      const audioUrl = URL.createObjectURL(blob);
      const audio = new Audio(audioUrl);
      
      audio.onended = () => { 
        isSpeaking = false; 
        updateVisualizerState();
      };
      audio.onerror = () => { 
        isSpeaking = false; 
        updateVisualizerState();
      };
      
      await audio.play();
    } else {
      isSpeaking = false;
      updateVisualizerState();
    }
  } catch (e) {
    isSpeaking = false;
    updateVisualizerState();
  }
}


// ==========================================
// 5. VOICE INPUT (WEB SPEECH API)
// ==========================================

function toggleVoiceInput() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SpeechRecognition) {
    showError("Mic Access Required HTTPS", "Web Speech API requires HTTPS or localhost. Ensure Tailscale Serve is active.");
    return;
  }

  if (recognition) {
    recognition.stop();
    return;
  }

  recognition = new SpeechRecognition();
  recognition.continuous = false;
  recognition.interimResults = false;
  recognition.lang = 'en-US';

  recognition.onstart = () => {
    micBtn.classList.add('listening');
  };

  recognition.onresult = (event) => {
    const transcript = event.results[0][0].transcript;
    userInput.value = transcript;
    sendQuery(transcript);
  };

  recognition.onerror = (event) => {
    micBtn.classList.remove('listening');
    recognition = null;
    showError(`Voice Error: ${event.error}`, `Speech recognition error: ${event.error}`);
  };

  recognition.onend = () => {
    micBtn.classList.remove('listening');
    recognition = null;
  };

  recognition.start();
}