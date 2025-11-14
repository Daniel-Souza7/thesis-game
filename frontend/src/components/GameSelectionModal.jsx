import React from 'react'

const GameSelectionModal = ({ onClose, onSelectGame, currentGame }) => {
  const games = [
    {
      id: 'upandout',
      name: 'Up-and-Out Min Put',
      description: '3 stocks, upper barrier at 110',
      difficulty: 'Medium'
    },
    {
      id: 'dko',
      name: 'Double Knock-Out Lookback Put',
      description: '1 stock, barriers at 90 and 110',
      difficulty: 'Hard'
    }
  ]

  const handleSelect = (gameId) => {
    onSelectGame(gameId)
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">SELECT GAME</h2>
          <button className="modal-close" onClick={onClose}>✕</button>
        </div>

        <div className="game-list">
          {games.map((game) => (
            <div
              key={game.id}
              className={`game-item ${currentGame === game.id ? 'active' : ''}`}
              onClick={() => handleSelect(game.id)}
            >
              <div className="game-item-header">
                <h3 className="game-item-title">{game.name}</h3>
                <span className={`difficulty-badge difficulty-${game.difficulty.toLowerCase()}`}>
                  {game.difficulty}
                </span>
              </div>
              <p className="game-item-description">{game.description}</p>
              {currentGame === game.id && (
                <div className="current-game-badge">CURRENT GAME</div>
              )}
            </div>
          ))}
        </div>

        <div className="modal-footer">
          <button className="arcade-button start" onClick={onClose}>
            CANCEL
          </button>
        </div>
      </div>
    </div>
  )
}

export default GameSelectionModal
