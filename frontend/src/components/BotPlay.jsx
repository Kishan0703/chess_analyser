export default function BotPlay({ onOpenGame }) {
  return (
    <section className="bot-play">
      <div className="section-head">
        <div>
          <p className="eyebrow">Offline practice</p>
          <h1>Play vs Bot</h1>
        </div>
      </div>
      <div className="status-line">Choose a side and difficulty to start a local Stockfish game.</div>
    </section>
  )
}
