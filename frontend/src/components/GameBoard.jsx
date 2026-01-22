import React, { useState, useEffect, useRef } from 'react'
import StockChart from './StockChart'
import InfoPanel from './InfoPanel'
import ControlPanel from './ControlPanel'
import ResultsDisplay from './ResultsDisplay'
import GameSelectionModal from './GameSelectionModal'

const GameBoard = ({ gameData, onGameComplete, onSwitchProduct, onPlayAgain, gameState, setGameState }) => {
  const [currentStep, setCurrentStep] = useState(0)
  const [playerDecision, setPlayerDecision] = useState(null) // null, 'hold', 'exercise'
  const [playerExerciseDate, setPlayerExerciseDate] = useState(null)
  const [playerPayoff, setPlayerPayoff] = useState(null)
  const [machineExerciseDate, setMachineExerciseDate] = useState(gameData.machine_exercise_date)
  const [machinePayoff, setMachinePayoff] = useState(null)
  const [isAnimating, setIsAnimating] = useState(false)
  const [showMachineDecision, setShowMachineDecision] = useState(false) // NEW: control when to show machine decision
  const [machineDecisionFlash, setMachineDecisionFlash] = useState(false) // NEW: flash effect
  const [showGameSelection, setShowGameSelection] = useState(false) // NEW: game selection modal
  const [revealedUpToStep, setRevealedUpToStep] = useState(0) // NEW: track which step machine marker can show

  const animationRef = useRef(null)

  const { path, payoffs_timeline, game_info, machine_decisions, barrier_path_upper, barrier_path_lower } = gameData
  const nb_dates = game_info.nb_dates

  // Check if barrier is hit at current step
  const isBarrierHit = () => {
    if (!game_info.barrier_type) return false

    const currentPrices = path.map(stock => stock[currentStep])

    if (game_info.barrier_type === 'up') {
      return currentPrices.some(price => price >= game_info.barrier)
    } else if (game_info.barrier_type === 'down') {
      // Down-and-out: barrier hit when ANY stock goes at or below barrier
      const minPrice = Math.min(...currentPrices)
      return minPrice <= game_info.barrier
    } else if (game_info.barrier_type === 'double') {
      // Check if this is a moving barrier game with basket average check (dispersion)
      const isDispersion = game_info.name === 'DoubleMovingBarrierDispersionCall'

      if (isDispersion && barrier_path_upper && barrier_path_lower) {
        // Dispersion call: check BASKET AVERAGE against MOVING barriers
        const basketAvg = currentPrices.reduce((a, b) => a + b, 0) / currentPrices.length
        const upperBarrier = barrier_path_upper[currentStep]
        const lowerBarrier = barrier_path_lower[currentStep]
        return basketAvg >= upperBarrier || basketAvg <= lowerBarrier
      } else {
        // Standard double barrier: check individual stock prices
        const maxPrice = Math.max(...currentPrices)
        const minPrice = Math.min(...currentPrices)
        return maxPrice >= game_info.barrier_up || minPrice <= game_info.barrier_down
      }
    }

    return false
  }

  // Start game automatically
  useEffect(() => {
    if (gameState === 'ready') {
      setGameState('playing')
      // Start animation to first step
      setTimeout(() => {
        setCurrentStep(1)
        // Don't show machine decision initially - wait for first user decision
      }, 1000)
    }
  }, [gameState])

  // Auto-advance animation (FIXED: removed !gameEnded check)
  useEffect(() => {
    if (gameState === 'playing' && !playerDecision && currentStep > 0 && currentStep < nb_dates) {
      // Wait for user decision - don't auto-advance
      return
    }

    // FIXED: Allow animation even when game ended (for fast-forward)
    if (isAnimating && currentStep < nb_dates) {
      animationRef.current = setTimeout(() => {
        setCurrentStep(prev => prev + 1)
        setRevealedUpToStep(prev => prev + 1) // Reveal during fast-forward animation
      }, 500) // Fast animation
    }

    return () => {
      if (animationRef.current) {
        clearTimeout(animationRef.current)
      }
    }
  }, [currentStep, isAnimating, playerDecision, gameState])

  // Check for automatic termination (barrier hit or maturity)
  useEffect(() => {
    if (gameState !== 'playing') return
    if (playerDecision) return // Already decided

    // Check if barrier hit
    if (isBarrierHit() && !playerDecision) {
      handleBarrierHit()
    }

    // Check if reached maturity
    if (currentStep === nb_dates && !playerDecision) {
      handleMaturity()
    }
  }, [currentStep, gameState, playerDecision])

  const handleBarrierHit = () => {
    // Player's payoff is 0 (barrier hit)
    setPlayerExerciseDate(currentStep)
    setPlayerPayoff(0)
    setPlayerDecision('barrier_hit')
    setRevealedUpToStep(currentStep) // Reveal machine line for this step

    // Show fast animation for machine if it hasn't exercised yet
    if (currentStep < machineExerciseDate) {
      setIsAnimating(true)
    } else {
      // Machine already exercised
      setMachinePayoff(payoffs_timeline[machineExerciseDate])
      finishGame()
    }
  }

  const handleMaturity = () => {
    // Reached maturity without exercising
    setPlayerExerciseDate(nb_dates)
    setPlayerPayoff(payoffs_timeline[nb_dates])
    setPlayerDecision('maturity')

    // Set machine payoff
    setMachinePayoff(payoffs_timeline[machineExerciseDate])
    finishGame()
  }

  const handleHold = () => {
    if (playerDecision) return

    // Check if at maturity
    if (currentStep === nb_dates) {
      handleMaturity()
      return
    }

    // NEW: Hide machine decision, then show after delay
    setShowMachineDecision(false)
    setMachineDecisionFlash(true)

    // Delay before advancing to next step
    setTimeout(() => {
      setShowMachineDecision(true)
      setMachineDecisionFlash(false)
      setRevealedUpToStep(currentStep) // Reveal machine line for this step
      setCurrentStep(prev => prev + 1)
    }, 300) // 0.3s delay
  }

  const handleExercise = () => {
    if (playerDecision) return

    // Player exercises
    setPlayerExerciseDate(currentStep)
    setPlayerPayoff(payoffs_timeline[currentStep])
    setPlayerDecision('exercise')
    setRevealedUpToStep(currentStep) // Reveal machine line for this step

    // Check if machine already exercised
    if (currentStep >= machineExerciseDate) {
      setMachinePayoff(payoffs_timeline[machineExerciseDate])
      finishGame()
    } else {
      // Continue animation to show machine's future decisions
      setIsAnimating(true)
    }
  }

  // Lock machine payoff when displayStep reaches machine exercise date
  // displayStep = currentStep - 1, so we set payoff when currentStep > machineExerciseDate
  useEffect(() => {
    const displayStep = currentStep - 1
    if (displayStep >= machineExerciseDate && machinePayoff === null) {
      setMachinePayoff(payoffs_timeline[machineExerciseDate])
    }
  }, [currentStep, machineExerciseDate, machinePayoff, payoffs_timeline])

  // When animation reaches machine exercise date or maturity
  useEffect(() => {
    if (isAnimating && playerDecision) {
      // Check if barrier is hit during fast forward (before machine exercises)
      if (currentStep < machineExerciseDate && isBarrierHit()) {
        // Barrier hit before machine could exercise - machine gets $0
        setIsAnimating(false)
        setMachinePayoff(0)
        finishGame()
      } else if (currentStep >= machineExerciseDate) {
        // Machine exercised before barrier
        setIsAnimating(false)
        setMachinePayoff(payoffs_timeline[machineExerciseDate])
        finishGame()
      } else if (currentStep >= nb_dates) {
        // Reached maturity
        setIsAnimating(false)
        setMachinePayoff(payoffs_timeline[machineExerciseDate])
        finishGame()
      }
    }
  }, [currentStep, isAnimating, playerDecision, machineExerciseDate])

  const finishGame = () => {
    setTimeout(() => {
      onGameComplete()
    }, 1000)
  }

  const getMachineDecisionText = () => {
    if (!showMachineDecision) return '-'

    // Show decision for PREVIOUS step to avoid spoiling
    const displayStep = currentStep - 1
    if (displayStep < 1) return '-'

    if (displayStep < machineExerciseDate) {
      return 'HOLD'
    } else if (displayStep === machineExerciseDate) {
      return 'EXERCISE'
    } else {
      return 'EXERCISED'
    }
  }

  const getMachineCurrentPayoff = () => {
    // If machine has exercised, show locked payoff
    if (machinePayoff !== null) {
      return machinePayoff
    }

    // Always show $0.00 until machine exercises
    return 0
  }

  const isPlayerTurn = gameState === 'playing' && !playerDecision && !isAnimating && currentStep > 0 && currentStep <= nb_dates

  // Determine current game ID based on game name
  const getCurrentGameId = () => {
    const name = game_info.name

    // Map game names to their IDs
    const nameToIdMap = {
      'UpAndOutCall': 'upandoutcall',
      'DownAndOutMinPut': 'downandoutminput',
      'DoubleBarrierMaxCall': 'doublebarriermaxcall',
      'RandomlyMovingBarrierCall': 'randomlymovingbarriercall',
      'UpAndOutMinPut': 'upandoutminput',
      'DownAndOutBest2Call': 'downandoutbest2call',
      'DoubleBarrierLookbackFloatingPut': 'doublebarrierlookbackfloatingput',
      'DoubleBarrierRankWeightedBskCall': 'doublebarrierrankweightedbskcall',
      'DoubleMovingBarrierDispersionCall': 'doublemovingbarrierdispersioncall'
    }

    return nameToIdMap[name] || 'upandoutcall'
  }

  const handleOpenGameSelection = () => {
    setShowGameSelection(true)
  }

  const handleSelectGame = (gameId) => {
    onSwitchProduct(gameId)
  }

  return (
    <div>
      {gameState === 'results' ? (
        <ResultsDisplay
          playerPayoff={playerPayoff}
          machinePayoff={machinePayoff}
          playerExerciseDate={playerExerciseDate}
          machineExerciseDate={machineExerciseDate}
          gameInfo={game_info}
          onPlayAgain={onPlayAgain}
          onSwitchProduct={handleOpenGameSelection}
          playerDecision={playerDecision}
          payoffsTimeline={payoffs_timeline}
        />
      ) : (
        <>
          <div className="game-board">
            <StockChart
              path={path}
              currentStep={currentStep}
              gameInfo={game_info}
              playerExerciseDate={playerExerciseDate}
              machineExerciseDate={machineExerciseDate}
              revealedUpToStep={revealedUpToStep}
              isAnimating={isAnimating}
              onHold={handleHold}
              onExercise={handleExercise}
              isPlayerTurn={isPlayerTurn}
            />

            <InfoPanel
              currentStep={currentStep}
              nbDates={nb_dates}
              currentPayoff={payoffs_timeline[currentStep]}
              gameInfo={game_info}
              path={path}
              isBarrierHit={isBarrierHit()}
              machineDecision={getMachineDecisionText()}
              machineCurrentPayoff={getMachineCurrentPayoff()}
              machineDecisionFlash={machineDecisionFlash}
              barrierPathUpper={barrier_path_upper}
              barrierPathLower={barrier_path_lower}
            />
          </div>

          <ControlPanel
            onSwitchProduct={handleOpenGameSelection}
            isAnimating={isAnimating}
            currentProduct={game_info.name}
          />
        </>
      )}

      {/* Game Selection Modal */}
      {showGameSelection && (
        <GameSelectionModal
          onClose={() => setShowGameSelection(false)}
          onSelectGame={handleSelectGame}
          currentGame={getCurrentGameId()}
        />
      )}
    </div>
  )
}

export default GameBoard
