import { useState, useEffect } from 'react'

interface WorkflowParameter {
  name: string
  description: string
  type: string
  exampleValue: string
}

interface WorkflowAction {
  step_number: number
  action_number: number
  name: string
  params: Record<string, any>
  is_done: boolean
  success: boolean | null
  extracted_content: string
  error: string | null
  include_in_memory: boolean
}

interface WorkflowStep {
  step_number: number
  description: string
  actions: WorkflowAction[]
}

interface Workflow {
  parameters: WorkflowParameter[]
  steps: WorkflowStep[]
}

interface WorkflowEditorProps {
  workflow: Workflow | null
  onChange: (workflow: Workflow) => void
  onToggle?: (enabled: boolean) => void
  enabled?: boolean
}

export default function WorkflowEditor({ workflow, onChange, onToggle, enabled = false }: WorkflowEditorProps) {
  const [jsonValue, setJsonValue] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (workflow) {
      setJsonValue(JSON.stringify(workflow, null, 2))
    } else {
      setJsonValue(JSON.stringify({
        parameters: [],
        steps: []
      }, null, 2))
    }
  }, [workflow])

  const handleJsonChange = (value: string) => {
    setJsonValue(value)
    setError(null)

    try {
      if (value.trim()) {
        const parsed = JSON.parse(value)
        onChange(parsed)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid JSON')
    }
  }

  return (
    <div className="h-full flex flex-col bg-[#1a1a1a]">
      {/* Workflow Header */}
      <div className="px-6 py-4 border-b border-white/10 bg-[#2a2a2a] flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h3 className="m-0 text-lg font-semibold text-white">Cached Workflow</h3>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => onToggle?.(e.target.checked)}
              className="w-4 h-4 accent-[#646cff]"
            />
            <span className="text-sm text-white/80">Enable cached workflow</span>
          </label>
        </div>
        {error && (
          <span className="text-xs text-red-400">Invalid JSON</span>
        )}
      </div>

      {/* Workflow Content */}
      <div className="flex-1 overflow-hidden flex">
        {/* JSON Editor */}
        <div className="flex-1 flex flex-col">
          <textarea
            value={jsonValue}
            onChange={(e) => handleJsonChange(e.target.value)}
            disabled={!enabled}
            className="flex-1 w-full px-6 py-4 bg-[#1a1a1a] text-white font-mono text-xs resize-none focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed"
            placeholder={enabled ? 'Enter workflow JSON...' : 'Enable cached workflow to edit'}
          />
        </div>

        {/* Info Panel */}
        <div className="w-96 border-l border-white/10 bg-[#2a2a2a] p-6 overflow-y-auto">
          <h4 className="mt-0 mb-4 text-sm font-semibold text-white">Workflow Structure</h4>

          <div className="space-y-4 text-xs">
            <div>
              <p className="mb-2 font-semibold text-blue-400">Parameters</p>
              <pre className="text-white/70 overflow-x-auto bg-[#1a1a1a] p-3 rounded border border-white/10">
{`{
  "name": "paramName",
  "description": "...",
  "type": "string",
  "exampleValue": "value"
}`}
              </pre>
            </div>

            <div>
              <p className="mb-2 font-semibold text-green-400">Steps & Actions</p>
              <pre className="text-white/70 overflow-x-auto bg-[#1a1a1a] p-3 rounded border border-white/10">
{`{
  "step_number": 1,
  "description": "...",
  "actions": [
    {
      "step_number": 1,
      "action_number": 1,
      "name": "navigate",
      "params": {
        "url": "https://..."
      },
      "is_done": false,
      "success": null,
      "extracted_content": "",
      "error": null,
      "include_in_memory": false
    }
  ]
}`}
              </pre>
            </div>

            <div>
              <p className="mb-2 font-semibold text-purple-400">Available Actions</p>
              <ul className="list-disc list-inside text-white/70 space-y-1">
                <li>navigate - Go to URL</li>
                <li>click - Click element</li>
                <li>input - Type text</li>
                <li>scroll - Scroll page</li>
                <li>wait - Wait seconds</li>
                <li>done - Finish task</li>
              </ul>
            </div>

            <div>
              <p className="mb-2 font-semibold text-yellow-400">Template Variables</p>
              <p className="text-white/70">
                Use <code className="bg-[#1a1a1a] px-1 py-0.5 rounded">{'{{ paramName }}'}</code> to insert parameter values into actions.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
