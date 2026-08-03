import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");

  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }

  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    const requestUrl: string = error?.config?.url ?? "";

    // A 401 from the login call itself just means "wrong credentials" --
    // let Login.tsx handle and display that. Only a 401 from an
    // *authenticated* request means the session is no longer valid.
    const isLoginRequest = requestUrl.includes("/auth/login");

    if (status === 401 && !isLoginRequest) {
      localStorage.removeItem("access_token");

      // Guard against redirect loops: only navigate if we're not
      // already on /login. ProtectedRoute now does the normal
      // client-side redirect via React Router; this hard redirect is
      // just a safety net for a session that expires mid-use.
      if (window.location.pathname !== "/login") {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default api;