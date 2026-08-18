import { useEffect, useState } from 'react'
import { api } from '../api.js'

export default function Settings() {
  const [cfg, setCfg] = useState(null)
  const [stockfishStatus, setStockfishStatus] = useState(null)
  const [status, setStatus] = useState('')

  const refreshStockfishStatus = async () => {
    const onboarding = await api.onboarding()
    setStockfishStatus(onboarding)
  }

  useEffect(() => {
    Promise.all([api.settings(), api.onboarding()])
      .then(([loaded, onboarding]) => {
        setCfg(loaded)
        setStockfishStatus(onboarding)
      })
      .catch((e) => setStatus(e.message))
  }, [])

  if (!cfg) return <div className="status-line">{status || 'Loading…'}</div>

  const isOllama = (cfg.coach_provider || 'ollama') === 'ollama'
  const isClaude = cfg.coach_provider === 'claude'
  const isGemini = cfg.coach_provider === 'gemini'

  const save = async () => {
    setStatus('Saving…')
    try {
      const updates = {
        chesscom_username: cfg.chesscom_username,
        coach_provider: cfg.coach_provider,
        ollama_url: cfg.ollama_url,
        ollama_model: cfg.ollama_model,
        claude_model: cfg.claude_model,
        gemini_model: cfg.gemini_model,
        engine_movetime_ms: Number(cfg.engine_movetime_ms),
        engine_threads: Number(cfg.engine_threads),
        stockfish_path: cfg.stockfish_path,
      }
      const saved = await api.saveSettings(updates)
      setCfg(saved)
      try {
        await refreshStockfishStatus()
      } catch (e) {
        setStatus(`Saved. Readiness check failed: ${e.message}`)
        return
      }
      setStatus('Saved.')
    } catch (e) {
      setStatus(`Save failed: ${e.message}`)
    }
  }

  return (
    <div className="settings-form">
      <h2>Settings</h2>

      <label>
        chess.com username
        <input
          value={cfg.chesscom_username || ''}
          onChange={(e) => setCfg({ ...cfg, chesscom_username: e.target.value })}
        />
      </label>

      <label>
        Coach provider
        <select
          value={cfg.coach_provider || 'ollama'}
          onChange={(e) => setCfg({ ...cfg, coach_provider: e.target.value })}
        >
          <option value="ollama">Ollama — free local LLM (recommended)</option>
          <option value="claude">Claude API — best quality (costs per game)</option>
          <option value="gemini">Gemini API — Google AI Studio key</option>
        </select>
      </label>

      {isOllama && (
        <>
          <div className="card" style={{ padding: '10px 14px', fontSize: 13, lineHeight: 1.6 }}>
            <strong>Ollama setup (one time):</strong>
            <ol style={{ margin: '6px 0 0', paddingLeft: 18 }}>
              <li>Install from <strong>ollama.com</strong></li>
              <li>Open a terminal and run: <code>ollama pull qwen3:8b</code></li>
              <li>Ollama runs automatically in the background after install.</li>
            </ol>
          </div>
          <label>
            Ollama URL
            <input
              value={cfg.ollama_url || 'http://localhost:11434'}
              onChange={(e) => setCfg({ ...cfg, ollama_url: e.target.value })}
            />
          </label>
          <label>
            Model
            <input
              value={cfg.ollama_model || 'qwen3:8b'}
              onChange={(e) => setCfg({ ...cfg, ollama_model: e.target.value })}
              placeholder="qwen3:8b"
            />
            <span className="status-line">
              qwen3:8b recommended (best grounding) · also works: llama3.1:8b, gemma2:9b, mistral
            </span>
          </label>
        </>
      )}

      {isClaude && (
        <>
          <p className="status-line">
            Anthropic API key {cfg.anthropic_api_key ? 'is set through the environment.' : 'is not set. Add ANTHROPIC_API_KEY to .env.'}
          </p>
          <label>
            Claude model
            <select
              value={cfg.claude_model}
              onChange={(e) => setCfg({ ...cfg, claude_model: e.target.value })}
            >
              <option value="claude-sonnet-4-6">Sonnet 4.6 (~3¢/game)</option>
              <option value="claude-haiku-4-5-20251001">Haiku 4.5 (~0.5¢/game)</option>
              <option value="claude-opus-4-8">Opus 4.8 (~15¢/game)</option>
            </select>
          </label>
        </>
      )}

      {isGemini && (
        <>
          <p className="status-line">
            Gemini API key {cfg.gemini_api_key ? 'is set through the environment.' : 'is not set. Add GEMINI_API_KEY to .env.'}
          </p>
          <label>
            Gemini model
            <input
              value={cfg.gemini_model || 'gemini-2.5-flash'}
              onChange={(e) => setCfg({ ...cfg, gemini_model: e.target.value })}
              placeholder="gemini-2.5-flash"
            />
            <span className="status-line">
              Use a Gemini model that supports text generation and JSON output.
            </span>
          </label>
        </>
      )}

      <hr style={{ border: 'none', borderTop: '1px solid var(--border)', margin: '4px 0' }} />

      <label>
        Engine time per move (ms) — higher = more accurate, slower
        <input
          type="number" min="50" max="2000" step="50"
          value={cfg.engine_movetime_ms}
          onChange={(e) => setCfg({ ...cfg, engine_movetime_ms: e.target.value })}
        />
      </label>
      <label>
        Engine threads
        <input
          type="number" min="1" max="16"
          value={cfg.engine_threads}
          onChange={(e) => setCfg({ ...cfg, engine_threads: e.target.value })}
        />
      </label>
      <label>
        Stockfish path
        <input
          value={cfg.stockfish_path || ''}
          onChange={(e) => setCfg({ ...cfg, stockfish_path: e.target.value })}
          placeholder="engines/stockfish.exe"
        />
        <span className={`status-line ${stockfishStatus && !stockfishStatus.stockfish_found ? 'error' : ''}`}>
          {stockfishStatus
            ? stockfishStatus.stockfish_found
              ? `Ready: ${stockfishStatus.stockfish_path}`
              : stockfishStatus.stockfish_error
            : 'Checking Stockfish readiness…'}
        </span>
      </label>

      <div>
        <button className="primary" onClick={save}>Save</button>
        <span className="status-line" style={{ marginLeft: 10 }}>{status}</span>
      </div>
    </div>
  )
}
