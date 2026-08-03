import api from "./api";

export interface LoginPayload {
  username: string;
  password: string;
}

export interface RegisterPayload {
  username: string;
  email: string;
  full_name: string;
  password: string;
  role_id?: number | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface CurrentUser {
  id: number;
  username: string;
  email: string;
  full_name: string;
  is_active: boolean;
  role_id?: number | null;
}

// Backend uses FastAPI's OAuth2PasswordRequestForm, which requires
// application/x-www-form-urlencoded body (NOT JSON).
export const login = async (
  payload: LoginPayload
): Promise<TokenResponse> => {
  const form = new URLSearchParams();
  form.append("username", payload.username);
  form.append("password", payload.password);

  const response = await api.post<TokenResponse>("/auth/login", form, {
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
  });

  return response.data;
};

export const register = async (payload: RegisterPayload) => {
  const response = await api.post("/auth/register", payload);
  return response.data;
};

export const getCurrentUser = async (): Promise<CurrentUser> => {
  const response = await api.get<CurrentUser>("/auth/me");
  return response.data;
};
