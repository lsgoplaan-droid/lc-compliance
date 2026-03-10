import axios from "axios";

const rawUrl = import.meta.env.VITE_API_URL || "/api";
const baseURL = rawUrl.endsWith("/api") ? rawUrl : `${rawUrl.replace(/\/+$/, "")}/api`;

const api = axios.create({
  baseURL,
  headers: { "Content-Type": "application/json" },
});

export default api;
