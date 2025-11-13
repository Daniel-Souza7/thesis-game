import React from 'react'

const InfoPanel = ({ currentStep, nbDates, currentPayoff, gameInfo, path, isBarrierHit, machineDecision }) => {
  // Calculate current prices
  const currentPrices = path.map(stock => stock[currentStep])
  const minPrice = Math.min(...currentPrices)
  const maxPrice = Math.max(...currentPrices)

  return (
    <div className="info-panel">
      <div className="info-item">
        <span className="info-label">TIME STEP</span>
        <div className="info-value large">{currentStep} / {nbDates}</div>
      </div>

      <div className="info-item">
        <span className="info-label">CURRENT PAYOFF</span>
        <div className={`info-value large ${isBarrierHit ? 'barrier-warning' : ''}`}>
          ${currentPayoff?.toFixed(2) || '0.00'}
        </div>
      </div>

      {isBarrierHit && (
        <div className="info-item">
          <span className="info-label barrier-warning">⚠ BARRIER HIT ⚠</span>
        </div>
      )}

      <div className="info-item">
        <span className="info-label">GAME TYPE</span>
        <div className="info-value" style={{ fontSize: '10px' }}>
          {gameInfo.name}
        </div>
      </div>

      <div className="info-item">
        <span className="info-label">CURRENT PRICES</span>
        {currentPrices.map((price, idx) => (
          <div key={idx} className="info-value" style={{ fontSize: '12px' }}>
            Stock {idx + 1}: ${price.toFixed(2)}
          </div>
        ))}
      </div>

      {gameInfo.nb_stocks > 1 && (
        <div className="info-item">
          <span className="info-label">MIN / MAX</span>
          <div className="info-value" style={{ fontSize: '12px' }}>
            ${minPrice.toFixed(2)} / ${maxPrice.toFixed(2)}
          </div>
        </div>
      )}

      <div className="machine-indicator">
        <div className="machine-label">MACHINE DECISION</div>
        <div className={`machine-decision ${machineDecision.toLowerCase()}`}>
          {machineDecision}
        </div>
      </div>
    </div>
  )
}

export default InfoPanel
