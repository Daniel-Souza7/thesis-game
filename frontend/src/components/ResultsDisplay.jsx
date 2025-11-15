import React from 'react'

const ResultsDisplay = ({
  playerPayoff,
  machinePayoff,
  playerExerciseDate,
  machineExerciseDate,
  gameInfo,
  onPlayAgain,
  onSwitchProduct
}) => {
  const playerWins = playerPayoff > machinePayoff
  const tie = playerPayoff === machinePayoff
  const machineWins = machinePayoff > playerPayoff

  const getWinnerText = () => {
    if (tie) return 'TIE GAME!'
    if (playerWins) return 'YOU WIN!'
    return 'MACHINE WINS!'
  }

  const getWinnerClass = () => {
    if (tie) return 'tie'
    if (playerWins) return 'player'
    return 'machine'
  }

  // Check if barrier was hit (payoff = 0 typically means barrier hit)
  const playerHitBarrier = playerPayoff === 0
  const machineHitBarrier = machinePayoff === 0

  // If both hit barrier, they hit it at the same step (the player's exercise date)
  const machineBarrierStep = (machineHitBarrier && playerHitBarrier) ? playerExerciseDate : machineExerciseDate

  return (
    <div className="results-screen">
      <div className="results-title">GAME OVER</div>

      <div className={`winner-announcement ${getWinnerClass()}`}>
        {getWinnerText()}
      </div>

      <div className="score-comparison">
        <div className="score-box player">
          <div className="score-title">YOUR SCORE</div>
          <div className="score-value">${playerPayoff?.toFixed(2) || '0.00'}</div>
          <div className="score-title" style={{ marginTop: '10px', fontSize: '8px' }}>
            {playerHitBarrier ? `Hit barrier at step ${playerExerciseDate}` : `Exercised at step ${playerExerciseDate}`}
          </div>
        </div>

        <div className="score-box machine">
          <div className="score-title">MACHINE SCORE</div>
          <div className="score-value" style={{ color: '#ff00ff', textShadow: '0 0 10px #ff00ff' }}>
            ${machinePayoff?.toFixed(2) || '0.00'}
          </div>
          <div className="score-title" style={{ marginTop: '10px', fontSize: '8px' }}>
            {machineHitBarrier ? `Hit barrier at step ${machineBarrierStep}` : `Exercised at step ${machineExerciseDate}`}
          </div>
        </div>
      </div>

      <div style={{ marginBottom: '20px', color: '#00ffff', fontSize: '10px' }}>
        {playerWins && 'Congratulations! You beat the optimal stopping algorithm!'}
        {tie && 'Perfect match! You played optimally!'}
        {machineWins && 'The algorithm found a better strategy. Try again!'}
      </div>

      <div className="button-group">
        <button className="arcade-button switch" onClick={onPlayAgain}>
          PLAY AGAIN
        </button>
        <button className="arcade-button switch" onClick={onSwitchProduct}>
          SWITCH GAME
        </button>
      </div>
    </div>
  )
}

export default ResultsDisplay
