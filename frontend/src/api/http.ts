import axios, { AxiosError } from "axios";
import { message } from "antd";

export const http = axios.create({
  baseURL: "/api",
  timeout: 30000,
});

http.interceptors.response.use(
  (res) => res,
  (error: AxiosError<{ detail?: string }>) => {
    const detail = error.response?.data?.detail || error.message || "请求失败";
    message.error(typeof detail === "string" ? detail : "服务暂时不可用");
    return Promise.reject(error);
  }
);
