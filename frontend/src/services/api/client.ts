/**
 * The one HTTP primitive every api/ module builds on. Distinguishes
 * three failure modes a REST-backed DashboardService needs to handle
 * differently (see docs/API_GUIDE.md's "Error handling"):
 *
 * - ApiHttpError - the backend responded, but with a non-2xx status
 *   (e.g. 409 from an invalid runtime transition).
 * - ApiTimeoutError - no response within `timeoutMs` (AbortController).
 * - ApiNetworkError - the request never reached a server at all
 *   (backend unavailable, DNS failure, CORS rejection, offline).
 */

export class ApiHttpError extends Error {
  readonly status: number
  readonly statusText: string
  readonly detail: string | undefined

  constructor(status: number, statusText: string, detail?: string) {
    super(detail ?? `HTTP ${status} ${statusText}`)
    this.name = 'ApiHttpError'
    this.status = status
    this.statusText = statusText
    this.detail = detail
  }
}

export class ApiTimeoutError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ApiTimeoutError'
  }
}

export class ApiNetworkError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'ApiNetworkError'
  }
}

export interface ApiClientConfig {
  baseUrl: string
  timeoutMs: number
}

async function parseErrorDetail(response: Response): Promise<string | undefined> {
  try {
    const body: unknown = await response.json()
    if (body && typeof body === 'object' && 'detail' in body) {
      const detail = (body as { detail: unknown }).detail
      return typeof detail === 'string' ? detail : undefined
    }
    return undefined
  } catch {
    return undefined
  }
}

export async function apiRequest<T>(
  path: string,
  config: ApiClientConfig,
  init?: RequestInit,
): Promise<T> {
  const controller = new AbortController()
  const timeoutHandle = setTimeout(() => controller.abort(), config.timeoutMs)

  try {
    let response: Response
    try {
      response = await fetch(`${config.baseUrl}${path}`, { ...init, signal: controller.signal })
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        throw new ApiTimeoutError(`${path} timed out after ${config.timeoutMs}ms`)
      }
      throw new ApiNetworkError(
        error instanceof Error ? error.message : `network error requesting ${path}`,
      )
    }

    if (!response.ok) {
      const detail = await parseErrorDetail(response)
      throw new ApiHttpError(response.status, response.statusText, detail)
    }

    return (await response.json()) as T
  } finally {
    clearTimeout(timeoutHandle)
  }
}
