import { useQuery, useMutation } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { AnalysisResult, MultiStageConfig } from '@/types/analysis';

export function useHealthCheck() {
  return useQuery({
    queryKey: ['health'],
    queryFn: api.health,
    staleTime: 30 * 1000, // 30 seconds
  });
}

export function useApiTest() {
  return useQuery({
    queryKey: ['api-test'],
    queryFn: api.test,
    staleTime: 30 * 1000, // 30 seconds
  });
}

export function useMultiStageDefaults() {
  return useQuery({
    queryKey: ['multi-stage-defaults'],
    queryFn: api.getMultiStageDefaults,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useMultiStageAnalysis() {
  return useMutation<AnalysisResult, Error, { file: File; config?: Partial<MultiStageConfig> }>({
    mutationFn: ({ file, config }) => api.analyzeMultiStage(file, config),
  });
}

export function useVitalityAnalysis() {
  return useMutation<AnalysisResult, Error, { file: File; config?: any }>({
    mutationFn: ({ file, config }) => api.analyzeVitality(file, config),
  });
}

export function useDemoAnalysis() {
  return useMutation<AnalysisResult, Error, { config?: Partial<MultiStageConfig> }>({
    mutationFn: ({ config }) => api.getDemoAnalysis(config),
  });
}

export function useAnalysisDefaults() {
  return useQuery({
    queryKey: ['analysisDefaults'],
    queryFn: () => api.getAnalysisDefaults(),
    staleTime: 10 * 60 * 1000, // 10 minutes
  });
}