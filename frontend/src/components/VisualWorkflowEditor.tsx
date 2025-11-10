import { useState, useEffect } from 'react'
import ParameterModal from './workflow-modals/ParameterModal'
import StepModal from './workflow-modals/StepModal'
import ActionModal from './workflow-modals/ActionModal'

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

interface VisualWorkflowEditorProps {
  workflow: Workflow | null
  onChange: (workflow: Workflow) => void
  onToggle?: (enabled: boolean) => void
  enabled?: boolean
}

const ACTION_ICONS: Record<string, string> = {
  navigate: '🌐',
  click: '👆',
  input: '⌨️',
  scroll: '📜',
  wait: '⏱️',
  done: '✅',
  extract: '📋',
  screenshot: '📸',
}

export default function VisualWorkflowEditor({
  workflow,
  onChange,
  onToggle,
  enabled = false,
}: VisualWorkflowEditorProps) {
  const [workflowData, setWorkflowData] = useState<Workflow>(workflow || { parameters: [], steps: [] })

  // Modal states
  const [parameterModal, setParameterModal] = useState<{ open: boolean; data: WorkflowParameter | null; index: number | null }>({
    open: false,
    data: null,
    index: null,
  })
  const [stepModal, setStepModal] = useState<{ open: boolean; data: WorkflowStep | null; index: number | null }>({
    open: false,
    data: null,
    index: null,
  })
  const [actionModal, setActionModal] = useState<{
    open: boolean
    data: WorkflowAction | null
    stepIndex: number | null
    actionIndex: number | null
  }>({
    open: false,
    data: null,
    stepIndex: null,
    actionIndex: null,
  })

  // Sync with external workflow changes on mount and when workflow prop changes
  useEffect(() => {
    if (workflow) {
      setWorkflowData(workflow)
    }
  }, [workflow])

  // Parameter actions
  const addParameter = () => {
    setParameterModal({ open: true, data: null, index: null })
  }

  const saveParameter = (param: WorkflowParameter) => {
    const newParams = [...workflowData.parameters]
    if (parameterModal.index !== null) {
      newParams[parameterModal.index] = param
    } else {
      newParams.push(param)
    }
    const updatedWorkflow = { ...workflowData, parameters: newParams }
    setWorkflowData(updatedWorkflow)
    onChange(updatedWorkflow)
  }

  const deleteParameter = (index: number) => {
    const newParams = workflowData.parameters.filter((_, idx) => idx !== index)
    const updatedWorkflow = { ...workflowData, parameters: newParams }
    setWorkflowData(updatedWorkflow)
    onChange(updatedWorkflow)
  }

  // Step actions
  const addStep = () => {
    setStepModal({ open: true, data: null, index: null })
  }

  const saveStep = (description: string) => {
    const newSteps = [...workflowData.steps]
    if (stepModal.index !== null) {
      newSteps[stepModal.index].description = description
    } else {
      const newStep: WorkflowStep = {
        step_number: newSteps.length + 1,
        description,
        actions: [],
      }
      newSteps.push(newStep)
    }
    const updatedWorkflow = { ...workflowData, steps: newSteps }
    setWorkflowData(updatedWorkflow)
    onChange(updatedWorkflow)
  }

  const deleteStep = (index: number) => {
    const newSteps = workflowData.steps.filter((_, idx) => idx !== index)
    // Renumber steps
    newSteps.forEach((step, idx) => {
      step.step_number = idx + 1
      step.actions.forEach(action => {
        action.step_number = idx + 1
      })
    })
    const updatedWorkflow = { ...workflowData, steps: newSteps }
    setWorkflowData(updatedWorkflow)
    onChange(updatedWorkflow)
  }

  // Action actions
  const saveAction = (actionData: { name: string; params: Record<string, any> }) => {
    if (actionModal.stepIndex === null) return

    const newSteps = [...workflowData.steps]
    const step = newSteps[actionModal.stepIndex]

    if (actionModal.actionIndex !== null) {
      // Edit existing action
      step.actions[actionModal.actionIndex] = {
        ...step.actions[actionModal.actionIndex],
        name: actionData.name,
        params: actionData.params,
      }
    } else {
      // Add new action
      const newAction: WorkflowAction = {
        step_number: step.step_number,
        action_number: step.actions.length + 1,
        name: actionData.name,
        params: actionData.params,
        is_done: false,
        success: null,
        extracted_content: '',
        error: null,
        include_in_memory: false,
      }
      step.actions.push(newAction)
    }

    const updatedWorkflow = { ...workflowData, steps: newSteps }
    setWorkflowData(updatedWorkflow)
    onChange(updatedWorkflow)
  }

  const deleteAction = (stepIndex: number, actionIndex: number) => {
    const newSteps = [...workflowData.steps]
    newSteps[stepIndex].actions = newSteps[stepIndex].actions.filter((_, idx) => idx !== actionIndex)
    // Renumber actions
    newSteps[stepIndex].actions.forEach((action, idx) => {
      action.action_number = idx + 1
    })
    const updatedWorkflow = { ...workflowData, steps: newSteps }
    setWorkflowData(updatedWorkflow)
    onChange(updatedWorkflow)
  }

  return (
    <div className="h-full flex flex-col bg-[#1a1a1a]">
      {/* Header */}
      <div className="px-6 py-4 border-b border-white/10 bg-[#2a2a2a]">
        <div className="flex items-center justify-between">
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

          {enabled && (
            <div className="flex items-center gap-3">
              {/* Parameters Section */}
              <div className="flex items-center gap-2">
                <span className="text-sm text-white/60 font-medium">Parameters:</span>
                {workflowData.parameters.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {workflowData.parameters.map((param, idx) => (
                      <button
                        key={idx}
                        onClick={() => setParameterModal({ open: true, data: param, index: idx })}
                        className="group flex items-center gap-1 px-2 py-0.5 bg-blue-500/20 hover:bg-blue-500/30 border border-blue-500/40 rounded-full text-xs transition-colors"
                      >
                        <span className="text-blue-300">{param.name}</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteParameter(idx)
                          }}
                          className="w-3 h-3 flex items-center justify-center rounded-full hover:bg-red-500/50 text-blue-200 hover:text-red-200 transition-colors"
                          title="Delete parameter"
                        >
                          ×
                        </button>
                      </button>
                    ))}
                  </div>
                )}
                <button
                  onClick={addParameter}
                  className="px-3 py-1.5 text-sm bg-blue-500 hover:bg-blue-600 text-white rounded transition-colors"
                >
                  + Parameter
                </button>
              </div>

              {/* Add Step Button */}
              <button
                onClick={addStep}
                className="px-3 py-1.5 text-sm bg-green-500 hover:bg-green-600 text-white rounded transition-colors"
              >
                + Step
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto p-6">
        {enabled ? (
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Steps Section */}
            {workflowData.steps.length > 0 && (
              <div className="space-y-4">
                <h4 className="text-sm font-semibold text-white/60 uppercase tracking-wide">Workflow Steps</h4>
                {workflowData.steps.map((step, stepIdx) => (
                  <div
                    key={stepIdx}
                    className="bg-[#2a2a2a] border border-white/10 rounded-lg overflow-hidden"
                  >
                    {/* Step Header */}
                    <div className="bg-green-500/20 border-b border-green-500/30 p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-xl">🔄</span>
                            <span className="font-semibold text-white">Step {step.step_number}</span>
                          </div>
                          <p className="text-sm text-white/80">{step.description}</p>
                        </div>
                        <div className="flex gap-2 ml-4">
                          <button
                            onClick={() => setStepModal({ open: true, data: step, index: stepIdx })}
                            className="px-2 py-1 text-xs bg-white/10 hover:bg-white/20 text-white rounded transition-colors"
                          >
                            ✏️ Edit
                          </button>
                          <button
                            onClick={() => deleteStep(stepIdx)}
                            className="px-2 py-1 text-xs bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded transition-colors"
                          >
                            🗑️ Delete
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Actions List */}
                    <div className="p-4 space-y-2">
                      {step.actions.map((action, actionIdx) => {
                        const icon = ACTION_ICONS[action.name] || '⚡'
                        return (
                          <div
                            key={actionIdx}
                            className="bg-purple-500/10 border border-purple-500/30 rounded p-3"
                          >
                            <div className="flex items-start justify-between">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <span className="text-lg">{icon}</span>
                                  <span className="font-semibold text-white capitalize">{action.name}</span>
                                  <span className="text-xs text-white/50">Action {action.action_number}</span>
                                </div>
                                {Object.keys(action.params).length > 0 && (
                                  <div className="space-y-1 ml-7">
                                    {Object.entries(action.params).map(([key, value]) => (
                                      <div key={key} className="text-xs">
                                        <span className="text-white/60">{key}:</span>
                                        <span className="ml-2 text-white/80 font-mono">
                                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                        </span>
                                      </div>
                                    ))}
                                  </div>
                                )}
                              </div>
                              <div className="flex gap-2 ml-4">
                                <button
                                  onClick={() =>
                                    setActionModal({
                                      open: true,
                                      data: action,
                                      stepIndex: stepIdx,
                                      actionIndex: actionIdx,
                                    })
                                  }
                                  className="px-2 py-1 text-xs bg-white/10 hover:bg-white/20 text-white rounded transition-colors"
                                >
                                  ✏️
                                </button>
                                <button
                                  onClick={() => deleteAction(stepIdx, actionIdx)}
                                  className="px-2 py-1 text-xs bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded transition-colors"
                                >
                                  🗑️
                                </button>
                              </div>
                            </div>
                          </div>
                        )
                      })}

                      {/* Add Action Button */}
                      <button
                        onClick={() => setActionModal({ open: true, data: null, stepIndex: stepIdx, actionIndex: null })}
                        className="w-full py-2 border-2 border-dashed border-purple-500/30 hover:border-purple-500/50 rounded text-purple-400 hover:text-purple-300 text-sm font-medium transition-colors flex items-center justify-center gap-2"
                      >
                        <span className="text-xl">+</span>
                        Add Action
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Empty State */}
            {workflowData.steps.length === 0 && (
              <div className="text-center py-12">
                <p className="text-white/40 mb-4">No steps defined yet</p>
                <button
                  onClick={addStep}
                  className="px-4 py-2 bg-green-500 hover:bg-green-600 text-white rounded transition-colors"
                >
                  Add First Step
                </button>
              </div>
            )}
          </div>
        ) : (
          <div className="h-full flex items-center justify-center">
            <p className="text-white/50 text-lg">Enable cached workflow to start editing</p>
          </div>
        )}
      </div>

      {/* Modals */}
      {parameterModal.open && (
        <ParameterModal
          parameter={parameterModal.data}
          onSave={saveParameter}
          onClose={() => setParameterModal({ open: false, data: null, index: null })}
        />
      )}
      {stepModal.open && (
        <StepModal
          step={stepModal.data}
          onSave={saveStep}
          onClose={() => setStepModal({ open: false, data: null, index: null })}
        />
      )}
      {actionModal.open && (
        <ActionModal
          action={actionModal.data}
          stepNumber={actionModal.stepIndex !== null ? workflowData.steps[actionModal.stepIndex]?.step_number : 0}
          onSave={saveAction}
          onClose={() => setActionModal({ open: false, data: null, stepIndex: null, actionIndex: null })}
        />
      )}
    </div>
  )
}
