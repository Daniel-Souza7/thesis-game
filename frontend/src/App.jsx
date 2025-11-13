import React, { useState, useEffect } from 'react'
import axios from 'axios'
import GameBoard from './components/GameBoard'

const API_BASE_URL = import.meta.env.PROD
  ? 'https://your-backend-url.vercel.app/api'  // Update this for production
  : '/api'

function App() {
  const [gameState, setGameState] = useState('loading') // loading, ready, playing, results
  const [currentProduct, setCurrentProduct] = useState('upandout')
  const [gameData, setGameData] = useState(null)
  const [error, setError] = useState(null)

  // Load initial game on mount
  useEffect(() => {
    startNewGame(currentProduct)
  }, [])

  const startNewGame = async (product) => {
    setGameState('loading')
    setError(null)

    try {
      const response = await axios.get(`${API_BASE_URL}/game/start`, {
        params: { product }
      })

      setGameData(response.data)
      setCurrentProduct(product)
      setGameState('ready')
    } catch (err) {
      console.error('Error starting game:', err)
      setError(err.message || 'Failed to start game. Make sure the backend is running.')
      setGameState('error')
    }
  }

  const switchProduct = () => {
    const newProduct = currentProduct === 'upandout' ? 'dko' : 'upandout'
    startNewGame(newProduct)
  }

  const handleGameComplete = () => {
    setGameState('results')
  }

  const playAgain = () => {
    startNewGame(currentProduct)
  }

  return (
    <div className="arcade-container">
      <h1 className="game-title">OPTIMAL STOPPING GAME</h1>
      <p className="game-subtitle">Challenge the Algorithm - Can You Beat the Machine?</p>

      {gameState === 'loading' && (
        <div className="loading-screen">
          <div className="loading-text">LOADING GAME...</div>
          <div className="loading-spinner"></div>
        </div>
      )}

      {gameState === 'error' && (
        <div className="error-message">
          <p>ERROR: {error}</p>
          <button className="arcade-button start" onClick={() => startNewGame(currentProduct)}>
            TRY AGAIN
          </button>
        </div>
      )}

      {(gameState === 'ready' || gameState === 'playing' || gameState === 'results') && gameData && (
        <>
          <GameBoard
            gameData={gameData}
            onGameComplete={handleGameComplete}
            onSwitchProduct={switchProduct}
            onPlayAgain={playAgain}
            gameState={gameState}
            setGameState={setGameState}
          />
        </>
      )}
    </div>
  )
}

export default App
