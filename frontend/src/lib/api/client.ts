export const TOKEN_KEY = 'id_token';

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export async function apiFetch<T>(_path: string, _init: RequestInit = {}): Promise<T> {
  throw new Error('not implemented');
}
