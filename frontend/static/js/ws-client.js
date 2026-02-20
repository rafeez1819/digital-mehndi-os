/**
 * 🌸 Digital Mehndi OS — WebSocket Client
 * Connects frontend to Django Channels backend.
 * Receives EmotionalPackets and drives the UI in real-time.
 */

class MehndiOSClient {
  constructor(userId = 'default') {
    this.userId   = userId;
    this.ws       = null;
    this.handlers = {};
    this.state = { valence: 0.0, arousal: 0.0, dominance: 0.5 };
    this._reconnectDelay = 1000;
  }

  // ── Connection ───────────────────────────────────────────────────────────

  connect() {
    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    const url   = `${proto}://${location.host}/ws/emotion/${this.userId}/`;
    this.ws = new WebSocket(url);

    this.ws.onopen    = ()    => { this._reconnectDelay = 1000; this._emit('connected'); };
    this.ws.onclose   = ()    => { this._emit('disconnected'); this._scheduleReconnect(); };
    this.ws.onerror   = (e)   => { this._emit('error', e); };
    this.ws.onmessage = (msg) => {
      try {
        const data = JSON.parse(msg.data);
        this._handlePacket(data);
      } catch(e) { console.error('WS parse error', e); }
    };
  }

  _scheduleReconnect() {
    setTimeout(() => this.connect(), this._reconnectDelay);
    this._reconnectDelay = Math.min(this._reconnectDelay * 2, 30000);
  }

  disconnect() {
    if (this.ws) this.ws.close();
  }

  // ── Send ─────────────────────────────────────────────────────────────────

  send(text, useClaude = true) {
    if (!this._ready()) return;
    this.ws.send(JSON.stringify({
      type: 'message',
      text,
      use_claude: useClaude,
      vad: { ...this.state },
    }));
  }

  overrideVAD(valence, arousal, dominance) {
    this.state = { valence, arousal, dominance };
    if (!this._ready()) return;
    this.ws.send(JSON.stringify({ type: 'vad_override', valence, arousal, dominance }));
  }

  getHistory(limit = 20) {
    if (!this._ready()) return;
    this.ws.send(JSON.stringify({ type: 'get_history', limit }));
  }

  ping() {
    if (this._ready()) this.ws.send(JSON.stringify({ type: 'ping' }));
  }

  _ready() {
    return this.ws && this.ws.readyState === WebSocket.OPEN;
  }

  // ── Packet Router ─────────────────────────────────────────────────────────

  _handlePacket(data) {
    switch(data.type) {
      case 'connected':
        if (data.baseline_vad) this.state = { ...data.baseline_vad };
        this._emit('ready', data);
        break;
      case 'thinking':
        this._emit('thinking', data);
        break;
      case 'emotion_packet':
        if (data.vad) this.state = { ...data.vad };
        this._emit('packet', data);
        break;
      case 'vad_updated':
        if (data.vad) this.state = { ...data.vad };
        this._emit('vad_updated', data);
        break;
      case 'history':
        this._emit('history', data);
        break;
      case 'pong':
        this._emit('pong');
        break;
      case 'error':
        this._emit('error', data);
        break;
    }
  }

  // ── Event Emitter ─────────────────────────────────────────────────────────

  on(event, fn) {
    if (!this.handlers[event]) this.handlers[event] = [];
    this.handlers[event].push(fn);
    return this;
  }

  _emit(event, data) {
    (this.handlers[event] || []).forEach(fn => fn(data));
  }
}

// ── Global init ──────────────────────────────────────────────────────────────

const mehndiClient = new MehndiOSClient('user-1');

mehndiClient
  .on('ready', (data) => {
    console.log('🌸 Connected. Baseline:', data.dominant_emotion);
    window._mehndiReady = true;
    if (window.onMehndiReady) window.onMehndiReady(data);
  })
  .on('packet', (packet) => {
    if (window.onEmotionPacket) window.onEmotionPacket(packet);
  })
  .on('thinking', () => {
    if (window.onThinking) window.onThinking();
  })
  .on('disconnected', () => {
    console.warn('🌸 WebSocket disconnected. Reconnecting...');
    window._mehndiReady = false;
  });

mehndiClient.connect();
window.mehndiClient = mehndiClient;
