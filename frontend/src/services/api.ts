import { 
  FactCheckResponse, 
  FactCheckHistoryItem, 
  DemoClaimItem, 
  EvaluationMetricsResponse 
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://factguard-ai.onrender.com/api/v1';

export async function verifyText(text: string): Promise<FactCheckResponse> {
  const response = await fetch(`${API_BASE_URL}/fact-check`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ input_text: text, input_type: 'text' }),
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({ detail: 'Failed to verify text.' }));
    throw new Error(errData.detail || 'Verification request failed.');
  }
  return response.json();
}

export async function verifyUrl(url: string): Promise<FactCheckResponse> {
  const formData = new FormData();
  formData.append('url', url);

  const response = await fetch(`${API_BASE_URL}/fact-check/url`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({ detail: 'Failed to verify URL.' }));
    throw new Error(errData.detail || 'URL Verification request failed.');
  }
  return response.json();
}

export async function verifyImage(file: File): Promise<FactCheckResponse> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/fact-check/image`, {
    method: 'POST',
    body: formData,
  });
  if (!response.ok) {
    const errData = await response.json().catch(() => ({ detail: 'Failed to OCR image.' }));
    throw new Error(errData.detail || 'Image OCR Verification failed.');
  }
  return response.json();
}

export async function getFactCheckHistory(): Promise<FactCheckHistoryItem[]> {
  const response = await fetch(`${API_BASE_URL}/fact-check/history`);
  if (!response.ok) return [];
  return response.json();
}

export async function getDemoClaims(): Promise<DemoClaimItem[]> {
  const response = await fetch(`${API_BASE_URL}/fact-check/demo-claims`);
  if (!response.ok) return [];
  return response.json();
}

export async function getFactCheckById(id: string): Promise<FactCheckResponse> {
  const response = await fetch(`${API_BASE_URL}/fact-check/${id}`);
  if (!response.ok) throw new Error('Report not found');
  return response.json();
}

export async function getEvaluationMetrics(): Promise<EvaluationMetricsResponse> {
  const response = await fetch(`${API_BASE_URL}/evaluations`);
  if (!response.ok) throw new Error('Failed to fetch evaluation metrics');
  return response.json();
}

export function getPdfDownloadUrl(id: string): string {
  return `${API_BASE_URL}/fact-check/${id}/pdf`;
}
