import { useState, useEffect } from 'react'
import './App.css'

function App() {
  const [status, setStatus] = useState({
    is_running: false,
    current_id: 0,
    total_records: 0,
    blank_count: 0,
    visual_mode: false
  })
  const [loading, setLoading] = useState(false)
  const [visualMode, setVisualMode] = useState(false)

  const fetchStatus = async () => {
    try {
      const res = await fetch('/api/status')
      const data = await res.json()
      setStatus(data)
      // Sync local visual mode state if running
      if (data.is_running) {
        setVisualMode(data.visual_mode)
      }
    } catch (error) {
      console.error("Error fetching status:", error)
    }
  }

  useEffect(() => {
    fetchStatus()
    const pollInterval = import.meta.env.VITE_POLL_INTERVAL || 5000
    const interval = setInterval(fetchStatus, pollInterval)
    return () => clearInterval(interval)
  }, [])

  const handleStart = async () => {
    setLoading(true)
    try {
      await fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ visual_mode: visualMode })
      })
      await fetchStatus()
    } catch (error) {
      console.error("Error starting:", error)
    }
    setLoading(false)
  }

  const handleStop = async () => {
    setLoading(true)
    try {
      await fetch('/api/stop', { method: 'POST' })
      await fetchStatus()
    } catch (error) {
      console.error("Error stopping:", error)
    }
    setLoading(false)
  }

  const handleDownload = () => {
    window.location.href = '/api/download'
  }

  return (
    <div className="container">
      <h1>Invoice Scraper Dashboard</h1>

      <div className="card">
        <div className="stat-grid">
          <div className="stat-item">
            <h3>Status</h3>
            <span className={`status-badge ${status.is_running ? 'running' : 'stopped'}`}>
              {status.is_running ? 'Running' : 'Stopped'}
            </span>
          </div>
          <div className="stat-item">
            <h3>Mode</h3>
            <span className="stat-value mode-value">
              {status.is_running ? (status.visual_mode ? 'Visual' : 'Fast') : 'Idle'}
            </span>
          </div>
          <div className="stat-item">
            <h3>Current Invoice ID</h3>
            <span className="stat-value">{status.current_id}</span>
          </div>
          <div className="stat-item">
            <h3>Total Records</h3>
            <span className="stat-value">{status.total_records}</span>
          </div>
          <div className="stat-item">
            <h3>Consecutive Blanks</h3>
            <span className="stat-value">{status.blank_count}</span>
          </div>
        </div>

        <div className="controls-section">
          <div className="mode-toggle">
            <label>
              <input
                type="checkbox"
                checked={visualMode}
                onChange={async (e) => {
                  const newMode = e.target.checked;
                  setVisualMode(newMode);
                  if (status.is_running) {
                    try {
                      await fetch('/api/mode', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ visual_mode: newMode })
                      });
                      await fetchStatus();
                    } catch (error) {
                      console.error("Error switching mode:", error);
                      // Revert if failed
                      setVisualMode(!newMode);
                    }
                  }
                }}
                disabled={loading}
              />
              Enable Visual Verification Mode
            </label>
          </div>

          <div className="controls">
            {!status.is_running ? (
              <button className="btn start-btn" onClick={handleStart} disabled={loading}>
                Start Scraping
              </button>
            ) : (
              <button className="btn stop-btn" onClick={handleStop} disabled={loading}>
                Stop Scraping
              </button>
            )}

            <button className="btn download-btn" onClick={handleDownload} disabled={status.total_records === 0}>
              Download Excel
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
