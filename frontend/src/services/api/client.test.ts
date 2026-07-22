import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { ApiHttpError, ApiNetworkError, ApiTimeoutError, apiRequest } from './client'

const config = { baseUrl: 'http://localhost:8000', timeoutMs: 50 }

describe('apiRequest', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('returns the parsed JSON body on a 2xx response', async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ hello: 'world' }), { status: 200 }),
    )

    const result = await apiRequest<{ hello: string }>('/api/dashboard', config)
    expect(result).toEqual({ hello: 'world' })
  })

  it('requests the concatenated base URL and path', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response('{}', { status: 200 }))

    await apiRequest('/api/runtime/state', config)

    expect(fetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/runtime/state',
      expect.objectContaining({ signal: expect.anything() }),
    )
  })

  it('throws ApiHttpError with the status and detail on a non-2xx response', async () => {
    vi.mocked(fetch).mockResolvedValue(
      new Response(JSON.stringify({ detail: 'session already exists' }), {
        status: 409,
        statusText: 'Conflict',
      }),
    )

    await expect(apiRequest('/api/runtime/start', config)).rejects.toMatchObject({
      name: 'ApiHttpError',
      status: 409,
      detail: 'session already exists',
    })
  })

  it('throws ApiHttpError even when the error body is not JSON', async () => {
    vi.mocked(fetch).mockResolvedValue(new Response('not json', { status: 500 }))

    await expect(apiRequest('/api/dashboard', config)).rejects.toBeInstanceOf(ApiHttpError)
  })

  it('throws ApiNetworkError when fetch itself rejects', async () => {
    vi.mocked(fetch).mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(apiRequest('/api/dashboard', config)).rejects.toBeInstanceOf(ApiNetworkError)
  })

  it('throws ApiTimeoutError when the request is aborted', async () => {
    vi.mocked(fetch).mockImplementation((_url, init) => {
      const signal = (init as RequestInit).signal
      return new Promise((_resolve, reject) => {
        signal?.addEventListener('abort', () => {
          reject(new DOMException('aborted', 'AbortError'))
        })
      })
    })

    await expect(apiRequest('/api/dashboard', config)).rejects.toBeInstanceOf(ApiTimeoutError)
  })
})
