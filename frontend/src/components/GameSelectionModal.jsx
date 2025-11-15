import React from 'react'

const GameSelectionModal = ({ onClose, onSelectGame, currentGame }) => {
  // Default to first game (upandoutcall) if no game is currently selected
  const activeGame = currentGame || 'upandoutcall'

  const games = [
    // MEDIUM
    {
      id: 'upandoutcall',
      name_line1: 'UpAndOut',
      name_line2: 'Call',
      desc_line1: '1 stock',
      desc_line2: 'upper barrier at 130',
      difficulty: 'Medium'
    },
    {
      id: 'downandoutminput',
      name_line1: 'DownAndOut',
      name_line2: 'MinPut',
      desc_line1: '3 stocks',
      desc_line2: 'lower barrier at 85',
      difficulty: 'Medium'
    },
    {
      id: 'doublebarriermaxcall',
      name_line1: 'DoubleBarrier',
      name_line2: 'MaxCall',
      desc_line1: '7 stocks',
      desc_line2: 'barriers at 85 and 130',
      difficulty: 'Medium'
    },
    // HARD
    {
      id: 'randomlymovingbarriercall',
      name_line1: 'RandomlyMoving',
      name_line2: 'BarrierCall',
      desc_line1: '1 stock',
      desc_line2: 'moving barrier at 125',
      difficulty: 'Hard'
    },
    {
      id: 'upandoutminput',
      name_line1: 'UpAndOut',
      name_line2: 'MinPut',
      desc_line1: '3 stocks',
      desc_line2: 'upper barrier at 120',
      difficulty: 'Hard'
    },
    {
      id: 'downandoutbest2call',
      name_line1: 'DownAndOut',
      name_line2: 'Best2Call',
      desc_line1: '7 stocks',
      desc_line2: 'lower barrier at 85',
      difficulty: 'Hard'
    },
    // IMPOSSIBLE
    {
      id: 'doublebarrierlookbackfloatingput',
      name_line1: 'DoubleBarrier',
      name_line2: 'LookbackFloatingPut',
      desc_line1: '1 stock',
      desc_line2: 'barriers at 85 and 115',
      difficulty: 'Impossible'
    },
    {
      id: 'doublebarrierrankweightedbskcall',
      name_line1: 'DoubleBarrier',
      name_line2: 'RankWeightedBskCall',
      desc_line1: '3 stocks',
      desc_line2: 'barriers at 80 and 125',
      difficulty: 'Impossible'
    },
    {
      id: 'doublemovingbarrierdispersioncall',
      name_line1: 'DoubleMoving',
      name_line2: 'BarrierDispersionCall',
      desc_line1: '7 stocks',
      desc_line2: 'barriers at 85 and 115',
      difficulty: 'Impossible'
    }
  ]

  const handleSelect = (gameId) => {
    onSelectGame(gameId)
    onClose()
  }

  return (
    <div className="modal-overlay" onClick={currentGame ? onClose : undefined}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2 className="modal-title">SELECT GAME</h2>
          {currentGame && <button className="modal-close" onClick={onClose}>✕</button>}
        </div>

        <div className="game-list">
          {games.map((game) => (
            <div
              key={game.id}
              className={`game-item ${activeGame === game.id ? 'active' : ''}`}
              onClick={() => handleSelect(game.id)}
            >
              <div className="game-item-header">
                <h3 className="game-item-title">
                  <div>{game.name_line1}</div>
                  <div>{game.name_line2}</div>
                </h3>
                <span className={`difficulty-badge difficulty-${game.difficulty.toLowerCase()}`}>
                  {game.difficulty}
                </span>
              </div>
              <p className="game-item-description">
                <span className="desc-stock-count">{game.desc_line1}</span>
                <br />
                <span className="desc-barrier-info">{game.desc_line2}</span>
              </p>
              {activeGame === game.id && (
                <div className="current-game-badge">CURRENT GAME</div>
              )}
            </div>
          ))}
        </div>

        {currentGame && (
          <div className="modal-footer">
            <button className="arcade-button start" onClick={onClose}>
              CANCEL
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

export default GameSelectionModal
