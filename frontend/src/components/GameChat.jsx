import { useEffect, useRef, useState } from 'react'
import { api } from '../api.js'

export default function GameChat({ gameId, ply, analyzed, currentMove }) {
  const [messages, setMessages] = useState([])
  const [question, setQuestion] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const endRef = useRef(null)

  useEffect(() => {
    endRef.current?.scrollIntoView({ block: 'nearest' })
  }, [messages, busy])

  const ask = async (e) => {
    e.preventDefault()
    const text = question.trim()
    if (!text || busy || !analyzed) return

    const history = messages.slice(-8)
    const userMessage = { role: 'user', content: text }
    setMessages((prev) => [...prev, userMessage])
    setQuestion('')
    setBusy(true)
    setError('')
    try {
      const result = await api.chat(gameId, text, ply, history)
      setMessages((prev) => [...prev, { role: 'assistant', content: result.answer }])
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  if (!analyzed) return null

  return (
    <div className="card game-chat">
      <div className="game-chat-head">
        <div>
          <h3>Ask about this game</h3>
          <div className="status-line">
            {ply === 0 ? 'Using the starting position' : `Using position after ${currentMove?.san || `ply ${ply}`}`}
          </div>
        </div>
      </div>

      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-empty">
            Ask about plans, best moves, why a move was bad, tactics, or what to play next.
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-message ${m.role}`}>
            {m.content}
          </div>
        ))}
        {busy && <div className="chat-message assistant thinking">Analyzing...</div>}
        <div ref={endRef} />
      </div>

      {error && <div className="error">{error}</div>}

      <form className="chat-form" onSubmit={ask}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask: why was this move bad?"
          disabled={busy}
        />
        <button className="primary" disabled={busy || !question.trim()}>
          Ask
        </button>
      </form>
    </div>
  )
}
