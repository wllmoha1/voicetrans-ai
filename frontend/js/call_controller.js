// Real-Time Call Controller & WebSocket Coordinator
// Handles Dual-Profile Call UI, Heartbeat Ping-Pong, and Ultra-Fast AI Speech Streaming

class CallController {
  constructor(roomId) {
    this.roomId = roomId;
    this.user = Auth.getUser();
    this.token = Auth.getToken();

    this.socket = null;
    this.streamer = null;
    this.player = null;

    this.mySessionId = null;
    this.myParticipant = null;
    this.counterpart = null;

    this.isMuted = false;
    this.isDeafened = false;
    this.pingInterval = null;
    this.reconnectTimer = null;
    this.isCallEnded = false;

    // DOM Elements
    this.localName = document.getElementById("localName");
    this.localAvatar = document.getElementById("localAvatar");
    this.localLangBadge = document.getElementById("localLangBadge");
    this.localStatusBadge = document.getElementById("localStatusBadge");

    this.remoteName = document.getElementById("remoteName");
    this.remoteAvatar = document.getElementById("remoteAvatar");
    this.remoteLangBadge = document.getElementById("remoteLangBadge");
    this.remoteStatusBadge = document.getElementById("remoteStatusBadge");

    this.callStatus = document.getElementById("callStatus");
    this.latencyBadge = document.getElementById("latencyBadge");
    this.subtitlesContainer = document.getElementById("subtitlesContainer");
    this.bridgeStatus = document.getElementById("bridgeStatus");

    this.muteBtn = document.getElementById("muteBtn");
    this.deafenBtn = document.getElementById("deafenBtn");
    this.endCallBtn = document.getElementById("endCallBtn");

    this.mySpeakingSelect = document.getElementById("mySpeakingSelect");
    this.myListeningSelect = document.getElementById("myListeningSelect");
    this.voiceGenderSelect = document.getElementById("voiceGenderSelect");
    this.audioUnlockOverlay = document.getElementById("audioUnlockOverlay");
  }

  async init() {
    this.setupAudioComponents();
    this.setupEventListeners();
    await this.loadLanguages();
    this.connectWebSocket();
    this.initMicrophone();
  }

  async initMicrophone() {
    try {
      await this.streamer.start();
      console.log("Microphone is capturing and streaming.");
      if (this.localStatusBadge) {
        this.localStatusBadge.textContent = "🎙️ Mic Diyaar ah";
        this.localStatusBadge.className = "text-[11px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
      }
    } catch (err) {
      console.error("Mic access error:", err);
      if (this.localStatusBadge) {
        this.localStatusBadge.textContent = "⚠️ Mic Xiran";
        this.localStatusBadge.className = "text-[11px] px-2 py-0.5 rounded-full bg-red-500/20 text-red-300 border border-red-500/30";
      }
      this.updateStatus("Fadlan ogolow Microphone-ka browser-kaaga!", "error");
    }
  }

  setupAudioComponents() {
    // 1. Audio Player for incoming AI speech
    this.player = new AudioPlayer({
      onPlayStart: () => {
        if (this.remoteAvatar) this.remoteAvatar.classList.add("speaking");
        if (this.bridgeStatus) this.bridgeStatus.textContent = "🔊 AI ayaa u hadlaysa...";
      },
      onPlayEnd: () => {
        if (this.remoteAvatar) this.remoteAvatar.classList.remove("speaking");
        if (this.bridgeStatus) this.bridgeStatus.textContent = "⚡ AI Diyaar bay u tahay";
      }
    });

    // 2. Audio Streamer for local microphone
    this.streamer = new AudioStreamer({
      silenceThreshold: 0.02,
      silenceDurationMs: 450, // Faster speech-to-text response
      onAudioChunk: (blob) => {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(blob);
          if (this.bridgeStatus) this.bridgeStatus.textContent = "📤 Codkaaga waa la dirayaa...";
        }
      },
      onSpeakingStateChange: (isSpeaking) => {
        if (this.localAvatar) {
          if (isSpeaking) {
            this.localAvatar.classList.add("speaking");
          } else {
            this.localAvatar.classList.remove("speaking");
          }
        }
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(JSON.stringify({
            type: "speaking_state",
            is_speaking: isSpeaking
          }));
        }
      }
    });
  }

  connectWebSocket() {
    if (this.isCallEnded) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const tokenParam = this.token ? `?token=${encodeURIComponent(this.token)}` : "";
    const wsUrl = `${protocol}//${window.location.host}/ws/call/${this.roomId}${tokenParam}`;

    console.log("Connecting WebSocket:", wsUrl);
    this.updateStatus("Isku xiraya wicitaanka...", "connecting");

    this.socket = new WebSocket(wsUrl);
    this.socket.binaryType = "arraybuffer";

    this.socket.onopen = () => {
      console.log("WebSocket Call Connected successfully.");
      this.updateStatus("Khadka wuu furan yahay", "connected");

      // Start keep-alive ping every 15 seconds to prevent Render 50s idle disconnect
      if (this.pingInterval) clearInterval(this.pingInterval);
      this.pingInterval = setInterval(() => {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(JSON.stringify({ type: "ping" }));
        }
      }, 15000);
    };

    this.socket.onmessage = (event) => {
      // 1. Binary Audio Chunks (MP3 synthesized speech from AI)
      if (event.data instanceof ArrayBuffer) {
        console.log("Received AI audio stream chunk:", event.data.byteLength);
        this.player.enqueue(event.data);
        return;
      }

      // 2. JSON Event Messages
      try {
        const data = JSON.parse(event.data);
        this.handleSocketEvent(data);
      } catch (err) {
        console.error("Error parsing JSON socket message:", err);
      }
    };

    this.socket.onclose = (event) => {
      console.warn("WebSocket closed. Code:", event.code, "Reason:", event.reason);
      if (this.pingInterval) clearInterval(this.pingInterval);

      if (!this.isCallEnded) {
        this.updateStatus("Khadku wuu go'ay. Dib ayaa loo xirayaa...", "waiting");
        // Auto-reconnect after 2.5 seconds
        if (!this.reconnectTimer) {
          this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connectWebSocket();
          }, 2500);
        }
      } else {
        this.updateStatus("Wicitaankii waa la jaray.", "disconnected");
      }
    };

    this.socket.onerror = (err) => {
      console.error("WebSocket Error:", err);
      this.updateStatus("Khalad ayaa ku dhacay khadka.", "error");
    };
  }

  handleSocketEvent(data) {
    switch (data.type) {
      case "init":
        this.mySessionId = data.my_session_id;
        this.myParticipant = data.my_participant;
        this.updateLocalUI(data.my_participant);
        this.refreshParticipants(data.participants || []);
        break;

      case "peer_joined":
      case "languages_updated":
        this.refreshParticipants(data.participants || []);
        break;

      case "peer_left":
        this.refreshParticipants(data.participants || []);
        this.updateStatus(`${data.username || 'Qofkii kale'} wuu ka baxay wicitaanka.`, "waiting");
        break;

      case "peer_speaking":
        if (this.remoteAvatar && data.session_id !== this.mySessionId) {
          if (data.is_speaking) {
            this.remoteAvatar.classList.add("speaking");
            if (this.bridgeStatus) this.bridgeStatus.textContent = "🎙️ Qofka kale ayaa hadlaya...";
          } else {
            this.remoteAvatar.classList.remove("speaking");
          }
        }
        break;

      case "ai_processing":
        if (this.remoteAvatar) {
          this.remoteAvatar.classList.add("translating");
        }
        if (this.bridgeStatus) {
          this.bridgeStatus.textContent = "🤖 AI ayaa hadalka u turjumaysa cod dabiici ah...";
        }
        this.updateStatus("AI ayaa hadalka turjumaysa...", "translating");
        break;

      case "ai_idle":
        if (this.remoteAvatar) {
          this.remoteAvatar.classList.remove("translating");
        }
        this.updateStatus("Khadka wuu furan yahay", "connected");
        break;

      case "translation_complete":
        this.displaySubtitle(data);
        break;
    }
  }

  refreshParticipants(participants) {
    if (!this.mySessionId) return;

    // Find the other participant whose session_id is different from mine
    const other = participants.find(p => p.session_id !== this.mySessionId);
    if (other) {
      this.counterpart = other;
      this.updateRemoteUI(other);
      this.updateStatus(`Khadka waxaa ku jira: ${other.full_name || other.username}`, "connected");
    } else {
      this.counterpart = null;
      this.resetRemoteUI();
      this.updateStatus("Waxaad ku jirtaa qolka. Qofka labaad ayaa la sugayaa...", "waiting");
    }
  }

  updateLocalUI(participant) {
    if (!participant) return;
    if (this.localName) {
      this.localName.textContent = `${participant.full_name || participant.username} (Adiga)`;
    }
    if (this.localLangBadge) {
      this.localLangBadge.textContent = `🗣️ Ku hadal: ${participant.speaking_language.toUpperCase()}`;
    }
  }

  updateRemoteUI(other) {
    if (!other) return;
    if (this.remoteName) {
      this.remoteName.textContent = other.full_name || other.username;
    }
    if (this.remoteLangBadge) {
      this.remoteLangBadge.textContent = `👂 Maqlaya: ${other.listening_language.toUpperCase()} | 🗣️ ${other.speaking_language.toUpperCase()}`;
    }
    if (this.remoteStatusBadge) {
      this.remoteStatusBadge.textContent = "🟢 Khadka ku jira";
      this.remoteStatusBadge.className = "text-[11px] px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
    }
    if (this.bridgeStatus) {
      this.bridgeStatus.textContent = `⚡ AI Bridge: ${this.mySpeakingSelect ? this.mySpeakingSelect.value.toUpperCase() : 'SO'} ➔ ${other.listening_language.toUpperCase()}`;
    }
  }

  resetRemoteUI() {
    if (this.remoteName) this.remoteName.textContent = "Qof labaad ayaa la sugayaa...";
    if (this.remoteLangBadge) this.remoteLangBadge.textContent = "Link-ga qof kale u dir si aad u wada hadashaan";
    if (this.remoteStatusBadge) {
      this.remoteStatusBadge.textContent = "⏳ Sugaya...";
      this.remoteStatusBadge.className = "text-[11px] px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/30";
    }
    if (this.bridgeStatus) {
      this.bridgeStatus.textContent = "Sugaya qofka labaad...";
    }
  }

  displaySubtitle(data) {
    if (!this.subtitlesContainer) return;

    if (this.latencyBadge && data.total_latency_ms) {
      this.latencyBadge.textContent = `⚡ Latency: ${(data.total_latency_ms / 1000).toFixed(2)}s`;
      this.latencyBadge.classList.remove("hidden");
    }

    const card = document.createElement("div");
    card.className = "p-3 rounded-xl bg-slate-800/90 border border-slate-700/80 shadow-md text-xs space-y-1";
    
    card.innerHTML = `
      <div class="flex justify-between items-center text-[11px] text-indigo-400 font-semibold">
        <span>🗣️ ${data.speaker_name} (${data.source_lang.toUpperCase()} ➔ ${data.target_lang.toUpperCase()})</span>
        <span class="text-emerald-400">${(data.total_latency_ms / 1000).toFixed(2)}s</span>
      </div>
      <div class="text-slate-300 italic">"${data.original_text}"</div>
      <div class="text-white font-medium flex items-center gap-1">
        <span class="text-indigo-400 font-bold">🤖 AI Voice:</span> "${data.translated_text}"
      </div>
    `;

    this.subtitlesContainer.appendChild(card);
    this.subtitlesContainer.scrollTop = this.subtitlesContainer.scrollHeight;
  }

  updateStatus(msg, state = "normal") {
    if (!this.callStatus) return;
    this.callStatus.textContent = msg;
    this.callStatus.className = "text-xs font-semibold px-3 py-1 rounded-full text-center inline-block ";
    
    if (state === "connected") {
      this.callStatus.className += "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
    } else if (state === "translating") {
      this.callStatus.className += "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 animate-pulse";
    } else if (state === "waiting") {
      this.callStatus.className += "bg-amber-500/20 text-amber-300 border border-amber-500/30";
    } else if (state === "error" || state === "disconnected") {
      this.callStatus.className += "bg-red-500/20 text-red-300 border border-red-500/30";
    } else {
      this.callStatus.className += "bg-slate-800 text-slate-300 border border-slate-700";
    }
  }

  async loadLanguages() {
    try {
      const res = await fetch("/api/languages");
      const data = await res.json();
      const langs = data.languages || [];

      const populate = (selectElem, defaultVal) => {
        if (!selectElem) return;
        selectElem.innerHTML = "";
        langs.forEach(l => {
          const opt = document.createElement("option");
          opt.value = l.code;
          opt.textContent = `${l.flag || ''} ${l.name}`;
          if (l.code === defaultVal) opt.selected = true;
          selectElem.appendChild(opt);
        });
      };

      const userNative = this.user ? this.user.native_language : "so";
      const userTarget = this.user ? this.user.target_language : "en";
      const userVoice = this.user ? this.user.preferred_voice : "male";

      populate(this.mySpeakingSelect, userNative);
      populate(this.myListeningSelect, userTarget);
      if (this.voiceGenderSelect) this.voiceGenderSelect.value = userVoice;

    } catch (e) {
      console.warn("Could not load languages list:", e);
    }
  }

  setupEventListeners() {
    // Unlock Audio Context on any user click
    const unlockAudio = () => {
      if (this.audioUnlockOverlay) {
        this.audioUnlockOverlay.classList.add("hidden");
      }
      // Play brief silent tick to unlock browser audio policy
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      if (ctx.state === "suspended") ctx.resume();
    };
    document.addEventListener("click", unlockAudio, { once: true });
    document.addEventListener("touchstart", unlockAudio, { once: true });

    if (this.audioUnlockOverlay) {
      this.audioUnlockOverlay.onclick = unlockAudio;
    }

    // Mute/Unmute Mic
    if (this.muteBtn) {
      this.muteBtn.onclick = () => {
        this.isMuted = !this.isMuted;
        this.streamer.setMuted(this.isMuted);
        this.muteBtn.classList.toggle("bg-red-600", this.isMuted);
        this.muteBtn.classList.toggle("bg-slate-800", !this.isMuted);
        this.muteBtn.innerHTML = this.isMuted 
          ? `<span class="text-xl">🔇</span><span>Unmute</span>` 
          : `<span class="text-xl">🎤</span><span>Mute</span>`;
      };
    }

    // Deafen Incoming Audio
    if (this.deafenBtn) {
      this.deafenBtn.onclick = () => {
        this.isDeafened = !this.isDeafened;
        this.player.setMuted(this.isDeafened);
        this.deafenBtn.classList.toggle("bg-red-600", this.isDeafened);
        this.deafenBtn.classList.toggle("bg-slate-800", !this.isDeafened);
        this.deafenBtn.innerHTML = this.isDeafened 
          ? `<span class="text-xl">🔈</span><span>Un-deafen</span>` 
          : `<span class="text-xl">🔊</span><span>Deafen</span>`;
      };
    }

    // End Call
    if (this.endCallBtn) {
      this.endCallBtn.onclick = () => this.hangUp();
    }

    // In-Call Language Changes
    const notifyLangChange = () => {
      const payload = {
        type: "update_languages",
        speaking_language: this.mySpeakingSelect ? this.mySpeakingSelect.value : "so",
        listening_language: this.myListeningSelect ? this.myListeningSelect.value : "en",
        voice_gender: this.voiceGenderSelect ? this.voiceGenderSelect.value : "male"
      };
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify(payload));
      }
      if (this.localLangBadge && payload.speaking_language) {
        this.localLangBadge.textContent = `🗣️ Ku hadal: ${payload.speaking_language.toUpperCase()}`;
      }
    };

    if (this.mySpeakingSelect) this.mySpeakingSelect.onchange = notifyLangChange;
    if (this.myListeningSelect) this.myListeningSelect.onchange = notifyLangChange;
    if (this.voiceGenderSelect) this.voiceGenderSelect.onchange = notifyLangChange;
  }

  hangUp() {
    this.isCallEnded = true;
    if (this.pingInterval) clearInterval(this.pingInterval);
    if (this.streamer) this.streamer.stop();
    if (this.player) this.player.stop();
    if (this.socket) {
      try {
        this.socket.send(JSON.stringify({ type: "leave_call" }));
        this.socket.close();
      } catch (e) {}
    }
    window.location.href = "/dashboard";
  }
}
