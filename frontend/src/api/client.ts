/** Minimal typed fetch wrapper for the DevVault API. */

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: unknown;
  request_id?: string | null;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId: string | null;

  constructor(status: number, code: string, message: string, requestId: string | null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.requestId = requestId;
  }
}

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

function isErrorEnvelope(value: unknown): value is { error: ApiErrorBody } {
  return (
    typeof value === 'object' &&
    value !== null &&
    'error' in value &&
    typeof (value as { error: unknown }).error === 'object'
  );
}

export interface RequestOptions {
  signal?: AbortSignal;
  /** HTTP statuses (besides 2xx) whose JSON body is a valid result rather than an error. */
  acceptStatuses?: number[];
}

export async function getJson<T>(path: string, options: RequestOptions = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      headers: { Accept: 'application/json' },
      ...(options.signal ? { signal: options.signal } : {}),
    });
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === 'AbortError') throw cause;
    throw new ApiError(0, 'network_error', 'Could not reach the DevVault API', null);
  }

  const requestId = response.headers.get('X-Request-ID');
  const body: unknown = await response.json().catch(() => null);

  if (response.ok || options.acceptStatuses?.includes(response.status)) {
    return body as T;
  }
  if (isErrorEnvelope(body)) {
    throw new ApiError(response.status, body.error.code, body.error.message, requestId);
  }
  throw new ApiError(
    response.status,
    'http_error',
    `Request failed (${response.status})`,
    requestId,
  );
}
