import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

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