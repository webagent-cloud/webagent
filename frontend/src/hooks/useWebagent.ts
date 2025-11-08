import { useState } from 'react'
import { API_BASE_URL } from '../config/api'

export interface TaskRequest {
  task: string
  model: string
  provider: string
  wait_for_completion?: boolean
}

export interface TaskResult {
  task_id: string
  result?: string
  status: string
  history?: any[]
}

export interface UseWebagentReturn {
  runTask: (request: TaskRequest) => Promise<void>
  loading: boolean
  result: TaskResult | null
  error: string | null
  reset: () => void
}

export const useWebagent = (): UseWebagentReturn => {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<TaskResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const runTask = async (request: TaskRequest) => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await fetch(`${API_BASE_URL}/run`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...request,
          wait_for_completion: request.wait_for_completion ?? true
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(
          errorData.detail ||
          `API error: ${response.status} ${response.statusText}`
        )
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const reset = () => {
    setResult(null)
    setError(null)
    setLoading(false)
  }

  return {
    runTask,
    loading,
    result,
    error,
    reset
  }
}
