import React from 'react'

const ControlPanel = ({
  onHold,
  onExercise,
  onSwitchProduct,
  isPlayerTurn,
  isAnimating,
  currentProduct
}) => {
  return (
    <div className="control-panel">
      <div className="button-group">
        <button
          className="arcade-button hold"
          onClick={onHold}
          disabled={!isPlayerTurn}
        >
          HOLD
        </button>
        <button
          className="arcade-button exercise"
          onClick={onExercise}
          disabled={!isPlayerTurn}
        >
          EXERCISE
        </button>
      </div>

      {!isPlayerTurn && (
        <div style={{ color: '#ffff00', fontSize: '12px', marginTop: '10px' }}>
          {isAnimating ? 'FAST FORWARD...' : 'WATCH THE PATH...'}
        </div>
      )}

      <button
        className="arcade-button switch"
        onClick={onSwitchProduct}
        disabled={isAnimating}
      >
        SWITCH GAME
      </button>

      <div style={{ color: '#00ffff', fontSize: '8px', marginTop: '20px', lineHeight: '1.5' }}>
        {currentProduct}
      </div>
    </div>
  )
}

export default ControlPanel
