// Re-exports the single authenticated Axios instance so every service file
// (asset.ts, ticket.ts, alert.ts, dashboard.ts, monitoring.ts, websocket.ts)
// automatically attaches the JWT Bearer token on every request.
// Previously this file created a second, un-authenticated Axios client,
// which meant any protected endpoint reached through the services/* layer
// silently went out with no Authorization header.
import api from "../api/client";

export default api;
