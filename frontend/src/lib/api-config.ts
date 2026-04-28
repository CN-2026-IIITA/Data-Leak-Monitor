import { getSession } from "next-auth/react";

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
export const WS_BASE = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export async function authFetch(url: string, options: RequestInit = {}) {
  const session = await getSession();
  const headers = new Headers(options.headers || {});
  
  if (session?.accessToken) {
    headers.set('Authorization', `Bearer ${session.accessToken}`);
  }
  
  return fetch(url, { ...options, headers });
}
