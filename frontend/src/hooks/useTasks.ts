import { useState, useEffect } from 'react'

export interface Task {
  id: number
  prompt: string
  model: string
  provider: string
  created_at: string
  status?: string
}

export interface UseTasksReturn {
  tasks: Task[]
  loading: boolean
  error: string | null
  refreshTasks: () => Promise<void>
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080'

export const useTasks = (): UseTasksReturn => {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchTasks = async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/tasks`)

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(
          errorData.detail ||
          `API error: ${response.status} ${response.statusText}`
        )
      }

      const data = await response.json()
      setTasks(data.tasks || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTasks()
  }, [])

  const refreshTasks = async () => {
    await fetchTasks()
  }

  return {
    tasks,
    loading,
    error,
    refreshTasks
  }
}
