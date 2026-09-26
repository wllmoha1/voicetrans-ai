// Professional Snapchat-Style Call Controller
// Supports WebRTC P2P Direct Audio & Video + AI Real-Time Voice Translation + Keep-Alive

class CallController {
  constructor(roomId, callType = "voice") {
    this.roomId = roomId;
    this.callType = callType; // "voice" or "video"
    this.user = Auth.getUser();
    this.token = Auth.getToken();

    this.socket = null;
    this.streamer = null;
    this.player = null;

    this.mySessionId = null;
    this.myParticipant = null;
    this.counterpart = null;

    // WebRTC Direct P2P Audio & Video Call
    this.peerConnection = null;
    this.localStream = null;
    this.remoteStream = null;
    this.isCameraOn = callType === "video";
    this.isMuted = false;
    this.isCallEnded = false;
    this.pingInterval = null;
    this.reconnectTimer = null;

    // STUN Servers for WebRTC P2P direct call
    this.rtcConfig = {
      iceServers: [
        { urls: "stun:stun.l.google.com:19302" },
        { urls: "stun:stun1.l.google.com:19302" },
        { urls: "stun:stun2.l.google.com:19302" }
      ]
    };

    // DOM Elements
    this.localVideo = document.getElementById("localVideo");
    this.remoteVideo = document.getElementById("remoteVideo");
    this.remoteAudio = document.getElementById("remoteAudio");
    this.localAvatar = document.getElementById("localAvatar");
    this.remoteAvatar = document.getElementById("remoteAvatar");
    this.localName = document.getElementById("localName");
    this.remoteName = document.getElementById("remoteName");
    this.localLangBadge = document.getElementById("localLangBadge");
    this.remoteLangBadge = document.getElementById("remoteLangBadge");
    this.voiceCallStage = document.getElementById("voiceCallStage");
    this.videoCallStage = document.getElementById("videoCallStage");

    this.callStatus = document.getElementById("callStatus");
    this.latencyBadge = document.getElementById("latencyBadge");
    this.subtitlesContainer = document.getElementById("subtitlesContainer");
    this.bridgeStatus = document.getElementById("bridgeStatus");

    this.muteBtn = document.getElementById("muteBtn");
    this.cameraBtn = document.getElementById("cameraBtn");
    this.endCallBtn = document.getElementById("endCallBtn");
    this.toggleCaptionsBtn = document.getElementById("toggleCaptionsBtn");
    this.captionsDrawer = document.getElementById("captionsDrawer");

    this.mySpeakingSelect = document.getElementById("mySpeakingSelect");
    this.myListeningSelect = document.getElementById("myListeningSelect");
    this.voiceGenderSelect = document.getElementById("voiceGenderSelect");
    this.audioUnlockOverlay = document.getElementById("audioUnlockOverlay");
  }

  async init() {
    this.setupAudioPlayer();
    this.setupEventListeners();
    await this.loadLanguages();
    await this.startLocalMedia();
    this.connectWebSocket();
  }

  async startLocalMedia() {
    try {
      const constraints = {
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        },
        video: this.isCameraOn ? { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: "user" } : false
      };

      this.localStream = await navigator.mediaDevices.getUserMedia(constraints);
      console.log("Local media acquired (audio + video:", this.isCameraOn, ")");

      if (this.localVideo && this.isCameraOn) {
        this.localVideo.srcObject = this.localStream;
        this.localVideo.play().catch(e => console.warn(e));
      }

      this.setupAudioStreamer(this.localStream);
      this.updateViewMode();
    } catch (err) {
      console.warn("Could not start full media, trying audio only:", err);
      try {
        this.localStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        this.setupAudioStreamer(this.localStream);
      } catch (e2) {
        console.error("Microphone denied:", e2);
        this.updateStatus("Fadlan ogolow Microphone-ka!", "error");
      }
    }
  }

  setupAudioPlayer() {
    this.player = new AudioPlayer({
      onPlayStart: () => {
        if (this.remoteAvatar) this.remoteAvatar.classList.add("speaking");
        if (this.bridgeStatus) this.bridgeStatus.textContent = "🔊 AI ayaa hadalka u turjumaysa...";
        // Voice ducking: Lower WebRTC direct audio volume during AI translation speech
        if (this.remoteAudio) this.remoteAudio.volume = 0.2;
      },
      onPlayEnd: () => {
        if (this.remoteAvatar) this.remoteAvatar.classList.remove("speaking");
        if (this.bridgeStatus) this.bridgeStatus.textContent = "⚡ AI Diyaar bay u tahay";
        // Restore WebRTC direct audio volume
        if (this.remoteAudio) this.remoteAudio.volume = 1.0;
      }
    });
  }

  setupAudioStreamer(stream) {
    this.streamer = new AudioStreamer({
      silenceThreshold: 0.02,
      silenceDurationMs: 450,
      onAudioChunk: (blob) => {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(blob);
          if (this.bridgeStatus) this.bridgeStatus.textContent = "📤 Codkaaga waa la dirayaa...";
        }
      },
      onSpeakingStateChange: (isSpeaking) => {
        if (this.localAvatar) {
          if (isSpeaking) this.localAvatar.classList.add("speaking");
          else this.localAvatar.classList.remove("speaking");
        }
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(JSON.stringify({
            type: "speaking_state",
            is_speaking: isSpeaking
          }));
        }
      }
    });

    // Provide existing stream
    this.streamer.mediaStream = stream;
    try {
      this.streamer.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = this.streamer.audioContext.createMediaStreamSource(stream);
      this.streamer.analyser = this.streamer.audioContext.createAnalyser();
      this.streamer.analyser.fftSize = 512;
      source.connect(this.streamer.analyser);
      this.streamer.initMediaRecorder();
      this.streamer.startVADLoop();
    } catch (e) {
      console.warn("VAD init error:", e);
    }
  }

  connectWebSocket() {
    if (this.isCallEnded) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const tokenParam = this.token ? `?token=${encodeURIComponent(this.token)}` : "";
    const wsUrl = `${protocol}//${window.location.host}/ws/call/${this.roomId}${tokenParam}`;

    console.log("Connecting Call WebSocket:", wsUrl);
    this.updateStatus("Isku xiraya wicitaanka...", "connecting");

    this.socket = new WebSocket(wsUrl);
    this.socket.binaryType = "arraybuffer";

    this.socket.onopen = () => {
      console.log("Call WebSocket Connected.");
      this.updateStatus("Khadku wuu furan yahay", "connected");

      // Heartbeat ping every 10 seconds to keep connection alive on Render indefinitely
      if (this.pingInterval) clearInterval(this.pingInterval);
      this.pingInterval = setInterval(() => {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
          this.socket.send(JSON.stringify({ type: "ping" }));
        }
      }, 10000);
    };

    this.socket.onmessage = async (event) => {
      // 1. Binary Audio Chunk from AI
      if (event.data instanceof ArrayBuffer) {
        this.player.enqueue(event.data);
        return;
      }

      // 2. JSON Event / WebRTC Signaling
      try {
        const data = JSON.parse(event.data);
        await this.handleSocketEvent(data);
      } catch (err) {
        console.error("Error handling socket message:", err);
      }
    };

    this.socket.onclose = (event) => {
      console.warn("Call WebSocket closed. Code:", event.code);
      if (this.pingInterval) clearInterval(this.pingInterval);

      if (!this.isCallEnded) {
        this.updateStatus("Khadka dib ayaa loo xirayaa...", "waiting");
        if (!this.reconnectTimer) {
          this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connectWebSocket();
          }, 2000);
        }
      }
    };

    this.socket.onerror = (err) => {
      console.error("Call WebSocket Error:", err);
    };
  }

  async handleSocketEvent(data) {
    switch (data.type) {
      case "init":
        this.mySessionId = data.my_session_id;
        this.myParticipant = data.my_participant;
        this.updateLocalUI(data.my_participant);
        this.refreshParticipants(data.participants || []);
        break;

      case "peer_joined":
        this.refreshParticipants(data.participants || []);
        // As the existing peer, initiate WebRTC P2P direct call
        if (this.counterpart) {
          await this.createWebRTCOffer();
        }
        break;

      case "peer_left":
        this.refreshParticipants(data.participants || []);
        if (this.peerConnection) {
          this.peerConnection.close();
          this.peerConnection = null;
        }
        break;

      case "webrtc_offer":
        await this.handleWebRTCOffer(data);
        break;

      case "webrtc_answer":
        await this.handleWebRTCAnswer(data);
        break;

      case "webrtc_ice":
        await this.handleWebRTCIce(data);
        break;

      case "peer_speaking":
        if (this.remoteAvatar && data.session_id !== this.mySessionId) {
          if (data.is_speaking) this.remoteAvatar.classList.add("speaking");
          else this.remoteAvatar.classList.remove("speaking");
        }
        break;

      case "ai_processing":
        if (this.remoteAvatar) this.remoteAvatar.classList.add("translating");
        if (this.bridgeStatus) this.bridgeStatus.textContent = "🤖 AI ayaa u hadlaysa...";
        break;

      case "ai_idle":
        if (this.remoteAvatar) this.remoteAvatar.classList.remove("translating");
        if (this.bridgeStatus) this.bridgeStatus.textContent = "⚡ AI Diyaar bay u tahay";
        break;

      case "translation_complete":
        this.displaySubtitle(data);
        break;

      case "languages_updated":
        this.refreshParticipants(data.participants || []);
        break;
    }
  }

  // --- WebRTC Peer-to-Peer Engine ---
  async getOrCreatePeerConnection() {
    if (this.peerConnection) return this.peerConnection;

    this.peerConnection = new RTCPeerConnection(this.rtcConfig);

    // Add local audio and video tracks
    if (this.localStream) {
      this.localStream.getTracks().forEach(track => {
        this.peerConnection.addTrack(track, this.localStream);
      });
    }

    // Handle incoming direct P2P audio/video stream
    this.peerConnection.ontrack = (event) => {
      console.log("Received WebRTC direct media track:", event.track.kind);
      this.remoteStream = event.streams[0];
      if (this.remoteAudio) {
        this.remoteAudio.srcObject = this.remoteStream;
        this.remoteAudio.play().catch(e => console.warn("Remote audio play warning:", e));
      }
      if (this.remoteVideo) {
        this.remoteVideo.srcObject = this.remoteStream;
        this.remoteVideo.play().catch(e => console.warn("Remote video play warning:", e));
      }
      this.updateViewMode();
    };

    // Send ICE candidates to peer via WebSocket signaling
    this.peerConnection.onicecandidate = (event) => {
      if (event.candidate && this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({
          type: "webrtc_ice",
          candidate: event.candidate
        }));
      }
    };

    return this.peerConnection;
  }

  async createWebRTCOffer() {
    try {
      const pc = await this.getOrCreatePeerConnection();
      const offer = await pc.createOffer();
      await pc.setLocalDescription(offer);

      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({
          type: "webrtc_offer",
          sdp: offer
        }));
      }
    } catch (e) {
      console.error("Error creating WebRTC offer:", e);
    }
  }

  async handleWebRTCOffer(data) {
    try {
      const pc = await this.getOrCreatePeerConnection();
      await pc.setRemoteDescription(new RTCSessionDescription(data.sdp));
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);

      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify({
          type: "webrtc_answer",
          sdp: answer
        }));
      }
    } catch (e) {
      console.error("Error handling WebRTC offer:", e);
    }
  }

  async handleWebRTCAnswer(data) {
    try {
      if (this.peerConnection) {
        await this.peerConnection.setRemoteDescription(new RTCSessionDescription(data.sdp));
      }
    } catch (e) {
      console.error("Error handling WebRTC answer:", e);
    }
  }

  async handleWebRTCIce(data) {
    try {
      if (this.peerConnection && data.candidate) {
        await this.peerConnection.addIceCandidate(new RTCIceCandidate(data.candidate));
      }
    } catch (e) {
      console.warn("Error adding ICE candidate:", e);
    }
  }

  // --- UI Updates ---
  refreshParticipants(participants) {
    if (!this.mySessionId) return;

    const other = participants.find(p => p.session_id !== this.mySessionId);
    if (other) {
      this.counterpart = other;
      this.updateRemoteUI(other);
      this.updateStatus(`Khadka: ${other.full_name || other.username}`, "connected");
    } else {
      this.counterpart = null;
      this.resetRemoteUI();
      this.updateStatus("Qofka labaad ayaa la sugayaa...", "waiting");
    }
  }

  updateLocalUI(participant) {
    if (!participant) return;
    if (this.localName) this.localName.textContent = `${participant.full_name || participant.username} (Adiga)`;
    if (this.localLangBadge) this.localLangBadge.textContent = `🗣️ ${participant.speaking_language.toUpperCase()}`;
  }

  updateRemoteUI(other) {
    if (!other) return;
    if (this.remoteName) this.remoteName.textContent = other.full_name || other.username;
    if (this.remoteLangBadge) this.remoteLangBadge.textContent = `👂 ${other.listening_language.toUpperCase()} | 🗣️ ${other.speaking_language.toUpperCase()}`;
    if (this.bridgeStatus) {
      this.bridgeStatus.textContent = `⚡ AI Bridge: ${this.mySpeakingSelect ? this.mySpeakingSelect.value.toUpperCase() : 'SO'} ➔ ${other.listening_language.toUpperCase()}`;
    }
  }

  resetRemoteUI() {
    if (this.remoteName) this.remoteName.textContent = "Qof kale ayaa la sugayaa...";
    if (this.remoteLangBadge) this.remoteLangBadge.textContent = "Sugaya...";
    if (this.bridgeStatus) this.bridgeStatus.textContent = "Sugaya qofka labaad...";
  }

  updateViewMode() {
    const hasRemoteVideo = this.remoteStream && this.remoteStream.getVideoTracks().length > 0;
    const isVideoMode = this.isCameraOn || hasRemoteVideo;

    if (this.videoCallStage && this.voiceCallStage) {
      if (isVideoMode) {
        this.videoCallStage.classList.remove("hidden");
        this.voiceCallStage.classList.add("hidden");
      } else {
        this.videoCallStage.classList.add("hidden");
        this.voiceCallStage.classList.remove("hidden");
      }
    }
  }

  displaySubtitle(data) {
    if (!this.subtitlesContainer) return;

    if (this.latencyBadge && data.total_latency_ms) {
      this.latencyBadge.textContent = `⚡ ${(data.total_latency_ms / 1000).toFixed(2)}s`;
      this.latencyBadge.classList.remove("hidden");
    }

    const card = document.createElement("div");
    card.className = "p-2.5 rounded-xl bg-slate-900/90 border border-slate-700/80 shadow text-xs space-y-1";
    card.innerHTML = `
      <div class="flex justify-between items-center text-[10px] text-indigo-400 font-semibold">
        <span>🗣️ ${data.speaker_name} (${data.source_lang.toUpperCase()} ➔ ${data.target_lang.toUpperCase()})</span>
        <span class="text-emerald-400">${(data.total_latency_ms / 1000).toFixed(2)}s</span>
      </div>
      <div class="text-slate-300 italic text-[11px]">"${data.original_text}"</div>
      <div class="text-white font-medium text-xs flex items-center gap-1">
        <span class="text-indigo-400 font-bold">🤖 AI:</span> "${data.translated_text}"
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

      const userNative = this.user?.native_language || localStorage.getItem("preferred_native_lang") || "so";
      const userTarget = this.user?.target_language || localStorage.getItem("preferred_target_lang") || userNative || "so";
      const userVoice = this.user?.preferred_voice || "male";

      populate(this.mySpeakingSelect, userNative);
      populate(this.myListeningSelect, userTarget);
      if (this.voiceGenderSelect) this.voiceGenderSelect.value = userVoice;

      if (this.localLangBadge) {
        this.localLangBadge.textContent = `🗣️ ${userNative.toUpperCase()}`;
      }
    } catch (e) {
      console.warn("Could not load languages:", e);
    }
  }

  setupEventListeners() {
    const unlockAudio = () => {
      if (this.audioUnlockOverlay) this.audioUnlockOverlay.classList.add("hidden");
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      if (ctx.state === "suspended") ctx.resume();

      // Silent trigger to unlock HTML5 Audio autoplay policy permanently
      try {
        const silentAudio = new Audio("data:audio/wav;base64,UklGRigAAABXQVZFZm10IBIAAAABAAEARKwAAIhYAQACABAAAABkYXRhAgAAAAEA");
        silentAudio.play().catch(() => {});
      } catch (e) {}

      if (this.remoteAudio) {
        this.remoteAudio.play().catch(() => {});
      }
      if (this.remoteVideo) {
        this.remoteVideo.play().catch(() => {});
      }
    };
    document.addEventListener("click", unlockAudio, { once: true });
    if (this.audioUnlockOverlay) this.audioUnlockOverlay.onclick = unlockAudio;

    // Toggle Camera (Video Call Option requested)
    if (this.cameraBtn) {
      this.cameraBtn.onclick = async () => {
        this.isCameraOn = !this.isCameraOn;
        this.cameraBtn.classList.toggle("bg-indigo-600", this.isCameraOn);
        this.cameraBtn.classList.toggle("bg-slate-800", !this.isCameraOn);

        if (this.localStream) {
          const videoTrack = this.localStream.getVideoTracks()[0];
          if (videoTrack) {
            videoTrack.enabled = this.isCameraOn;
          } else if (this.isCameraOn) {
            // Need to request video
            try {
              const videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
              const newVideoTrack = videoStream.getVideoTracks()[0];
              this.localStream.addTrack(newVideoTrack);
              if (this.localVideo) this.localVideo.srcObject = this.localStream;
              if (this.peerConnection) {
                this.peerConnection.addTrack(newVideoTrack, this.localStream);
                await this.createWebRTCOffer();
              }
            } catch (err) {
              console.warn("Could not enable camera:", err);
            }
          }
        }
        this.updateViewMode();
      };
    }

    // Mute Microphone
    if (this.muteBtn) {
      this.muteBtn.onclick = () => {
        this.isMuted = !this.isMuted;
        if (this.localStream) {
          this.localStream.getAudioTracks().forEach(t => t.enabled = !this.isMuted);
        }
        if (this.streamer) this.streamer.setMuted(this.isMuted);
        this.muteBtn.classList.toggle("bg-red-600", this.isMuted);
        this.muteBtn.classList.toggle("bg-slate-800", !this.isMuted);
        this.muteBtn.innerHTML = this.isMuted 
          ? `<span class="text-xl">🔇</span>` 
          : `<span class="text-xl">🎤</span>`;
      };
    }

    // Toggle In-Call Captions / Chat
    if (this.toggleCaptionsBtn && this.captionsDrawer) {
      this.toggleCaptionsBtn.onclick = () => {
        this.captionsDrawer.classList.toggle("hidden");
      };
    }

    // End Call
    if (this.endCallBtn) {
      this.endCallBtn.onclick = () => this.hangUp();
    }

    // In-Call Language Switcher
    const notifyLangChange = () => {
      const speakingLang = this.mySpeakingSelect ? this.mySpeakingSelect.value : "so";
      const listeningLang = this.myListeningSelect ? this.myListeningSelect.value : "so";
      const voiceGender = this.voiceGenderSelect ? this.voiceGenderSelect.value : "male";

      localStorage.setItem("preferred_native_lang", speakingLang);
      localStorage.setItem("preferred_target_lang", listeningLang);

      const payload = {
        type: "update_languages",
        speaking_language: speakingLang,
        listening_language: listeningLang,
        voice_gender: voiceGender
      };
      if (this.socket && this.socket.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify(payload));
      }
      if (this.localLangBadge && payload.speaking_language) {
        this.localLangBadge.textContent = `🗣️ ${payload.speaking_language.toUpperCase()}`;
      }
    };

    if (this.mySpeakingSelect) this.mySpeakingSelect.onchange = notifyLangChange;
    if (this.myListeningSelect) this.myListeningSelect.onchange = notifyLangChange;
    if (this.voiceGenderSelect) this.voiceGenderSelect.onchange = notifyLangChange;
  }

  hangUp() {
    this.isCallEnded = true;
    if (this.pingInterval) clearInterval(this.pingInterval);
    if (this.peerConnection) {
      try { this.peerConnection.close(); } catch (e) {}
    }
    if (this.localStream) {
      this.localStream.getTracks().forEach(t => t.stop());
    }
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
