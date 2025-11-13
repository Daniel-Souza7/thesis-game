import React, { useState, useEffect, useRef } from 'react'
import StockChart from './StockChart'
import InfoPanel from './InfoPanel'
import ControlPanel from './ControlPanel'
import ResultsDisplay from './ResultsDisplay'

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

  const animationRef = useRef(null)

  const { path, payoffs_timeline, game_info, machine_decisions } = gameData
  const nb_dates = game_info.nb_dates

  // Check if barrier is hit at current step
  const isBarrierHit = () => {
    if (!game_info.barrier_type) return false

    const currentPrices = path.map(stock => stock[currentStep])

    if (game_info.barrier_type === 'up') {
      return currentPrices.some(price => price >= game_info.barrier)
    } else if (game_info.barrier_type === 'double') {
      const maxPrice = Math.max(...currentPrices)
      const minPrice = Math.min(...currentPrices)
      return maxPrice >= game_info.barrier_up || minPrice <= game_info.barrier_down
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
        setShowMachineDecision(true) // Show machine decision for step 1
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
      setCurrentStep(prev => prev + 1)
    }, 300) // 0.3s delay
  }

  const handleExercise = () => {
    if (playerDecision) return

    // Player exercises
    setPlayerExerciseDate(currentStep)
    setPlayerPayoff(payoffs_timeline[currentStep])
    setPlayerDecision('exercise')

    // Check if machine already exercised
    if (currentStep >= machineExerciseDate) {
      setMachinePayoff(payoffs_timeline[machineExerciseDate])
      finishGame()
    } else {
      // Continue animation to show machine's future decisions
      setIsAnimating(true)
    }
  }

  // When animation reaches machine exercise date or maturity
  useEffect(() => {
    if (isAnimating && playerDecision) {
      if (currentStep >= machineExerciseDate) {
        setIsAnimating(false)
        setMachinePayoff(payoffs_timeline[machineExerciseDate])
        finishGame()
      } else if (currentStep >= nb_dates) {
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
    if (!showMachineDecision) return '...'

    if (currentStep < machineExerciseDate) {
      return 'HOLD'
    } else if (currentStep === machineExerciseDate) {
      return 'EXERCISE'
    } else {
      return 'EXERCISED'
    }
  }

  const getMachineCurrentPayoff = () => {
    // If machine hasn't exercised yet, show current payoff
    // If machine has exercised, show locked payoff
    if (machinePayoff !== null) {
      return machinePayoff
    }
    return payoffs_timeline[currentStep]
  }

  const isPlayerTurn = gameState === 'playing' && !playerDecision && !isAnimating && currentStep > 0 && currentStep <= nb_dates

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
          onSwitchProduct={onSwitchProduct}
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
            />
          </div>

          <ControlPanel
            onHold={handleHold}
            onExercise={handleExercise}
            onSwitchProduct={onSwitchProduct}
            isPlayerTurn={isPlayerTurn}
            isAnimating={isAnimating}
            currentProduct={game_info.name}
          />
        </>
      )}
    </div>
  )
}

export default GameBoard
