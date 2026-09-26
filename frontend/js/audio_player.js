// Incoming AI Voice Audio Player with Queueing

class AudioPlayer {
  constructor(options = {}) {
    this.queue = [];
    this.isPlaying = false;
    this.currentAudio = null;
    this.isMuted = false;
    this.onPlayStart = options.onPlayStart || (() => {});
    this.onPlayEnd = options.onPlayEnd || (() => {});
  }

  setMuted(muted) {
    this.isMuted = muted;
    if (this.currentAudio) {
      this.currentAudio.muted = muted;
    }
  }

  enqueue(audioBlobOrBuffer) {
    let blob;
    if (audioBlobOrBuffer instanceof Blob) {
      blob = audioBlobOrBuffer;
    } else {
      blob = new Blob([audioBlobOrBuffer], { type: "audio/mp3" });
    }

    const url = URL.createObjectURL(blob);
    this.queue.push(url);

    if (!this.isPlaying) {
      this.playNext();
    }
  }

  playNext() {
    if (this.queue.length === 0) {
      this.isPlaying = false;
      this.currentAudio = null;
      this.onPlayEnd();
      return;
    }

    this.isPlaying = true;
    const nextUrl = this.queue.shift();
    const audio = new Audio(nextUrl);
    this.currentAudio = audio;
    audio.muted = this.isMuted;

    audio.onplay = () => {
      this.onPlayStart();
    };

    audio.onended = () => {
      URL.revokeObjectURL(nextUrl);
      this.playNext();
    };

    audio.onerror = (err) => {
      console.error("Audio playback error:", err);
      URL.revokeObjectURL(nextUrl);
      this.playNext();
    };

    audio.play().catch((err) => {
      console.warn("Autoplay was blocked or failed:", err);
      this.playNext();
    });
  }

  stop() {
    this.queue.forEach(url => URL.revokeObjectURL(url));
    this.queue = [];
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio = null;
    }
    this.isPlaying = false;
    this.onPlayEnd();
  }
}
