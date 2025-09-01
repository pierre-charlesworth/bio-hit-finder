/**
 * API client for bio-hit-finder backend
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  });

  if (!response.ok) {
    throw new ApiError(response.status, `API Error: ${response.statusText}`);
  }

  return response.json();
}

export const api = {
  // Health check
  health: () => apiRequest<{ status: string; service: string }>('/health'),
  
  // Test endpoint
  test: () => apiRequest<{ message: string }>('/v1/test'),

  // File upload endpoints (to be implemented)
  uploadFile: async (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/v1/upload`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new ApiError(response.status, 'File upload failed');
    }
    
    return response.json();
  },

  // Multi-stage analysis endpoints
  analyzeMultiStage: async (file: File, config?: any) => {
    const formData = new FormData();
    formData.append('file', file);
    if (config) {
      formData.append('config', JSON.stringify(config));
    }
    
    const response = await fetch(`${API_BASE_URL}/v1/analyze/multi-stage`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new ApiError(response.status, 'Multi-stage analysis failed');
    }
    
    return response.json();
  },

  analyzeVitality: async (file: File, config?: any) => {
    const formData = new FormData();
    formData.append('file', file);
    if (config) {
      formData.append('config', JSON.stringify(config));
    }
    
    const response = await fetch(`${API_BASE_URL}/v1/analyze/vitality`, {
      method: 'POST',
      body: formData,
    });
    
    if (!response.ok) {
      throw new ApiError(response.status, 'Vitality analysis failed');
    }
    
    return response.json();
  },

  getDemoAnalysis: async (config?: any) => {
    return apiRequest<any>('/v1/analyze/demo', {
      method: 'POST',
      body: config ? JSON.stringify(config) : undefined,
    });
  },

  getMultiStageDefaults: () =>
    apiRequest<any>('/v1/config/multi-stage-defaults'),
};

export type { ApiError };