import axios, { AxiosError } from "axios";
import { message } from "antd";
import { appStore } from "../stores/appStore";

export const http = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

http.interceptors.request.use((config) => {
  config.params = { ...config.params, user_id: appStore.userId };
  return config;
});

let lastApiToast = "";

http.interceptors.response.use(
  (res) => res,
  (error: AxiosError<{ detail?: string }>) => {
    const detail = error.response?.data?.detail || error.message || "请求失败";
    const text = typeof detail === "string" ? detail : "服务暂时不可用";
    if (text !== lastApiToast) {
      lastApiToast = text;
      window.setTimeout(() => {
        if (lastApiToast === text) lastApiToast = "";
      }, 2500);
      message.error({ content: text, key: "api-error" });
    }
    return Promise.reject(error);
  }
);
