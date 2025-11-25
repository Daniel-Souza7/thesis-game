import React from 'react'

const ControlPanel = ({
  onSwitchProduct,
  isAnimating,
  currentProduct
}) => {
  return (
    <div className="control-panel">
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
