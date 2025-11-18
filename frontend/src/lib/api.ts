import createClient from 'openapi-fetch';
import type { paths } from '@/types/api';

export const api = createClient<paths>({
  baseUrl: (process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000') + '/v1',
});


