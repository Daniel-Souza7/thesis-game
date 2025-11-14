import React from 'react'

const GameSelectionModal = ({ onClose, onSelectGame, currentGame }) => {
  const games = [
    // MEDIUM
    {
      id: 'upandoutcall',
      name: 'UpAndOutCall',
      description: '1 stock, upper barrier at 130',
      difficulty: 'Medium'
    },
    {
      id: 'downandoutbskput',
      name: 'DownAndOutBskPut',
      description: '3 stocks, lower barrier at 70',
      difficulty: 'Medium'
    },
    {
      id: 'doublebarriermaxcall',
      name: 'DoubleBarrierMaxCall',
      description: '7 stocks, barriers at 85 and 130',
      difficulty: 'Medium'
    },
    // HARD
    {
      id: 'randomlymovingbarriercall',
      name: 'RandomlyMovingBarrierCall',
      description: '1 stock, moving barrier at 125',
      difficulty: 'Hard'
    },
    {
      id: 'upandoutminput',
      name: 'UpAndOutMinPut',
      description: '3 stocks, upper barrier at 120',
      difficulty: 'Hard'
    },
    {
      id: 'downandoutbest2call',
      name: 'DownAndOutBest2Call',
      description: '7 stocks, lower barrier at 85',
      difficulty: 'Hard'
    },
    // IMPOSSIBLE
    {
      id: 'doublebarrierlookbackfloatingput',
      name: 'DoubleBarrierLookbackFloatingPut',
      description: '1 stock, barriers at 85 and 115',
      difficulty: 'Impossible'
    },
    {
      id: 'doublebarrierrankweightedbskcall',
      name: 'DoubleBarrierRankWeightedBskCall',
      description: '3 stocks, barriers at 80 and 125',
      difficulty: 'Impossible'
    },
    {
      id: 'doublemovingbarrierdispersioncall',
      name: 'DoubleMovingBarrierDispersionCall',
      description: '7 stocks, barriers at 85 and 115',
      difficulty: 'Impossible'
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
