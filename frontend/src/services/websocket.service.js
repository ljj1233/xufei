import { ref } from 'vue';

export class WebSocketService {
  constructor() {
    this.socket = null;
    this.isConnected = ref(false);
    this.listeners = new Map();
  }

  connect(clientId) {
    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/${clientId}`;
    this.socket = new WebSocket(wsUrl);

    this.socket.onopen = () => {
      console.log('WebSocket已连接');
      this.isConnected.value = true;
    };

    this.socket.onclose = () => {
      console.log('WebSocket已断开');
      this.isConnected.value = false;
      // 尝试重新连接
      setTimeout(() => this.connect(clientId), 5000);
    };

    this.socket.onerror = (error) => {
      console.error('WebSocket错误:', error);
    };

    this.socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        const { type } = message;
        
        if (this.listeners.has(type)) {
          this.listeners.get(type).forEach(callback => callback(message));
        }
      } catch (error) {
        console.error('解析WebSocket消息时出错:', error);
      }
    };
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
    }
  }

  send(type, data = {}) {
    if (this.socket && this.isConnected.value) {
      this.socket.send(JSON.stringify({
        type,
        data,
        timestamp: Date.now()
      }));
    } else {
      console.error('WebSocket未连接');
    }
  }

  on(type, callback) {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, []);
    }
    this.listeners.get(type).push(callback);
  }

  off(type, callback) {
    if (this.listeners.has(type)) {
      const callbacks = this.listeners.get(type);
      const index = callbacks.indexOf(callback);
      if (index !== -1) {
        callbacks.splice(index, 1);
      }
    }
  }
}

// 创建单例
export const webSocketService = new WebSocketService(); 