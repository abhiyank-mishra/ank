/**
 * ANK — LiveKit Web Client
 * Connects to LiveKit Cloud, streams audio, shows transcriptions.
 * Owner: Abhiyank
 */

// ═══════════════════════════════════════
//  STATE
// ═══════════════════════════════════════
let room = null;
let isConnected = false;
let audioContext = null;
let analyser = null;
let micStream = null;
let animFrameId = null;
let currentRoomName = null;
let settingsOpen = false;

// DOM refs
const orbEl = document.getElementById("orb");
const orbStatus = document.getElementById("orb-status");
const btnConnect = document.getElementById("btn-connect");
const connStatus = document.getElementById("connection-status");
const agentStatus = document.getElementById("agent-status");
const transcriptFeed = document.getElementById("transcript-feed");
const audioBars = document.getElementById("audio-bars");
const roomInfo = document.getElementById("room-info");
const clockEl = document.getElementById("clock");
const btnAgentStart = document.getElementById("btn-agent-start");
const btnAgentStop = document.getElementById("btn-agent-stop");
const settingsPanel = document.getElementById("settings-panel");
const settingsOverlay = document.getElementById("settings-overlay");
const settingsBtn = document.getElementById("btn-settings");

// ═══════════════════════════════════════
//  CLOCK
// ═══════════════════════════════════════
function updateClock() {
    const now = new Date();
    clockEl.textContent = now.toLocaleTimeString("en-US", { hour12: false });
}
setInterval(updateClock, 1000);
updateClock();

// ═══════════════════════════════════════
//  PARTICLES BACKGROUND
// ═══════════════════════════════════════
(function initParticles() {
    const canvas = document.getElementById("particles-canvas");
    const ctx = canvas.getContext("2d");
    let particles = [];
    const PARTICLE_COUNT = 60;

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener("resize", resize);
    resize();

    class Particle {
        constructor() { this.reset(); }
        reset() {
            this.x = Math.random() * canvas.width;
            this.y = Math.random() * canvas.height;
            this.vx = (Math.random() - 0.5) * 0.3;
            this.vy = (Math.random() - 0.5) * 0.3;
            this.size = Math.random() * 1.5 + 0.5;
            this.alpha = Math.random() * 0.3 + 0.05;
        }
        update() {
            this.x += this.vx;
            this.y += this.vy;
            if (this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) {
                this.reset();
            }
        }
        draw() {
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 229, 255, ${this.alpha})`;
            ctx.fill();
        }
    }

    for (let i = 0; i < PARTICLE_COUNT; i++) {
        particles.push(new Particle());
    }

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        for (let i = 0; i < particles.length; i++) {
            particles[i].update();
            particles[i].draw();
            for (let j = i + 1; j < particles.length; j++) {
                const dx = particles[i].x - particles[j].x;
                const dy = particles[i].y - particles[j].y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 120) {
                    ctx.beginPath();
                    ctx.moveTo(particles[i].x, particles[i].y);
                    ctx.lineTo(particles[j].x, particles[j].y);
                    ctx.strokeStyle = `rgba(0, 229, 255, ${0.04 * (1 - dist / 120)})`;
                    ctx.lineWidth = 0.5;
                    ctx.stroke();
                }
            }
        }
        requestAnimationFrame(animate);
    }
    animate();
})();

// ═══════════════════════════════════════
//  TOAST NOTIFICATION
// ═══════════════════════════════════════
function showToast(message, duration = 2500) {
    let toast = document.querySelector(".toast");
    if (!toast) {
        toast = document.createElement("div");
        toast.className = "toast";
        document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add("show");
    setTimeout(() => toast.classList.remove("show"), duration);
}

// ═══════════════════════════════════════
//  TRANSCRIPT
// ═══════════════════════════════════════
function addTranscript(text, type = "system") {
    const empty = transcriptFeed.querySelector(".transcript-empty");
    if (empty) empty.remove();

    const msg = document.createElement("div");
    msg.className = `transcript-msg ${type}`;

    const senderNames = { user: "YOU", agent: "ANK", system: "SYSTEM" };
    msg.innerHTML = `
        <div class="msg-sender">${senderNames[type] || "SYSTEM"}</div>
        <div>${text}</div>
    `;

    transcriptFeed.appendChild(msg);
    transcriptFeed.scrollTop = transcriptFeed.scrollHeight;
}

function clearTranscript() {
    transcriptFeed.innerHTML = '<div class="transcript-empty">Awaiting voice input...</div>';
}

// ═══════════════════════════════════════
//  AUDIO VISUALIZATION
// ═══════════════════════════════════════
function startAudioVisualization(stream) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    analyser = audioContext.createAnalyser();
    analyser.fftSize = 64;

    const source = audioContext.createMediaStreamSource(stream);
    source.connect(analyser);

    const bars = audioBars.querySelectorAll(".bar");
    audioBars.classList.add("visible");
    const dataArray = new Uint8Array(analyser.frequencyBinCount);

    function visualize() {
        analyser.getByteFrequencyData(dataArray);
        bars.forEach((bar, i) => {
            const value = dataArray[i] || 0;
            const height = Math.max(3, (value / 255) * 28);
            bar.style.height = height + "px";
        });
        animFrameId = requestAnimationFrame(visualize);
    }
    visualize();
}

function stopAudioVisualization() {
    if (animFrameId) cancelAnimationFrame(animFrameId);
    if (audioContext) audioContext.close();
    audioContext = null;
    analyser = null;
    audioBars.classList.remove("visible");
    audioBars.querySelectorAll(".bar").forEach(b => (b.style.height = "3px"));
}

// ═══════════════════════════════════════
//  SETTINGS PANEL
// ═══════════════════════════════════════
function toggleSettings() {
    settingsOpen = !settingsOpen;
    settingsPanel.classList.toggle("open", settingsOpen);
    settingsOverlay.classList.toggle("open", settingsOpen);
    settingsBtn.classList.toggle("active", settingsOpen);

    if (settingsOpen) {
        loadSettings();
    }
}

async function loadSettings() {
    try {
        const resp = await fetch("/api/settings");
        const config = await resp.json();

        // Voice
        const voiceSelect = document.getElementById("voice-select");
        voiceSelect.value = config.voice || "Charon";

        // MCP Servers
        renderMcpServers(config.mcp_servers || []);

        // Health
        updateHealth(config);
    } catch (e) {
        console.error("Failed to load settings:", e);
    }
}

async function saveSettings() {
    const voiceSelect = document.getElementById("voice-select");
    const saveBtn = document.querySelector(".btn-save-settings");

    try {
        const resp = await fetch("/api/settings", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                voice: voiceSelect.value,
            }),
        });
        const data = await resp.json();

        if (data.status === "saved") {
            saveBtn.classList.add("saved");
            saveBtn.textContent = "✓ Saved!";
            showToast(`Settings saved. Voice: ${voiceSelect.value}`);
            setTimeout(() => {
                saveBtn.classList.remove("saved");
                saveBtn.textContent = "💾 Save Settings";
            }, 2000);
        }
    } catch (e) {
        showToast("Failed to save settings");
    }
}

function renderMcpServers(servers) {
    const list = document.getElementById("mcp-list");
    const emptyEl = document.getElementById("mcp-empty");

    // Clear existing items
    list.querySelectorAll(".mcp-item").forEach(el => el.remove());

    if (servers.length === 0) {
        if (emptyEl) emptyEl.style.display = "block";
        return;
    }

    if (emptyEl) emptyEl.style.display = "none";

    servers.forEach((server, idx) => {
        const item = document.createElement("div");
        item.className = "mcp-item";
        item.innerHTML = `
            <div class="mcp-item-info">
                <span class="mcp-item-name">${server.name}</span>
                <span class="mcp-item-url">${server.url}</span>
            </div>
            <span class="mcp-item-badge">${server.type || "SSE"}</span>
            <button class="mcp-item-remove" onclick="removeMcpServer(${idx})" title="Remove">✕</button>
        `;
        list.appendChild(item);
    });
}

async function addMcpServer() {
    const nameEl = document.getElementById("mcp-name");
    const urlEl = document.getElementById("mcp-url");
    const typeEl = document.getElementById("mcp-type");

    const name = nameEl.value.trim();
    const url = urlEl.value.trim();
    const type = typeEl.value;

    if (!name || !url) {
        showToast("Please fill in server name and URL");
        return;
    }

    try {
        const resp = await fetch("/api/mcp/add", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ name, url, type }),
        });
        const data = await resp.json();

        if (data.status === "added") {
            renderMcpServers(data.mcp_servers);
            nameEl.value = "";
            urlEl.value = "";
            showToast(`Added MCP server: ${name}`);
        }
    } catch (e) {
        showToast("Failed to add MCP server");
    }
}

async function removeMcpServer(index) {
    try {
        const resp = await fetch("/api/mcp/remove", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ index }),
        });
        const data = await resp.json();

        if (data.status === "removed") {
            renderMcpServers(data.mcp_servers);
            showToast(`Removed: ${data.removed.name}`);
        }
    } catch (e) {
        showToast("Failed to remove server");
    }
}

function updateHealth() {
    const serverDot = document.getElementById("health-server");
    const agentDot = document.getElementById("health-agent");
    const livekitDot = document.getElementById("health-livekit");
    const mcpDot = document.getElementById("health-mcp");

    // Server is always online if we got here
    serverDot.className = "health-dot online";

    // Check agent & livekit status
    fetch("/api/status")
        .then(r => r.json())
        .then(data => {
            agentDot.className = data.agent === "running" ? "health-dot online" : "health-dot offline";
            livekitDot.className = data.livekit_url ? "health-dot online" : "health-dot offline";
            mcpDot.className = data.mcp_servers > 0 ? "health-dot online" : "health-dot warning";
        })
        .catch(() => {
            agentDot.className = "health-dot offline";
            livekitDot.className = "health-dot offline";
            mcpDot.className = "health-dot offline";
        });
}

// ═══════════════════════════════════════
//  LIVEKIT CONNECTION
// ═══════════════════════════════════════
async function toggleConnection() {
    if (isConnected) {
        await disconnect();
    } else {
        await connect();
    }
}

async function connect() {
    try {
        btnConnect.classList.add("connecting");
        btnConnect.querySelector(".btn-label").textContent = "CONNECTING...";
        orbStatus.textContent = "Establishing Link...";
        addTranscript("Initializing LiveKit connection...", "system");

        currentRoomName = `ank-room-${Date.now()}`;
        const resp = await fetch("/api/token", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ room: currentRoomName, identity: "Abhiyank" }),
        });

        if (!resp.ok) throw new Error("Failed to get token");
        const { token, url, room: roomName } = await resp.json();
        currentRoomName = roomName;

        room = new LivekitClient.Room({
            adaptiveStream: true,
            dynacast: true,
            audioCaptureDefaults: {
                noiseSuppression: true,
                echoCancellation: true,
                autoGainControl: true,
            },
        });

        room.on(LivekitClient.RoomEvent.Connected, () => {
            addTranscript(`Connected to room: ${roomName}`, "system");
        });

        room.on(LivekitClient.RoomEvent.Disconnected, () => {
            handleDisconnect();
        });

        room.on(LivekitClient.RoomEvent.TrackSubscribed, (track, publication, participant) => {
            if (track.kind === "audio") {
                const audioEl = track.attach();
                document.body.appendChild(audioEl);
                orbEl.classList.add("speaking");
                addTranscript("Ank voice channel active.", "system");
            }
        });

        room.on(LivekitClient.RoomEvent.TrackUnsubscribed, (track) => {
            track.detach().forEach((el) => el.remove());
            orbEl.classList.remove("speaking");
        });

        room.on(LivekitClient.RoomEvent.DataReceived, (payload, participant) => {
            try {
                const text = new TextDecoder().decode(payload);
                const msg = JSON.parse(text);
                if (msg.type === "transcription") {
                    const sender = msg.participant === "Ank" ? "agent" : "user";
                    addTranscript(msg.text, sender);
                }
            } catch (e) { /* ignore */ }
        });

        room.on(LivekitClient.RoomEvent.ParticipantConnected, (participant) => {
            addTranscript(`${participant.identity} joined.`, "system");
        });

        room.on(LivekitClient.RoomEvent.ParticipantDisconnected, (participant) => {
            addTranscript(`${participant.identity} left.`, "system");
        });

        room.on(LivekitClient.RoomEvent.ActiveSpeakersChanged, (speakers) => {
            const agentSpeaking = speakers.some(s => s.identity !== "Abhiyank");
            orbEl.classList.toggle("speaking", agentSpeaking);
        });

        await room.connect(url, token);
        await room.localParticipant.setMicrophoneEnabled(true);

        // Audio visualization
        const micTracks = room.localParticipant.audioTrackPublications;
        micTracks.forEach((pub) => {
            if (pub.track && pub.track.mediaStream) {
                startAudioVisualization(pub.track.mediaStream);
            }
        });

        if (!audioContext) {
            try {
                micStream = await navigator.mediaDevices.getUserMedia({ audio: true });
                startAudioVisualization(micStream);
            } catch (e) { /* no mic visualization */ }
        }

        // Update UI
        isConnected = true;
        orbEl.classList.add("active");
        orbStatus.textContent = "Systems Online";
        orbStatus.classList.add("active");
        btnConnect.classList.remove("connecting");
        btnConnect.classList.add("connected");
        btnConnect.querySelector(".btn-icon").textContent = "⏻";
        btnConnect.querySelector(".btn-label").textContent = "DISCONNECT";
        connStatus.classList.add("connected");
        connStatus.querySelector(".status-label").textContent = "CONNECTED";
        roomInfo.textContent = `Room: ${roomName}`;

        addTranscript("Ank is online. Awaiting commands, Sir.", "agent");
        showToast("Connection established");

    } catch (err) {
        console.error("Connection error:", err);
        addTranscript(`Connection failed: ${err.message}`, "system");
        btnConnect.classList.remove("connecting");
        btnConnect.querySelector(".btn-label").textContent = "INITIALIZE";
        connStatus.classList.add("error");
        connStatus.querySelector(".status-label").textContent = "ERROR";
        orbStatus.textContent = "Connection Failed";
        showToast("Connection failed");
        setTimeout(() => {
            connStatus.classList.remove("error");
            connStatus.querySelector(".status-label").textContent = "OFFLINE";
            orbStatus.textContent = "Systems Standing By";
        }, 3000);
    }
}

async function disconnect() {
    if (room) {
        await room.disconnect();
    }
    handleDisconnect();
}

function handleDisconnect() {
    isConnected = false;
    room = null;

    stopAudioVisualization();
    if (micStream) {
        micStream.getTracks().forEach((t) => t.stop());
        micStream = null;
    }

    document.querySelectorAll("audio").forEach((el) => el.remove());

    orbEl.classList.remove("active", "speaking");
    orbStatus.textContent = "Systems Standing By";
    orbStatus.classList.remove("active");
    btnConnect.classList.remove("connected", "connecting");
    btnConnect.querySelector(".btn-icon").textContent = "⚡";
    btnConnect.querySelector(".btn-label").textContent = "INITIALIZE";
    connStatus.classList.remove("connected");
    connStatus.querySelector(".status-label").textContent = "OFFLINE";
    roomInfo.textContent = "Room: —";

    addTranscript("Disconnected.", "system");
}

// ═══════════════════════════════════════
//  AGENT CONTROL
// ═══════════════════════════════════════
async function startAgent() {
    try {
        btnAgentStart.disabled = true;
        addTranscript("Starting Ank Agent...", "system");

        const resp = await fetch("/api/agent/start", { method: "POST" });
        const data = await resp.json();

        if (data.status === "started") {
            addTranscript(`Agent started (PID: ${data.pid}).`, "system");
            agentStatus.classList.add("connected");
            agentStatus.querySelector(".status-label").textContent = "AGENT: LIVE";
            btnAgentStop.disabled = false;
            showToast("Agent started");
        } else if (data.status === "already_running") {
            addTranscript("Agent is already running.", "system");
            agentStatus.classList.add("connected");
            agentStatus.querySelector(".status-label").textContent = "AGENT: LIVE";
            btnAgentStart.disabled = false;
            btnAgentStop.disabled = false;
        }
    } catch (err) {
        addTranscript(`Failed to start agent: ${err.message}`, "system");
        btnAgentStart.disabled = false;
    }
}

async function stopAgent() {
    try {
        const resp = await fetch("/api/agent/stop", { method: "POST" });
        const data = await resp.json();

        addTranscript(`Agent ${data.status}.`, "system");
        agentStatus.classList.remove("connected");
        agentStatus.querySelector(".status-label").textContent = "AGENT: —";
        btnAgentStart.disabled = false;
        btnAgentStop.disabled = true;
        showToast("Agent stopped");
    } catch (err) {
        addTranscript(`Failed to stop agent: ${err.message}`, "system");
    }
}

// ═══════════════════════════════════════
//  STATUS POLLING
// ═══════════════════════════════════════
async function pollStatus() {
    try {
        const resp = await fetch("/api/status");
        const data = await resp.json();

        if (data.agent === "running") {
            agentStatus.classList.add("connected");
            agentStatus.querySelector(".status-label").textContent = "AGENT: LIVE";
            btnAgentStop.disabled = false;
        } else {
            agentStatus.classList.remove("connected");
            agentStatus.querySelector(".status-label").textContent = "AGENT: —";
            btnAgentStart.disabled = false;
        }
    } catch (e) { /* server not ready */ }
}

setInterval(pollStatus, 5000);
pollStatus();

// ═══════════════════════════════════════
//  PWA SERVICE WORKER
// ═══════════════════════════════════════
if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("/sw.js").catch(() => {});
}
