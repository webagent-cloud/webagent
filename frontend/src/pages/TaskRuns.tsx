import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { API_BASE_URL } from '../config/api'
import TaskHeader from '../components/TaskHeader'

interface TaskRun {
  id: number
  description: string
  is_done: boolean
  is_successful: boolean | null
}

interface TaskRunDetails {
  id: number
  task_id: number
  prompt: string
  model: string
  provider: string
  webhook_url?: string
  response_format: string
  json_schema?: string
  result: string | null
  is_done: boolean
  is_successful: boolean | null
  webhook_result_success?: boolean | null
  webhook_result_status_code?: number | null
  webhook_result_message?: string | null
  steps: RunStep[]
}

interface RunStep {
  task_run_id: number
  step_number: number
  description: string
  screenshot?: string | null
  actions: RunAction[]
}

interface RunAction {
  id: number
  task_run_id: number
  step_number: number
  action_number: number
  name: string
  params: any
  is_done: boolean
  success: boolean | null
  extracted_content: string | null
  error: string | null
  include_in_memory: boolean | null
}

export default function TaskRuns() {
  const { id } = useParams<{ id: string }>()

  const [runs, setRuns] = useState<TaskRun[]>([])
  const [selectedRunId, setSelectedRunId] = useState<number | null>(null)
  const [runDetails, setRunDetails] = useState<TaskRunDetails | null>(null)

  const [loading, setLoading] = useState(true)
  const [detailsLoading, setDetailsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch runs list
  useEffect(() => {
    const fetchRuns = async () => {
      try {
        setLoading(true)
        const response = await fetch(`${API_BASE_URL}/tasks/${id}/runs`)
        if (!response.ok) {
          throw new Error(`Failed to fetch runs: ${response.statusText}`)
        }
        const data = await response.json()
        setRuns(data)

        // Auto-select the first run if available
        if (data.length > 0) {
          setSelectedRunId(data[0].id)
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load runs')
      } finally {
        setLoading(false)
      }
    }

    if (id) {
      fetchRuns()
    }
  }, [id])

  // Fetch run details when selected
  useEffect(() => {
    const fetchRunDetails = async () => {
      if (!selectedRunId) return

      try {
        setDetailsLoading(true)
        const response = await fetch(`${API_BASE_URL}/runs/${selectedRunId}`)
        if (!response.ok) {
          throw new Error(`Failed to fetch run details: ${response.statusText}`)
        }
        const data = await response.json()
        setRunDetails(data)
      } catch (err) {
        console.error('Error fetching run details:', err)
      } finally {
        setDetailsLoading(false)
      }
    }

    fetchRunDetails()
  }, [selectedRunId])

  const getStatusBadge = (run: TaskRun) => {
    if (!run.is_done) {
      return <span className="px-2 py-1 rounded-full text-xs font-semibold bg-yellow-500/20 text-yellow-500">Running</span>
    }
    if (run.is_successful) {
      return <span className="px-2 py-1 rounded-full text-xs font-semibold bg-green-500/20 text-green-500">Success</span>
    }
    return <span className="px-2 py-1 rounded-full text-xs font-semibold bg-red-500/20 text-red-500">Failed</span>
  }

  return (
    <div className="min-h-screen flex flex-col bg-[#1a1a1a]">
      <TaskHeader taskId={id || ''} activeTab="runs" />

      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Left Sidebar - Runs List */}
        <div className="w-80 bg-[#2a2a2a] border-r border-white/10 flex flex-col">
          <div className="p-4 border-b border-white/10">
            <h2 className="text-lg font-semibold text-white">Task Runs</h2>
            <p className="text-sm text-white/60 mt-1">{runs.length} total runs</p>
          </div>

          {loading ? (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-white/60">Loading runs...</p>
            </div>
          ) : error ? (
            <div className="flex-1 flex items-center justify-center p-4">
              <p className="text-red-500 text-sm">{error}</p>
            </div>
          ) : runs.length === 0 ? (
            <div className="flex-1 flex items-center justify-center p-4">
              <p className="text-white/60 text-sm text-center">
                No runs yet for this task.
              </p>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto">
              {runs.map((run) => (
                <button
                  key={run.id}
                  onClick={() => setSelectedRunId(run.id)}
                  className={`w-full p-4 border-b border-white/10 text-left transition-colors ${
                    selectedRunId === run.id
                      ? 'bg-[#646cff]/20 border-l-4 border-l-[#646cff]'
                      : 'hover:bg-white/5'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-white">Run #{run.id}</span>
                    {getStatusBadge(run)}
                  </div>
                  <p className="text-xs text-white/70 line-clamp-2">{run.description}</p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right Content - Run Details */}
        <div className="flex-1 overflow-y-auto p-6">
          {!selectedRunId ? (
            <div className="h-full flex items-center justify-center">
              <p className="text-white/60">Select a run to view details</p>
            </div>
          ) : detailsLoading ? (
            <div className="h-full flex items-center justify-center">
              <p className="text-white/60">Loading run details...</p>
            </div>
          ) : runDetails ? (
            <div className="max-w-4xl mx-auto">
              {/* Run Header */}
              <div className="bg-[#2a2a2a] rounded-lg p-6 mb-6">
                <div className="flex items-center justify-between mb-4">
                  <h1 className="text-2xl font-bold text-white">Run #{runDetails.id}</h1>
                  {getStatusBadge({
                    id: runDetails.id,
                    description: runDetails.prompt,
                    is_done: runDetails.is_done,
                    is_successful: runDetails.is_successful
                  })}
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex gap-2">
                    <span className="text-white/60">Prompt:</span>
                    <span className="text-white">{runDetails.prompt}</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-white/60">Model:</span>
                    <span className="text-white">{runDetails.model}</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-white/60">Provider:</span>
                    <span className="text-white">{runDetails.provider}</span>
                  </div>
                  <div className="flex gap-2">
                    <span className="text-white/60">Status:</span>
                    <span className="text-white">
                      {runDetails.is_done ? (runDetails.is_successful ? 'Success' : 'Failed') : 'Running'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Result */}
              {runDetails.result && (
                <div className="bg-[#2a2a2a] rounded-lg p-6 mb-6">
                  <h2 className="text-lg font-semibold text-white mb-4">Result</h2>
                  <pre className="bg-black/30 p-4 rounded overflow-x-auto text-sm text-white/90">
                    {runDetails.result}
                  </pre>
                </div>
              )}

              {/* Steps */}
              {runDetails.steps && runDetails.steps.length > 0 && (
                <div className="bg-[#2a2a2a] rounded-lg p-6">
                  <h2 className="text-lg font-semibold text-white mb-4">
                    Execution Steps ({runDetails.steps.length})
                  </h2>
                  <div className="space-y-4">
                    {runDetails.steps.map((step) => (
                      <div
                        key={`${step.task_run_id}-${step.step_number}`}
                        className="bg-black/20 rounded-lg p-4 border border-white/10"
                      >
                        <div className="flex items-center gap-2 mb-2">
                          <span className="px-2 py-1 bg-[#646cff]/20 text-[#646cff] rounded text-xs font-semibold">
                            Step {step.step_number}
                          </span>
                          <span className="text-white text-sm">{step.description}</span>
                        </div>

                        {step.actions && step.actions.length > 0 && (
                          <div className="mt-3 space-y-2">
                            {step.actions.map((action) => (
                              <div
                                key={action.id}
                                className="bg-black/30 rounded p-3 text-xs"
                              >
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-semibold text-white/60">Action:</span>
                                  <span className="text-white">{action.name}</span>
                                  {action.is_done && (
                                    <span className={`ml-auto px-2 py-0.5 rounded text-[0.65rem] font-semibold ${
                                      action.success
                                        ? 'bg-green-500/20 text-green-500'
                                        : 'bg-red-500/20 text-red-500'
                                    }`}>
                                      {action.success ? 'Success' : 'Failed'}
                                    </span>
                                  )}
                                </div>
                                {action.params && Object.keys(action.params).length > 0 && (
                                  <div className="text-white/60 mb-1">
                                    <span className="font-semibold">Parameters:</span>
                                    <pre className="mt-1 text-white/80 overflow-x-auto">
                                      {JSON.stringify(action.params, null, 2)}
                                    </pre>
                                  </div>
                                )}
                                {action.extracted_content && (
                                  <div className="text-white/60 mb-1">
                                    <span className="font-semibold">Extracted Content:</span>
                                    <pre className="mt-1 text-white/80 overflow-x-auto">
                                      {action.extracted_content}
                                    </pre>
                                  </div>
                                )}
                                {action.error && (
                                  <div className="text-red-400/80">
                                    <span className="font-semibold">Error:</span>
                                    <pre className="mt-1 overflow-x-auto">
                                      {action.error}
                                    </pre>
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="h-full flex items-center justify-center">
              <p className="text-red-500">Failed to load run details</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
