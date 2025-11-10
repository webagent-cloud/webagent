import { useNavigate, Link } from 'react-router-dom'
import logo from '../assets/logo.png'

interface TaskHeaderProps {
  taskId: string | number
  activeTab: 'editor' | 'runs'
}

export default function TaskHeader({ taskId, activeTab }: TaskHeaderProps) {
  const navigate = useNavigate()

  return (
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
            <span className="text-white">Task #{taskId}</span>
          </div>
        </div>

        {/* Center: Navigation */}
        <div className="flex gap-6 flex-1 justify-center">
          {activeTab === 'editor' ? (
            <span className="py-3 px-1 border-b-2 border-[#646cff] text-white font-medium">
              Editor
            </span>
          ) : (
            <button
              onClick={() => navigate(`/tasks/${taskId}`)}
              className="py-3 px-1 border-b-2 border-transparent text-white/60 hover:text-white transition-colors font-medium"
            >
              Editor
            </button>
          )}

          {activeTab === 'runs' ? (
            <span className="py-3 px-1 border-b-2 border-[#646cff] text-white font-medium">
              Runs
            </span>
          ) : (
            <button
              onClick={() => navigate(`/tasks/${taskId}/runs`)}
              className="py-3 px-1 border-b-2 border-transparent text-white/60 hover:text-white transition-colors font-medium"
            >
              Runs
            </button>
          )}
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
  )
}
