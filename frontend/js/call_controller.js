// Real-Time Call Controller & WebSocket Coordinator

class CallController {
  constructor(roomId) {
    this.roomId = roomId;
    this.user = Auth.getUser();
    this.token = Auth.getToken();

    this.socket = null;
    this.streamer = null;
    this.player = null;

    this.isMuted = false;
    this.isDeafened = false;
    this.counterpart = null;

    // DOM Elements
    this.localAvatar = document.getElementById("localAvatar");
    this.remoteAvatar = document.getElementById("remoteAvatar");
    this.remoteName = document.getElementById("remoteName");
    this.callStatus = document.getElementById("callStatus");
    this.latencyBadge = document.getElementById("latencyBadge");
    this.subtitlesContainer = document.getElementById("subtitlesContainer");
    this.muteBtn = document.getElementById("muteBtn");
    this.deafenBtn = document.getElementById("deafenBtn");
    this.endCallBtn = document.getElementById("endCallBtn");
    this.mySpeakingSelect = document.getElementById("mySpeakingSelect");
    this.myListeningSelect = document.getElementById("myListeningSelect");
    this.voiceGenderSelect = document.getElementById("voiceGenderSelect");
  }

  async init() {
    this.setupAudioComponents();
    this.setupEventListeners();
    await this.loadLanguages();
    this.connectWebSocket();

    // Start mic streaming
    try {
      await this.streamer.start();
      this.updateStatus("Wicitaanku wuu xirmay. Hadal markasta!", "connected");
    } catch (err) {
      console.error("Mic start failed:", err);
      this.updateStatus("Microphone-ka lama heli karo. Fadlan fasax sii!", "error");
    }
  }

  setupAudioComponents() {
    // 1. Audio Player for incoming AI speech
    this.player = new AudioPlayer({
      onPlayStart: () => {
        if (this.remoteAvatar) this.remoteAvatar.classList.add("speaking");
      },
      onPlayEnd: () => {
        if (this.remoteAvatar) this.remoteAvatar.classList.remove("speaking");
      }
    });

    // 2. Audio Streamer for local microphone
    this.streamer = new AudioStreamer({
      onAudioChunk: (blob) => {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(blob);
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
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const tokenParam = this.token ? `?token=${encodeURIComponent(this.token)}` : "";
    const wsUrl = `${protocol}//${window.location.host}/ws/call/${this.roomId}${tokenParam}`;

    this.socket = new WebSocket(wsUrl);
    this.socket.binaryType = "arraybuffer";

    this.socket.onopen = () => {
      console.log("WebSocket Call Connected.");
      this.updateStatus("Ku xirmay qolka wicitaanka...", "connected");
    };

    this.socket.onmessage = (event) => {
      // Binary Data = Incoming AI Speech audio bytes (MP3)
      if (event.data instanceof ArrayBuffer) {
        console.log("Received AI audio stream bytes:", event.data.byteLength);
        this.player.enqueue(event.data);
        return;
      }

      // JSON Control Message
      try {
        const data = JSON.parse(event.data);
        this.handleSocketEvent(data);
      } catch (err) {
        console.error("Error parsing JSON socket message:", err);
      }
    };

    this.socket.onclose = () => {
      console.log("WebSocket Disconnected.");
      this.updateStatus("Wicitaanku wuu go'ay.", "disconnected");
    };

    this.socket.onerror = (err) => {
      console.error("WebSocket Error:", err);
      this.updateStatus("Khalad ayaa ku dhacay khadka.", "error");
    };
  }

  handleSocketEvent(data) {
    switch (data.type) {
      case "peer_joined":
        this.handlePeerJoined(data);
        break;

      case "peer_left":
        this.handlePeerLeft(data);
        break;

      case "peer_speaking":
        if (this.remoteAvatar) {
          if (data.is_speaking) {
            this.remoteAvatar.classList.add("speaking");
          } else {
            this.remoteAvatar.classList.remove("speaking");
          }
        }
        break;

      case "ai_processing":
        if (this.remoteAvatar) {
          this.remoteAvatar.classList.add("translating");
        }
        this.updateStatus("AI ayaa hadalka turjumaya...", "translating");
        break;

      case "ai_idle":
        if (this.remoteAvatar) {
          this.remoteAvatar.classList.remove("translating");
        }
        this.updateStatus("Wicitaanka tooska ah waa firfircoon yahay", "connected");
        break;

      case "translation_complete":
        this.displaySubtitle(data);
        break;

      case "languages_updated":
        if (data.peer && (!this.user || data.peer.user_id !== this.user.id)) {
          this.counterpart = data.peer;
          this.updateCounterpartUI();
        }
        break;

      case "ai_error":
        console.warn("AI Pipeline Notice:", data.message);
        break;
    }
  }

  handlePeerJoined(data) {
    const list = data.participants || [];
    const other = list.find(p => !this.user || p.user_id !== this.user.id);
    if (other) {
      this.counterpart = other;
      this.updateCounterpartUI();
      this.updateStatus(`${other.full_name || other.username} ayaa soo galay wicitaanka!`, "connected");
    } else {
      this.updateStatus("Waxaad ku jirtaa qolka. Qofka labaad ayaa la sugayaa...", "waiting");
    }
  }

  handlePeerLeft(data) {
    this.counterpart = null;
    if (this.remoteName) this.remoteName.textContent = "Qof kale ma joogo";
    this.updateStatus(`${data.username || 'Qofkii kale'} wuu ka baxay wicitaanka.`, "waiting");
  }

  updateCounterpartUI() {
    if (!this.counterpart) return;
    if (this.remoteName) {
      this.remoteName.textContent = this.counterpart.full_name || this.counterpart.username;
    }
    const remoteLangBadge = document.getElementById("remoteLangBadge");
    if (remoteLangBadge) {
      remoteLangBadge.textContent = `Maqlaya: ${this.counterpart.listening_language.toUpperCase()} | Ku hadlaya: ${this.counterpart.speaking_language.toUpperCase()}`;
    }
  }

  displaySubtitle(data) {
    if (!this.subtitlesContainer) return;

    if (this.latencyBadge && data.total_latency_ms) {
      this.latencyBadge.textContent = `⚡ Latency: ${(data.total_latency_ms / 1000).toFixed(2)}s`;
      this.latencyBadge.classList.remove("hidden");
    }

    const card = document.createElement("div");
    card.className = "p-3 rounded-xl bg-slate-800/80 border border-slate-700/60 shadow-md text-sm space-y-1 animate-fade-in";
    
    card.innerHTML = `
      <div class="flex justify-between items-center text-xs text-indigo-400 font-medium">
        <span>🗣️ ${data.speaker_name} (${data.source_lang.toUpperCase()} ➔ ${data.target_lang.toUpperCase()})</span>
        <span class="text-emerald-400">${(data.total_latency_ms / 1000).toFixed(2)}s</span>
      </div>
      <div class="text-slate-300 text-xs italic">"${data.original_text}"</div>
      <div class="text-white font-semibold flex items-center gap-1.5">
        <span class="text-indigo-400">🤖 AI Voice:</span> "${data.translated_text}"
      </div>
    `;

    this.subtitlesContainer.appendChild(card);
    this.subtitlesContainer.scrollTop = this.subtitlesContainer.scrollHeight;

    // Keep max 25 items in view
    while (this.subtitlesContainer.children.length > 25) {
      this.subtitlesContainer.removeChild(this.subtitlesContainer.firstChild);
    }
  }

  updateStatus(msg, state = "normal") {
    if (!this.callStatus) return;
    this.callStatus.textContent = msg;
    this.callStatus.className = "text-xs font-medium px-3 py-1 rounded-full text-center inline-block ";
    
    if (state === "connected") {
      this.callStatus.className += "bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
    } else if (state === "translating") {
      this.callStatus.className += "bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 animate-pulse";
    } else if (state === "waiting") {
      this.callStatus.className += "bg-amber-500/20 text-amber-300 border border-amber-500/30";
    } else if (state === "error" || state === "disconnected") {
      this.callStatus.className += "bg-red-500/20 text-red-300 border border-red-500/30";
    } else {
      this.callStatus.className += "bg-slate-700 text-slate-300";
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
    // Mute Microphone
    if (this.muteBtn) {
      this.muteBtn.onclick = () => {
        this.isMuted = !this.isMuted;
        this.streamer.setMuted(this.isMuted);
        this.muteBtn.classList.toggle("bg-red-600", this.isMuted);
        this.muteBtn.classList.toggle("bg-slate-700", !this.isMuted);
        this.muteBtn.innerHTML = this.isMuted 
          ? `<span>🔇</span><span>Unmute</span>` 
          : `<span>🎤</span><span>Mute</span>`;
      };
    }

    // Deafen (Mute Incoming Speaker)
    if (this.deafenBtn) {
      this.deafenBtn.onclick = () => {
        this.isDeafened = !this.isDeafened;
        this.player.setMuted(this.isDeafened);
        this.deafenBtn.classList.toggle("bg-red-600", this.isDeafened);
        this.deafenBtn.classList.toggle("bg-slate-700", !this.isDeafened);
        this.deafenBtn.innerHTML = this.isDeafened 
          ? `<span>🔈</span><span>Un-deafen</span>` 
          : `<span>🔊</span><span>Deafen</span>`;
      };
    }

    // End Call
    if (this.endCallBtn) {
      this.endCallBtn.onclick = () => {
        this.hangUp();
      };
    }

    // In-Call Language Switchers
    const notifyLangChange = () => {
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({
          type: "update_languages",
          speaking_language: this.mySpeakingSelect ? this.mySpeakingSelect.value : "so",
          listening_language: this.myListeningSelect ? this.myListeningSelect.value : "en",
          voice_gender: this.voiceGenderSelect ? this.voiceGenderSelect.value : "male"
        }));
      }
    };

    if (this.mySpeakingSelect) this.mySpeakingSelect.onchange = notifyLangChange;
    if (this.myListeningSelect) this.myListeningSelect.onchange = notifyLangChange;
    if (this.voiceGenderSelect) this.voiceGenderSelect.onchange = notifyLangChange;
  }

  hangUp() {
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
