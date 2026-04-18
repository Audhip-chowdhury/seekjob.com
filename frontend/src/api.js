import axios from "axios";

const env = import.meta.env;
export const API_BASE =
  env.VITE_API_URL ||
  `http://${env.VITE_API_HOST ?? "localhost"}:${env.VITE_API_PORT ?? "8020"}`;

export const api = axios.create({
  baseURL: API_BASE,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("seekjob_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function mediaUrl(path) {
  if (!path) return null;
  if (path.startsWith("http")) return path;
  return `${API_BASE}/uploads/${path.replace(/^\//, "")}`;
}
