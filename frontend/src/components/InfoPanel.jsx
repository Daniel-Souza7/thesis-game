import React from 'react'

const InfoPanel = ({
  currentStep,
  nbDates,
  currentPayoff,
  gameInfo,
  path,
  isBarrierHit,
  machineDecision,
  machineCurrentPayoff,
  machineDecisionFlash,
  barrierPathUpper,
  barrierPathLower
}) => {
  // Calculate current prices
  const currentPrices = path.map(stock => stock[currentStep])
  const minPrice = Math.min(...currentPrices)
  const maxPrice = Math.max(...currentPrices)

  // Get payoff formula based on game type
  const getPayoffFormula = () => {
    const name = gameInfo.name

    // MEDIUM
    if (name === 'UpAndOutCall') {
      return (
        <span>
          (S(t) - K)<sup>+</sup>
          <br />
          <span style={{ fontSize: '7px' }}>If max<sub>τ≤t</sub> S(τ) {'<'} {gameInfo.barrier}</span>
        </span>
      )
    } else if (name === 'DownAndOutMinPut') {
      return (
        <span>
          (K - min<sub>i</sub> S<sub>i</sub>(t))<sup>+</sup>
          <br />
          <span style={{ fontSize: '7px' }}>If min<sub>τ≤t,i</sub> S<sub>i</sub>(τ) {'>'} {gameInfo.barrier}</span>
        </span>
      )
    } else if (name === 'DoubleBarrierMaxCall') {
      return (
        <span>
          (max<sub>i</sub> S<sub>i</sub>(t) - K)<sup>+</sup>
          <br />
          <span style={{ fontSize: '7px' }}>If {gameInfo.barrier_down} {'<'} S<sub>i</sub> {'<'} {gameInfo.barrier_up}</span>
        </span>
      )
    }
    // HARD
    else if (name === 'RandomlyMovingBarrierCall' || name.includes('StepBarrier')) {
      return (
        <span>
          (S(t) - K)<sup>+</sup>
          <br />
          <span style={{ fontSize: '7px' }}>If S(τ) {'<'} B(τ) ∀τ≤t</span>
        </span>
      )
    } else if (name === 'UpAndOutMinPut') {
      return (
        <span>
          (K - min<sub>i</sub> S<sub>i</sub>(t))<sup>+</sup>
          <br />
          <span style={{ fontSize: '7px' }}>If max<sub>τ≤t,i</sub> S<sub>i</sub>(τ) {'<'} {gameInfo.barrier}</span>
        </span>
      )
    } else if (name === 'DownAndOutBest2Call') {
      return (
        <span>
          (avg(top 2 stocks) - K)<sup>+</sup>
          <br />
          <span style={{ fontSize: '7px' }}>If min<sub>τ≤t,i</sub> S<sub>i</sub>(τ) {'>'} {gameInfo.barrier}</span>
        </span>
      )
    }
    // IMPOSSIBLE
    else if (name.includes('Lookback')) {
      return (
        <span>
          (max<sub>τ≤t</sub> S(τ) - S(t))<sup>+</sup>
          <br />
          <span style={{ fontSize: '7px' }}>If {gameInfo.barrier_down} {'<'} S(τ) {'<'} {gameInfo.barrier_up}</span>
        </span>
      )
    } else if (name.includes('RankWeighted')) {
      return (
        <span>
          (0.15×S<sub>1st</sub> + 0.50×S<sub>2nd</sub> + 0.35×S<sub>3rd</sub> - K)<sup>+</sup>
          <br />
          <span style={{ fontSize: '7px' }}>If {gameInfo.barrier_down} {'<'} S<sub>i</sub> {'<'} {gameInfo.barrier_up}</span>
        </span>
      )
    } else if (name.includes('Dispersion')) {
      return (
        <span>
          (std(S<sub>1</sub>,...,S<sub>7</sub>) - K)<sup>+</sup>
          <br />
          <span style={{ fontSize: '7px' }}>If B<sub>L</sub>(τ) {'<'} avg(S(τ)) {'<'} B<sub>U</sub>(τ) ∀τ</span>
        </span>
      )
    }

    return 'Payoff: ...'
  }

  // Get barrier display text (with moving barrier support)
  const getBarrierText = () => {
    // For moving barriers, use the current barrier values
    if (barrierPathUpper && !barrierPathLower) {
      // Single upper moving barrier (RandomlyMovingBarrierCall)
      const currentBarrier = barrierPathUpper[currentStep]
      return `Upper Barrier: ${currentBarrier.toFixed(2)}`
    } else if (barrierPathUpper && barrierPathLower) {
      // Double moving barriers (DoubleMovingBarrierDispersionCall)
      const currentBarrierLower = barrierPathLower[currentStep]
      const currentBarrierUpper = barrierPathUpper[currentStep]
      return `Barriers: ${currentBarrierLower.toFixed(2)} / ${currentBarrierUpper.toFixed(2)}`
    }
    // Static barriers
    else if (gameInfo.barrier_type === 'up') {
      return `Upper Barrier: ${gameInfo.barrier}`
    } else if (gameInfo.barrier_type === 'down') {
      return `Lower Barrier: ${gameInfo.barrier}`
    } else if (gameInfo.barrier_type === 'double') {
      return `Barriers: ${gameInfo.barrier_down} / ${gameInfo.barrier_up}`
    }
    return ''
  }

  return (
    <div className="info-panel">
      <div className="info-item">
        <span className="info-label">TIME STEP</span>
        <div className="info-value large">{currentStep} / {nbDates}</div>
      </div>

      <div className="info-item">
        <span className="info-label">YOUR PAYOFF</span>
        <div className={`info-value large ${isBarrierHit ? 'barrier-warning' : ''}`}>
          ${currentPayoff?.toFixed(2) || '0.00'}
        </div>
      </div>

      {isBarrierHit && (
        <div className="info-item">
          <span className="info-label barrier-warning">⚠ BARRIER HIT ⚠</span>
        </div>
      )}

      {getBarrierText() && (
        <div className="info-item">
          <span className="info-label">BARRIERS</span>
          <div className="info-value" style={{ fontSize: '12px', color: '#ff0000' }}>
            {getBarrierText()}
          </div>
        </div>
      )}

      <div className="info-item">
        <span className="info-label">STRIKE PRICE</span>
        <div className="info-value" style={{ fontSize: '14px', color: '#ffff00' }}>
          K = ${gameInfo.strike || 100}
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

      <div className={`machine-indicator ${machineDecisionFlash ? 'flash' : ''}`}>
        <div className="machine-label">MACHINE DECISION</div>
        <div className={`machine-decision ${machineDecision.toLowerCase()}`}>
          {machineDecision}
        </div>
        <div className="machine-payoff">
          ${machineCurrentPayoff?.toFixed(2) || '0.00'}
        </div>
      </div>

      <div className="payoff-formula">
        <div className="formula-label">PAYOFF FORMULA</div>
        <div className="formula-text">
          {getPayoffFormula()}
        </div>
      </div>
    </div>
  )
}

export default InfoPanel
