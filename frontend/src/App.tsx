import { useState, type FormEvent, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useWebagent } from './hooks/useWebagent'
import { useTasks } from './hooks/useTasks'
import logo from './assets/logo.png'

interface TaskFormData {
  prompt: string
  webhook_url?: string
  response_format?: string
  json_schema?: string
}

function App() {
  const navigate = useNavigate()
  const { runTask, loading, result, error } = useWebagent()
  const { tasks, loading: tasksLoading, error: tasksError, refreshTasks } = useTasks()
  const [formData, setFormData] = useState<TaskFormData>({
    prompt: ''
  })
  const [showAdvanced, setShowAdvanced] = useState(false)

  // Refresh task list when a new task completes
  useEffect(() => {
    if (result) {
      refreshTasks()
    }
  }, [result])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    await runTask({
      ...formData,
      wait_for_completion: true
    })
  }

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="w-full bg-white/5 border-b border-white/10 py-4 px-4">
        <div className="max-w-[1600px] mx-auto flex items-center justify-center">
          <img src={logo} alt="Webagent" className="max-w-[100px] w-full h-auto" />
        </div>
      </header>

      {/* Main Content - Centered Single Column Layout */}
      <main className="flex-1 flex flex-col items-center justify-start px-4 py-8">
        <div className="w-full max-w-[800px] flex flex-col gap-8">
        {/* Create New Task Block */}
        <div className="bg-white/5 p-8 rounded-lg">
          <h2 className="mt-0 mb-6 text-[1.75rem] text-[#646cff]">Create New Task</h2>

          <form onSubmit={handleSubmit} className="mb-4">
            {/* Task Description */}
            <div className="mb-6 text-left">
              <label htmlFor="prompt" className="block mb-2 font-semibold">
                Task Description:
              </label>
              <textarea
                id="prompt"
                value={formData.prompt}
                onChange={(e) => setFormData({ ...formData, prompt: e.target.value })}
                placeholder="e.g., go to https://example.com and get the page title"
                required
                rows={4}
                className="w-full px-3 py-2 border border-white/20 rounded bg-black/20 text-inherit font-inherit text-base resize-y min-h-[100px] focus:outline-none focus:border-[#646cff]"
              />
            </div>

            {/* Advanced Parameters Toggle */}
            <div className="mb-6">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center gap-2 text-[#646cff] hover:text-[#535bf2] transition-colors duration-300 font-semibold"
              >
                <span>{showAdvanced ? '▼' : '▶'}</span>
                <span>Advanced Parameters</span>
              </button>
            </div>

            {/* Advanced Parameters Section */}
            {showAdvanced && (
              <div className="mb-6 space-y-4 p-4 border border-white/10 rounded bg-black/10">
                {/* Response Format */}
                <div className="text-left">
                  <label htmlFor="response_format" className="block mb-2 font-semibold">
                    Response Format:
                  </label>
                  <select
                    id="response_format"
                    value={formData.response_format || 'text'}
                    onChange={(e) => setFormData({ ...formData, response_format: e.target.value })}
                    className="w-full px-3 py-2 border border-white/20 rounded bg-black/20 text-inherit font-inherit text-base focus:outline-none focus:border-[#646cff]"
                  >
                    <option value="text">Text</option>
                    <option value="json">JSON</option>
                  </select>
                </div>

                {/* JSON Schema - Only show when response format is JSON */}
                {formData.response_format === 'json' && (
                  <div className="text-left">
                    <label htmlFor="json_schema" className="block mb-2 font-semibold">
                      JSON Schema:
                    </label>
                    <textarea
                      id="json_schema"
                      value={formData.json_schema || ''}
                      onChange={(e) => setFormData({ ...formData, json_schema: e.target.value })}
                      placeholder='{"name": "schema_name", "schema": {"type": "object", "properties": {...}}}'
                      rows={6}
                      className="w-full px-3 py-2 border border-white/20 rounded bg-black/20 text-inherit font-mono text-sm resize-y focus:outline-none focus:border-[#646cff]"
                    />
                    <p className="text-xs text-white/50 mt-1">
                      Optional JSON Schema Draft 7 for structured output
                    </p>
                  </div>
                )}

                {/* Webhook URL */}
                <div className="text-left">
                  <label htmlFor="webhook_url" className="block mb-2 font-semibold">
                    Webhook URL:
                  </label>
                  <input
                    type="url"
                    id="webhook_url"
                    value={formData.webhook_url || ''}
                    onChange={(e) => setFormData({ ...formData, webhook_url: e.target.value })}
                    placeholder="https://your-webhook-endpoint.com/callback"
                    className="w-full px-3 py-2 border border-white/20 rounded bg-black/20 text-inherit font-inherit text-base focus:outline-none focus:border-[#646cff]"
                  />
                  <p className="text-xs text-white/50 mt-1">
                    Optional URL to receive webhook notification when task completes
                  </p>
                </div>
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading || !formData.prompt}
              className="w-full px-3 py-2 bg-[#646cff] text-white border-none rounded text-base font-semibold cursor-pointer transition-colors duration-300 hover:bg-[#535bf2] disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Running Task...' : 'Run Task'}
            </button>
          </form>

          {/* Error Display */}
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 p-4 rounded mb-8 text-left">
              <h3 className="mt-0 text-[#ff6b6b]">Error:</h3>
              <p>{error}</p>
            </div>
          )}

          {/* Result Display */}
          {result && (
            <div className="bg-green-500/5 border border-green-500/20 p-4 rounded text-left">
              <h3 className="mt-0 text-[#51cf66]">Result:</h3>
              <div className="mt-4">
                <p className="my-2">
                  <strong>Task ID:</strong> {result.task_id}
                </p>
                <p className="my-2">
                  <strong>Status:</strong> {result.status}
                </p>
                {result.result && (
                  <div>
                    <strong>Output:</strong>
                    <pre className="bg-black/30 p-4 rounded overflow-x-auto mt-2 text-sm">
                      {JSON.stringify(result.result, null, 2)}
                    </pre>
                  </div>
                )}
                {result.history && result.history.length > 0 && (
                  <div>
                    <strong>History:</strong>
                    <pre className="bg-black/30 p-4 rounded overflow-x-auto mt-2 text-sm">
                      {JSON.stringify(result.history, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Your Tasks Block */}
        <div className="bg-white/5 p-8 rounded-lg">
          {/* Header with Refresh Button */}
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4 sm:gap-0">
            <h2 className="m-0 text-[1.75rem] text-[#646cff]">Your Tasks</h2>
            <button
              onClick={refreshTasks}
              disabled={tasksLoading}
              className="w-full sm:w-auto px-4 py-2 bg-[#646cff]/20 text-[#646cff] border border-[#646cff] rounded text-sm cursor-pointer transition-all duration-300 hover:bg-[#646cff]/30 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {tasksLoading ? 'Loading...' : 'Refresh'}
            </button>
          </div>

          {/* Tasks Error */}
          {tasksError && (
            <div className="bg-red-500/10 border border-red-500/30 p-4 rounded">
              <p>{tasksError}</p>
            </div>
          )}

          {/* Loading State */}
          {tasksLoading && tasks.length === 0 ? (
            <p className="text-center text-white/60 py-8">Loading tasks...</p>
          ) : tasks.length === 0 ? (
            <p className="text-center text-white/60 py-8">No tasks yet. Create your first task!</p>
          ) : (
            /* Tasks List */
            <div className="flex flex-col gap-4 max-h-[600px] overflow-y-auto pr-2 [&::-webkit-scrollbar]:w-2 [&::-webkit-scrollbar-track]:bg-black/10 [&::-webkit-scrollbar-track]:rounded [&::-webkit-scrollbar-thumb]:bg-[#646cff]/30 [&::-webkit-scrollbar-thumb]:rounded [&::-webkit-scrollbar-thumb:hover]:bg-[#646cff]/50">
              {tasks.map((task) => (
                <div
                  key={task.id}
                  onClick={() => navigate(`/tasks/${task.id}`)}
                  className="bg-black/20 p-4 rounded-md border border-white/10 transition-all duration-200 hover:bg-black/30 hover:border-[#646cff]/30 cursor-pointer"
                >
                  {/* Task Header */}
                  <div className="flex justify-between items-center mb-3">
                    <span className="font-semibold text-[#646cff] text-sm">
                      Task #{task.id}
                    </span>
                    <span className="text-[0.85rem] text-white/60">
                      {task.provider} / {task.model}
                    </span>
                  </div>

                  {/* Task Prompt */}
                  <p className="my-3 leading-relaxed text-white/90">{task.prompt}</p>

                  {/* Task Footer */}
                  <div className="flex justify-between items-center mt-3 pt-3 border-t border-white/10">
                    <div className="flex items-center gap-3">
                      <span className="text-xs text-white/50">
                        {new Date(task.created_at).toLocaleString()}
                      </span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(`/tasks/${task.id}`)
                        }}
                        className="text-xs px-3 py-1 bg-[#646cff]/20 text-[#646cff] border border-[#646cff] rounded hover:bg-[#646cff]/30 transition-colors duration-200"
                      >
                        Edit
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          navigate(`/tasks/${task.id}/runs`)
                        }}
                        className="text-xs px-3 py-1 bg-[#646cff]/20 text-[#646cff] border border-[#646cff] rounded hover:bg-[#646cff]/30 transition-colors duration-200"
                      >
                        Runs
                      </button>
                    </div>
                    {task.status && (
                      <span
                        className={`px-3 py-1 rounded-full text-[0.75rem] font-semibold uppercase ${
                          task.status.toLowerCase() === 'completed'
                            ? 'bg-[#51cf66]/20 text-[#51cf66]'
                            : task.status.toLowerCase() === 'running'
                            ? 'bg-[#ffb800]/20 text-[#ffb800]'
                            : task.status.toLowerCase() === 'failed'
                            ? 'bg-[#ff6b6b]/20 text-[#ff6b6b]'
                            : 'bg-[#646cff]/20 text-[#646cff]'
                        }`}
                      >
                        {task.status}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        </div>
      </main>
    </div>
  )
}

export default App
