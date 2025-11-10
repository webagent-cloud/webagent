import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import './index.css'
import App from './App.tsx'
import TaskEdit from './pages/TaskEdit.tsx'
import TaskRuns from './pages/TaskRuns.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<App />} />
        <Route path="/tasks/:id" element={<TaskEdit />} />
        <Route path="/tasks/:id/runs" element={<TaskRuns />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
