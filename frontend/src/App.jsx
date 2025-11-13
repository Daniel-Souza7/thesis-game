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
    <>
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

      {/* LinkedIn Button */}
      <a
        href="https://www.linkedin.com/in/souza247/"
        target="_blank"
        rel="noopener noreferrer"
        className="linkedin-button"
        title="Connect on LinkedIn"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
          <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
        </svg>
      </a>
    </>
  )
}

export default App
