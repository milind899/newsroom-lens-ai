import axios from "axios";
import { AnalysisResponse, CompareResponse } from "./types";

const API_BASE = "http://localhost:8000/api";

export async function analyzeArticle(params: {
  url?: string;
  text?: string;
  file?: File;
  output_language?: string;
}): Promise<AnalysisResponse> {
  const formData = new FormData();
  if (params.url) formData.append("url", params.url);
  if (params.text) formData.append("text", params.text);
  if (params.file) formData.append("file", params.file);
  formData.append("output_language", params.output_language || "en");

  const response = await axios.post<AnalysisResponse>(
    `${API_BASE}/analyze`,
    formData,
    {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 300000, // 5 min — models may take time on first load
    }
  );
  return response.data;
}

export async function compareSources(
  urlA: string,
  urlB: string,
  outputLang: string = "en"
): Promise<CompareResponse> {
  const response = await axios.post<CompareResponse>(
    `${API_BASE}/compare`,
    { url_a: urlA, url_b: urlB, output_language: outputLang },
    { timeout: 600000 }
  );
  return response.data;
}

export async function downloadPdfReport(data: AnalysisResponse): Promise<void> {
  const response = await axios.post(`${API_BASE}/report/pdf`, data, {
    responseType: "blob",
    timeout: 30000,
  });
  const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
  const link = document.createElement("a");
  link.href = url;
  link.setAttribute("download", "newsroom-lens-report.pdf");
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
