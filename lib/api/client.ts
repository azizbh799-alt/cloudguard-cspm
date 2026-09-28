import { apiUrl } from '@/lib/mock/data'
export const apiClient={baseUrl:apiUrl,async get<T>(path:string):Promise<T>{const response=await fetch(`${apiUrl}${path}`);if(!response.ok)throw new Error('API request failed');return response.json() as Promise<T>}}
export const mockApi={async get<T>(data:T):Promise<T>{return Promise.resolve(data)}}
