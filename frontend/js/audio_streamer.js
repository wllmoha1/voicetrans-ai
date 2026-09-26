// Audio Streamer with Browser-Side Voice Activity Detection (VAD)
// Optimized for low-latency fast turnaround and short word captures

class AudioStreamer {
  constructor(options = {}) {
    this.onAudioChunk = options.onAudioChunk || (() => {});
    this.onSpeakingStateChange = options.onSpeakingStateChange || (() => {});
    this.onVisualizerData = options.onVisualizerData || (() => {});

    this.mediaStream = null;
    this.audioContext = null;
    this.analyser = null;
    this.mediaRecorder = null;
    this.audioChunks = [];

    this.isMuted = false;
    this.isSpeaking = false;
    this.silenceTimer = null;
    this.silenceThreshold = options.silenceThreshold || 0.018; // Sensitive voice energy
    this.silenceDurationMs = options.silenceDurationMs || 450;   // Fast pause detection
    this.animationFrameId = null;
  }

  async start() {
    try {
      this.mediaStream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          channelCount: 1,
          sampleRate: 16000
        }
      });

      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      if (this.audioContext.state === "suspended") {
        await this.audioContext.resume();
      }

      const source = this.audioContext.createMediaStreamSource(this.mediaStream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 512;
      this.analyser.smoothingTimeConstant = 0.3;
      source.connect(this.analyser);

      this.initMediaRecorder();
      this.startVADLoop();

      console.log("AudioStreamer started and capturing mic.");
      return true;
    } catch (err) {
      console.error("Microphone access failed:", err);
      throw err;
    }
  }

  initMediaRecorder() {
    let mimeType = "audio/webm;codecs=opus";
    if (!MediaRecorder.isTypeSupported(mimeType)) {
      mimeType = "audio/webm";
      if (!MediaRecorder.isTypeSupported(mimeType)) {
        mimeType = "audio/mp4";
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = "";
        }
      }
    }

    const options = mimeType ? { mimeType } : {};
    this.mediaRecorder = new MediaRecorder(this.mediaStream, options);

    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        this.audioChunks.push(e.data);
      }
    };

    this.mediaRecorder.onstop = () => {
      if (this.audioChunks.length > 0) {
        const fullBlob = new Blob(this.audioChunks, { type: this.mediaRecorder.mimeType || "audio/webm" });
        this.audioChunks = [];
        // Accept segments > 500 bytes (captures short words like 'Haa', 'Hello', etc.)
        if (fullBlob.size > 500) {
          console.log(`Sending speech audio segment: ${fullBlob.size} bytes`);
          this.onAudioChunk(fullBlob);
        }
      }
    };
  }

  startVADLoop() {
    const buffer = new Float32Array(this.analyser.fftSize);

    const checkVolume = () => {
      if (!this.mediaStream || this.isMuted) {
        this.animationFrameId = requestAnimationFrame(checkVolume);
        return;
      }

      this.analyser.getFloatTimeDomainData(buffer);
      
      // Calculate Root Mean Square (RMS) volume
      let sum = 0;
      for (let i = 0; i < buffer.length; i++) {
        sum += buffer[i] * buffer[i];
      }
      const rms = Math.sqrt(sum / buffer.length);

      this.onVisualizerData(rms);

      // Check speech activity
      if (rms > this.silenceThreshold) {
        if (!this.isSpeaking) {
          this.isSpeaking = true;
          this.onSpeakingStateChange(true);
          this.startRecordingChunk();
        }

        // Reset silence pause timer whenever voice energy is detected
        if (this.silenceTimer) {
          clearTimeout(this.silenceTimer);
          this.silenceTimer = null;
        }
      } else {
        if (this.isSpeaking && !this.silenceTimer) {
          // Pause detected, wait 450ms then flush speech segment
          this.silenceTimer = setTimeout(() => {
            this.isSpeaking = false;
            this.onSpeakingStateChange(false);
            this.stopRecordingChunk();
            this.silenceTimer = null;
          }, this.silenceDurationMs);
        }
      }

      this.animationFrameId = requestAnimationFrame(checkVolume);
    };

    this.animationFrameId = requestAnimationFrame(checkVolume);
  }

  startRecordingChunk() {
    if (this.mediaRecorder && this.mediaRecorder.state === "inactive") {
      this.audioChunks = [];
      this.mediaRecorder.start(100);
    }
  }

  stopRecordingChunk() {
    if (this.mediaRecorder && this.mediaRecorder.state === "recording") {
      this.mediaRecorder.stop();
    }
  }

  setMuted(muted) {
    this.isMuted = muted;
    if (this.mediaStream) {
      this.mediaStream.getAudioTracks().forEach(track => {
        track.enabled = !muted;
      });
    }
    if (muted && this.isSpeaking) {
      this.isSpeaking = false;
      this.onSpeakingStateChange(false);
      this.stopRecordingChunk();
    }
  }

  stop() {
    if (this.animationFrameId) cancelAnimationFrame(this.animationFrameId);
    if (this.silenceTimer) clearTimeout(this.silenceTimer);
    if (this.mediaRecorder && this.mediaRecorder.state !== "inactive") {
      try { this.mediaRecorder.stop(); } catch (e) {}
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach(track => track.stop());
    }
    if (this.audioContext && this.audioContext.state !== "closed") {
      try { this.audioContext.close(); } catch (e) {}
    }
    this.isSpeaking = false;
  }
}
