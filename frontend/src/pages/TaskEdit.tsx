import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { API_BASE_URL } from '../config/api'
import TaskHeader from '../components/TaskHeader'
import VisualWorkflowEditor from '../components/VisualWorkflowEditor'

interface Task {
  id: number
  prompt: string
  model: string
  provider: string
  webhook_url?: string
  response_format?: string
  json_schema?: string
  cached_workflow?: any
  use_cached_workflow?: boolean
}

interface TaskFormData {
  prompt: string
  model: string
  provider: string
  webhook_url?: string
  response_format?: string
  json_schema?: string
  cached_workflow?: any
  use_cached_workflow?: boolean
}

export default function TaskEdit() {
  const { id } = useParams<{ id: string }>()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [task, setTask] = useState<Task | null>(null)
  const [formData, setFormData] = useState<TaskFormData>({
    prompt: '',
    model: 'o3',
    provider: 'openai'
  })
  const [showAdvanced, setShowAdvanced] = useState(false)

  useEffect(() => {
    const fetchTask = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/tasks/${id}`)
        if (!response.ok) {
          throw new Error(`Failed to fetch task: ${response.statusText}`)
        }
        const data = await response.json()
        setTask(data)
        setFormData({
          prompt: data.prompt || '',
          model: data.model || 'o3',
          provider: data.provider || 'openai',
          webhook_url: data.webhook_url || '',
          response_format: data.response_format || 'text',
          json_schema: data.json_schema || '',
          cached_workflow: data.cached_workflow || null,
          use_cached_workflow: data.use_cached_workflow || false
        })
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load task')
      } finally {
        setLoading(false)
      }
    }

    if (id) {
      fetchTask()
    }
  }, [id])

  const handleSave = async () => {
    setSaving(true)
    setError(null)

    try {
      const response = await fetch(`${API_BASE_URL}/tasks/${id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(
          errorData.detail || `Failed to update task: ${response.statusText}`
        )
      }

      const updatedTask = await response.json()
      setTask(updatedTask)
      return true
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update task')
      return false
    } finally {
      setSaving(false)
    }
  }

  const handleSaveAndRun = async () => {
    setRunning(true)
    setError(null)

    try {
      // First save the task
      const saveSuccess = await handleSave()
      if (!saveSuccess) {
        return
      }

      // Then trigger a run
      const response = await fetch(`${API_BASE_URL}/tasks/${id}/runs`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          wait_for_completion: false
        })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(
          errorData.detail || `Failed to run task: ${response.statusText}`
        )
      }

      // Navigate to runs page to see the execution
      window.location.href = `/tasks/${id}/runs`
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to run task')
    } finally {
      setRunning(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#1a1a1a]">
        <p className="text-white/60">Loading task...</p>
      </div>
    )
  }

  if (!task) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#1a1a1a]">
        <p className="text-red-500">Task not found</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#1a1a1a]">
      <TaskHeader taskId={task.id} activeTab="editor" />

      {/* Control Bar */}
          <div className="w-full bg-[#2a2a2a] border-b border-white/10 px-6 py-4">
            {/* Prompt Textarea */}
            <div className="mb-4">
              <textarea
                value={formData.prompt}
                onChange={(e) => setFormData({ ...formData, prompt: e.target.value })}
                placeholder="Task prompt..."
                rows={4}
                className="w-full px-3 py-2 border border-white/20 rounded bg-[#1a1a1a] text-white text-sm focus:outline-none focus:border-[#646cff] resize-y"
              />
            </div>

            {/* Controls Row */}
            <div className="flex items-center gap-4">
              {/* Advanced Parameters Toggle */}
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="px-4 py-2 bg-[#1a1a1a] border border-white/20 rounded text-white/80 text-sm hover:bg-white/5 transition-colors"
              >
                {showAdvanced ? 'Hide' : 'Show'} Advanced
              </button>

              <div className="flex-1"></div>

              {/* Save Button */}
              <button
                onClick={handleSave}
                disabled={saving || !formData.prompt}
                className="px-6 py-2 bg-[#646cff] text-white border-none rounded text-sm font-semibold cursor-pointer transition-colors duration-300 hover:bg-[#535bf2] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Saving...' : 'Save'}
              </button>

              {/* Save and Run Button */}
              <button
                onClick={handleSaveAndRun}
                disabled={running || saving || !formData.prompt}
                className="px-6 py-2 bg-[#10b981] text-white border-none rounded text-sm font-semibold cursor-pointer transition-colors duration-300 hover:bg-[#059669] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {running ? 'Running...' : 'Save & Run'}
              </button>
            </div>

            {/* Advanced Parameters Section */}
            {showAdvanced && (
              <div className="mt-4 grid grid-cols-1 md:grid-cols-3 gap-4 p-4 border border-white/10 rounded bg-[#1a1a1a]">
                {/* Provider */}
                <div>
                  <label className="block mb-2 text-sm font-medium text-white/80">
                    Provider
                  </label>
                  <select
                    value={formData.provider}
                    onChange={(e) => setFormData({ ...formData, provider: e.target.value })}
                    className="w-full px-3 py-2 border border-white/20 rounded bg-[#2a2a2a] text-white text-sm focus:outline-none focus:border-[#646cff]"
                  >
                    <option value="openai">OpenAI</option>
                    <option value="anthropic">Anthropic</option>
                    <option value="google">Google</option>
                    <option value="groq">Groq</option>
                    <option value="deepseek">DeepSeek</option>
                  </select>
                </div>

                {/* Model */}
                <div>
                  <label className="block mb-2 text-sm font-medium text-white/80">
                    Model
                  </label>
                  <input
                    type="text"
                    value={formData.model}
                    onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                    placeholder="e.g., o3"
                    className="w-full px-3 py-2 border border-white/20 rounded bg-[#2a2a2a] text-white text-sm focus:outline-none focus:border-[#646cff]"
                  />
                </div>

                {/* Response Format */}
                <div>
                  <label className="block mb-2 text-sm font-medium text-white/80">
                    Response Format
                  </label>
                  <select
                    value={formData.response_format || 'text'}
                    onChange={(e) => setFormData({ ...formData, response_format: e.target.value })}
                    className="w-full px-3 py-2 border border-white/20 rounded bg-[#2a2a2a] text-white text-sm focus:outline-none focus:border-[#646cff]"
                  >
                    <option value="text">Text</option>
                    <option value="json">JSON</option>
                  </select>
                </div>

                {/* Webhook URL */}
                <div className="md:col-span-2">
                  <label className="block mb-2 text-sm font-medium text-white/80">
                    Webhook URL
                  </label>
                  <input
                    type="url"
                    value={formData.webhook_url || ''}
                    onChange={(e) => setFormData({ ...formData, webhook_url: e.target.value })}
                    placeholder="https://your-webhook-endpoint.com/callback"
                    className="w-full px-3 py-2 border border-white/20 rounded bg-[#2a2a2a] text-white text-sm focus:outline-none focus:border-[#646cff]"
                  />
                </div>

                {/* JSON Schema */}
                <div className="md:col-span-3">
                  <label className="block mb-2 text-sm font-medium text-white/80">
                    JSON Schema
                  </label>
                  <textarea
                    value={formData.json_schema || ''}
                    onChange={(e) => setFormData({ ...formData, json_schema: e.target.value })}
                    placeholder='{"name": "schema_name", "schema": {"type": "object", "properties": {...}}}'
                    rows={3}
                    className="w-full px-3 py-2 border border-white/20 rounded bg-[#2a2a2a] text-white font-mono text-xs resize-y focus:outline-none focus:border-[#646cff]"
                  />
                </div>
              </div>
            )}

            {/* Error Display */}
            {error && (
              <div className="mt-4 bg-red-500/10 border border-red-500/30 p-3 rounded">
                <p className="text-[#ff6b6b] text-sm m-0">{error}</p>
              </div>
            )}
          </div>

          {/* Workflow Editor - Full Width and Height */}
          <div className="flex-1 overflow-hidden">
            <VisualWorkflowEditor
              workflow={formData.cached_workflow}
              onChange={(workflow) => setFormData({ ...formData, cached_workflow: workflow })}
              onToggle={(enabled) => setFormData({ ...formData, use_cached_workflow: enabled })}
              enabled={formData.use_cached_workflow || false}
            />
          </div>
    </div>
  )
}
