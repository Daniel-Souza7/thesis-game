import React from 'react'

const GameSelectionModal = ({ onClose, onSelectGame, currentGame }) => {
  const games = [
    // MEDIUM
    {
      id: 'upandoutcall',
      name_line1: 'UpAndOut',
      name_line2: 'Call',
      description: '1 stock, upper barrier at 130',
      difficulty: 'Medium'
    },
    {
      id: 'downandoutbskput',
      name_line1: 'DownAndOut',
      name_line2: 'BskPut',
      description: '3 stocks, lower barrier at 70',
      difficulty: 'Medium'
    },
    {
      id: 'doublebarriermaxcall',
      name_line1: 'DoubleBarrier',
      name_line2: 'MaxCall',
      description: '7 stocks, barriers at 85 and 130',
      difficulty: 'Medium'
    },
    // HARD
    {
      id: 'randomlymovingbarriercall',
      name_line1: 'RandomlyMoving',
      name_line2: 'BarrierCall',
      description: '1 stock, moving barrier at 125',
      difficulty: 'Hard'
    },
    {
      id: 'upandoutminput',
      name_line1: 'UpAndOut',
      name_line2: 'MinPut',
      description: '3 stocks, upper barrier at 120',
      difficulty: 'Hard'
    },
    {
      id: 'downandoutbest2call',
      name_line1: 'DownAndOut',
      name_line2: 'Best2Call',
      description: '7 stocks, lower barrier at 85',
      difficulty: 'Hard'
    },
    // IMPOSSIBLE
    {
      id: 'doublebarrierlookbackfloatingput',
      name_line1: 'DoubleBarrier',
      name_line2: 'LookbackFloatingPut',
      description: '1 stock, barriers at 85 and 115',
      difficulty: 'Impossible'
    },
    {
      id: 'doublebarrierrankweightedbskcall',
      name_line1: 'DoubleBarrier',
      name_line2: 'RankWeightedBskCall',
      description: '3 stocks, barriers at 80 and 125',
      difficulty: 'Impossible'
    },
    {
      id: 'doublemovingbarrierdispersioncall',
      name_line1: 'DoubleMoving',
      name_line2: 'BarrierDispersionCall',
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
                <h3 className="game-item-title">
                  <div>{game.name_line1}</div>
                  <div>{game.name_line2}</div>
                </h3>
              </div>
              <p className="game-item-description">{game.description}</p>
              {currentGame === game.id && (
                <div className="current-game-badge">CURRENT GAME</div>
              )}
              <div className="game-item-footer">
                <span className={`difficulty-badge difficulty-${game.difficulty.toLowerCase()}`}>
                  {game.difficulty}
                </span>
              </div>
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
