class DashboardSocket {
  private socket: WebSocket | null = null;

  connect(onMessage: (data: any) => void) {
    this.socket = new WebSocket("ws://127.0.0.1:8000/ws/dashboard");

    this.socket.onopen = () => {
      console.log("WebSocket Connected");
    };

    this.socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      onMessage(data);
    };

    this.socket.onclose = () => {
      console.log("WebSocket Disconnected");
    };
  }

  disconnect() {
    this.socket?.close();
  }
}

export default new DashboardSocket();