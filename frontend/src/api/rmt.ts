const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export async function fetchWignerData(n: number, scale: number) {
  const response = await fetch(`${API_BASE_URL}/api/rmt/wigner`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ n, scale })
  });
  if (!response.ok) throw new Error('Failed to fetch data');
  return response.json();
}

export async function fetchMPData(n: number, p: number, scale: number) {
  const response = await fetch(`${API_BASE_URL}/api/rmt/mp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ n, p, scale })
  });
  if (!response.ok) throw new Error('Failed to fetch data');
  return response.json();
}

export async function uploadMatrix(file: File, scale: number, fillStrategy: string = 'zero', standardize: boolean = true) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('scale', scale.toString());
  formData.append('fill_strategy', fillStrategy);
  formData.append('standardize', standardize.toString());

  const response = await fetch(`${API_BASE_URL}/api/rmt/upload`, {
    method: 'POST',
    body: formData
  });
  if (!response.ok) throw new Error('Failed to upload data');
  return response.json();
}

interface AnalyzeParams {
    dataset_name: string;
    n: number;
    p: number;
    q: number;
    sparsity: number;
    lambda_plus: number;
    lambda_minus: number;
    top_eigenvalues: number[];
    outlier_count: number;
    model_name: string;
    api_key: string;
    base_url: string;
    eigenvector_summary: string;
}

export async function streamAnalyze(params: AnalyzeParams, onChunk: (text: string) => void) {
    const response = await fetch(`${API_BASE_URL}/api/rmt/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(params)
    });
    
    if (!response.ok || !response.body) throw new Error('API Request Failed Verification.');
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        onChunk(decoder.decode(value, { stream: true }));
    }
}

export async function fetchRollingData(file: File, windowSize: number = 60, stepSize: number = 1, standardize: boolean = true) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('window_size', windowSize.toString());
  formData.append('step_size', stepSize.toString());
  formData.append('standardize', standardize.toString());

  const response = await fetch(`${API_BASE_URL}/api/rmt/rolling`, {
    method: 'POST',
    body: formData
  });
  if (!response.ok) throw new Error('Failed to fetch rolling data');
  return response.json();
}

export async function fetchHeatmapRebuild(file: File, topK: number = -1, scale: number = 1.0, fillStrategy: string = 'zero', standardize: boolean = true) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('top_k', topK.toString());
  formData.append('scale', scale.toString());
  formData.append('fill_strategy', fillStrategy);
  formData.append('standardize', standardize.toString());

  const response = await fetch(`${API_BASE_URL}/api/rmt/heatmap_rebuild`, {
    method: 'POST',
    body: formData
  });
  if (!response.ok) throw new Error('Failed to rebuild heatmap');
  return response.json();
}
