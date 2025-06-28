import React, { useState, useEffect } from 'react'
import { Calendar, Camera, Users, MapPin, Tag, Clock, BarChart } from 'lucide-react'
import { useSessionStore } from '../stores/sessionStore'
import './SessionPanel.css'

export const SessionPanel: React.FC = () => {
  const { 
    sessions, 
    currentSession, 
    presets,
    loadSessions, 
    createSession, 
    setCurrentSession,
    loadPresets 
  } = useSessionStore()
  
  const [showNewSession, setShowNewSession] = useState(false)
  const [newSession, setNewSession] = useState({
    name: '',
    type: 'custom' as const,
    clientName: '',
    location: '',
    description: ''
  })

  useEffect(() => {
    loadSessions()
    loadPresets()
  }, [])

  const handleCreateSession = async () => {
    if (!newSession.name) return
    
    try {
      await createSession({
        ...newSession,
        date: new Date().toISOString(),
        imageCount: 0,
        processedCount: 0,
        status: 'active',
        tags: [],
        averageQualityScore: 0,
        processingTimeTotal: 0
      })
      
      setShowNewSession(false)
      setNewSession({
        name: '',
        type: 'custom',
        clientName: '',
        location: '',
        description: ''
      })
    } catch (error) {
      console.error('Failed to create session:', error)
    }
  }

  const getSessionTypeIcon = (type: string) => {
    switch (type) {
      case 'wedding':
        return '💒'
      case 'portrait':
        return '👤'
      case 'sports':
        return '⚽'
      case 'event':
        return '🎉'
      case 'product':
        return '📦'
      case 'landscape':
        return '🏞️'
      default:
        return '📷'
    }
  }

  return (
    <div className="session-panel">
      <div className="session-header">
        <h2>Photo Sessions</h2>
        <button 
          className="new-session-btn"
          onClick={() => setShowNewSession(!showNewSession)}
        >
          + New Session
        </button>
      </div>

      {showNewSession && (
        <div className="new-session-form">
          <input
            type="text"
            placeholder="Session Name"
            value={newSession.name}
            onChange={(e) => setNewSession({ ...newSession, name: e.target.value })}
            className="session-input"
          />
          
          <select 
            value={newSession.type}
            onChange={(e) => setNewSession({ ...newSession, type: e.target.value as any })}
            className="session-select"
          >
            <option value="custom">Custom</option>
            <option value="wedding">Wedding</option>
            <option value="portrait">Portrait</option>
            <option value="sports">Sports</option>
            <option value="event">Event</option>
            <option value="product">Product</option>
            <option value="landscape">Landscape</option>
          </select>

          <input
            type="text"
            placeholder="Client Name"
            value={newSession.clientName}
            onChange={(e) => setNewSession({ ...newSession, clientName: e.target.value })}
            className="session-input"
          />

          <input
            type="text"
            placeholder="Location"
            value={newSession.location}
            onChange={(e) => setNewSession({ ...newSession, location: e.target.value })}
            className="session-input"
          />

          <textarea
            placeholder="Description"
            value={newSession.description}
            onChange={(e) => setNewSession({ ...newSession, description: e.target.value })}
            className="session-textarea"
          />

          <div className="form-actions">
            <button onClick={handleCreateSession} className="create-btn">
              Create Session
            </button>
            <button onClick={() => setShowNewSession(false)} className="cancel-btn">
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="sessions-list">
        {sessions.map((session) => (
          <div 
            key={session.id}
            className={`session-item ${currentSession?.id === session.id ? 'active' : ''}`}
            onClick={() => setCurrentSession(session)}
          >
            <div className="session-item-header">
              <span className="session-icon">{getSessionTypeIcon(session.type)}</span>
              <div className="session-info">
                <h3>{session.name}</h3>
                <div className="session-meta">
                  {session.clientName && (
                    <span><Users size={14} /> {session.clientName}</span>
                  )}
                  {session.location && (
                    <span><MapPin size={14} /> {session.location}</span>
                  )}
                  <span><Calendar size={14} /> {new Date(session.date).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
            
            <div className="session-stats">
              <div className="stat">
                <Camera size={16} />
                <span>{session.processedCount} / {session.imageCount}</span>
              </div>
              {session.averageQualityScore > 0 && (
                <div className="stat">
                  <BarChart size={16} />
                  <span>{session.averageQualityScore.toFixed(1)}</span>
                </div>
              )}
              {session.processingTimeTotal > 0 && (
                <div className="stat">
                  <Clock size={16} />
                  <span>{Math.round(session.processingTimeTotal / 60)}m</span>
                </div>
              )}
            </div>

            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ 
                  width: `${session.imageCount > 0 ? (session.processedCount / session.imageCount * 100) : 0}%` 
                }}
              />
            </div>
          </div>
        ))}
      </div>

      {currentSession && (
        <div className="current-session-details">
          <h3>Current Session</h3>
          <div className="session-detail-info">
            <p><strong>Type:</strong> {currentSession.type}</p>
            <p><strong>Status:</strong> {currentSession.status}</p>
            {currentSession.description && (
              <p><strong>Description:</strong> {currentSession.description}</p>
            )}
          </div>
        </div>
      )}

      {presets.length > 0 && (
        <div className="presets-section">
          <h3>Processing Presets</h3>
          <div className="presets-list">
            {presets.map((preset) => (
              <div key={preset.id} className="preset-item">
                <span className="preset-name">{preset.name}</span>
                <div className="preset-tags">
                  {preset.tags.map((tag) => (
                    <span key={tag} className="preset-tag">
                      <Tag size={12} /> {tag}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}