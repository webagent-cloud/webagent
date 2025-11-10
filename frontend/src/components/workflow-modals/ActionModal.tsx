import { useState, useEffect } from 'react'

interface ActionFormData {
  name: string
  params: Record<string, any>
}

interface ActionModalProps {
  action: ActionFormData | null
  stepNumber: number
  onSave: (action: ActionFormData) => void
  onClose: () => void
}

const ACTION_TYPES = [
  { value: 'navigate', label: 'Navigate', icon: '🌐', params: ['url'] },
  { value: 'click', label: 'Click', icon: '👆', params: ['selector'] },
  { value: 'input', label: 'Input', icon: '⌨️', params: ['selector', 'text'] },
  { value: 'scroll', label: 'Scroll', icon: '📜', params: ['direction', 'amount'] },
  { value: 'wait', label: 'Wait', icon: '⏱️', params: ['seconds'] },
  { value: 'extract', label: 'Extract', icon: '📋', params: ['selector', 'attribute'] },
  { value: 'screenshot', label: 'Screenshot', icon: '📸', params: ['filename'] },
  { value: 'done', label: 'Done', icon: '✅', params: [] },
]

export default function ActionModal({ action, stepNumber, onSave, onClose }: ActionModalProps) {
  const [formData, setFormData] = useState<ActionFormData>({
    name: 'navigate',
    params: {}
  })

  useEffect(() => {
    if (action) {
      setFormData(action)
    }
  }, [action])

  const selectedActionType = ACTION_TYPES.find(a => a.value === formData.name) || ACTION_TYPES[0]

  const handleActionTypeChange = (actionType: string) => {
    const actionDef = ACTION_TYPES.find(a => a.value === actionType)
    const newParams: Record<string, any> = {}

    // Initialize params with empty values
    actionDef?.params.forEach(param => {
      newParams[param] = formData.params[param] || ''
    })

    setFormData({
      name: actionType,
      params: newParams
    })
  }

  const handleParamChange = (paramName: string, value: string) => {
    setFormData({
      ...formData,
      params: {
        ...formData.params,
        [paramName]: value
      }
    })
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSave(formData)
    onClose()
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-900 rounded-lg shadow-xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 sticky top-0 bg-white dark:bg-gray-900">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {action ? 'Edit Action' : `Add Action to Step ${stepNumber}`}
          </h3>
        </div>

        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              Action Type *
            </label>
            <select
              required
              value={formData.name}
              onChange={(e) => handleActionTypeChange(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
            >
              {ACTION_TYPES.map(action => (
                <option key={action.value} value={action.value}>
                  {action.icon} {action.label}
                </option>
              ))}
            </select>
          </div>

          {selectedActionType.params.length > 0 && (
            <div className="space-y-3 pt-2">
              <p className="text-sm font-medium text-gray-700 dark:text-gray-300">Parameters</p>
              {selectedActionType.params.map(param => (
                <div key={param}>
                  <label className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1 capitalize">
                    {param} *
                  </label>
                  {param === 'text' || param === 'selector' ? (
                    <textarea
                      required
                      value={formData.params[param] || ''}
                      onChange={(e) => handleParamChange(param, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono"
                      rows={2}
                      placeholder={`Enter ${param}...`}
                    />
                  ) : (
                    <input
                      type="text"
                      required
                      value={formData.params[param] || ''}
                      onChange={(e) => handleParamChange(param, e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder={`Enter ${param}...`}
                    />
                  )}
                </div>
              ))}
              <div className="text-xs text-gray-500 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 p-2 rounded">
                💡 Tip: Use <code className="bg-gray-200 dark:bg-gray-700 px-1 rounded">{'{{ paramName }}'}</code> to reference workflow parameters
              </div>
            </div>
          )}

          <div className="flex gap-3 pt-4 sticky bottom-0 bg-white dark:bg-gray-900 pb-2">
            <button
              type="submit"
              className="flex-1 px-4 py-2 bg-purple-500 hover:bg-purple-600 text-white rounded-md transition-colors"
            >
              {action ? 'Update' : 'Add'} Action
            </button>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 text-gray-900 dark:text-white rounded-md transition-colors"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
