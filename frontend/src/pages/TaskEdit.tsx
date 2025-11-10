import { useState, useEffect } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { API_BASE_URL } from '../config/api'
import logo from '../assets/logo.png'
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
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [task, setTask] = useState<Task | null>(null)
  const [formData, setFormData] = useState<TaskFormData>({
    prompt: '',
    model: 'o3',
    provider: 'openai'
  })
  const [showAdvanced, setShowAdvanced] = useState(false)
  const [activeTab, setActiveTab] = useState<'editor' | 'executions'>('editor')

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
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update task')
    } finally {
      setSaving(false)
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
      {/* Header with Tabs */}
      <header className="w-full bg-[#2a2a2a] border-b border-white/10 px-6 py-3">
        <div className="flex items-center justify-between">
          {/* Left: Logo and Breadcrumb */}
          <div className="flex items-center gap-4 flex-1">
            <img
              src={logo}
              alt="Webagent"
              className="h-8 cursor-pointer"
              onClick={() => navigate('/')}
            />
            <div className="flex items-center gap-2 text-sm text-white/60">
              <Link to="/" className="hover:text-white transition-colors">Home</Link>
              <span>›</span>
              <span className="text-white">Task #{task.id}</span>
            </div>
          </div>

          {/* Center: Tabs */}
          <div className="flex gap-6 flex-1 justify-center">
            <button
              onClick={() => setActiveTab('editor')}
              className={`py-3 px-1 border-b-2 transition-colors font-medium ${
                activeTab === 'editor'
                  ? 'border-[#646cff] text-white'
                  : 'border-transparent text-white/60 hover:text-white'
              }`}
            >
              Editor
            </button>
            <button
              onClick={() => setActiveTab('executions')}
              className={`py-3 px-1 border-b-2 transition-colors font-medium ${
                activeTab === 'executions'
                  ? 'border-[#646cff] text-white'
                  : 'border-transparent text-white/60 hover:text-white'
              }`}
            >
              Executions
            </button>
          </div>

          {/* Right: GitHub Link */}
          <div className="flex-1 flex justify-end">
            <a
              href="https://github.com/webagent-cloud/webagent"
              target="_blank"
              rel="noopener noreferrer"
              className="text-white/60 hover:text-white transition-colors text-sm flex items-center gap-2"
            >
              <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
              </svg>
              GitHub
            </a>
          </div>
        </div>
      </header>

      {activeTab === 'editor' ? (
        <>
          {/* Control Bar */}
          <div className="w-full bg-[#2a2a2a] border-b border-white/10 px-6 py-4">
            <div className="flex items-center gap-4">
              {/* Prompt Input */}
              <div className="flex-1">
                <input
                  type="text"
                  value={formData.prompt}
                  onChange={(e) => setFormData({ ...formData, prompt: e.target.value })}
                  placeholder="Task prompt..."
                  className="w-full px-3 py-2 border border-white/20 rounded bg-[#1a1a1a] text-white text-sm focus:outline-none focus:border-[#646cff]"
                />
              </div>

              {/* Advanced Parameters Toggle */}
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="px-4 py-2 bg-[#1a1a1a] border border-white/20 rounded text-white/80 text-sm hover:bg-white/5 transition-colors"
              >
                {showAdvanced ? 'Hide' : 'Show'} Advanced
              </button>

              {/* Save Button */}
              <button
                onClick={handleSave}
                disabled={saving || !formData.prompt}
                className="px-6 py-2 bg-[#646cff] text-white border-none rounded text-sm font-semibold cursor-pointer transition-colors duration-300 hover:bg-[#535bf2] disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {saving ? 'Saving...' : 'Save'}
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
        </>
      ) : (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-white/60">Executions view coming soon...</p>
        </div>
      )}
    </div>
  )
}
