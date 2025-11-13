import React from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'

const StockChart = ({ path, currentStep, gameInfo, playerExerciseDate, machineExerciseDate }) => {
  // Prepare data for chart (only show up to current step)
  const chartData = []
  for (let i = 0; i <= currentStep; i++) {
    const dataPoint = { step: i }

    // Add each stock's price
    path.forEach((stock, idx) => {
      dataPoint[`Stock ${idx + 1}`] = stock[i]
    })

    chartData.push(dataPoint)
  }

  // Colors for different stocks
  const colors = ['#00ff00', '#00ffff', '#ff00ff', '#ffff00', '#ff9900']

  // Generate lines for each stock
  const stockLines = path.map((_, idx) => (
    <Line
      key={idx}
      type="monotone"
      dataKey={`Stock ${idx + 1}`}
      stroke={colors[idx % colors.length]}
      strokeWidth={3}
      dot={false}
      animationDuration={300}
    />
  ))

  return (
    <div className="chart-container">
      <div className="chart-header">
        <div className="chart-title">STOCK PRICE PATHS</div>
        <div className="chart-game-name">{gameInfo.name}</div>
      </div>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#333" />
          <XAxis
            dataKey="step"
            stroke="#00ff00"
            tick={{ fill: '#00ff00', fontSize: 10 }}
            label={{ value: 'Time Step', position: 'insideBottom', offset: -5, fill: '#00ff00', fontSize: 12 }}
          />
          <YAxis
            stroke="#00ff00"
            tick={{ fill: '#00ff00', fontSize: 10 }}
            label={{ value: 'Price', angle: -90, position: 'insideLeft', fill: '#00ff00', fontSize: 12 }}
            domain={['auto', 'auto']}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1a1a2e',
              border: '2px solid #00ff00',
              borderRadius: '5px',
              fontSize: '10px',
              fontFamily: 'Press Start 2P'
            }}
            labelStyle={{ color: '#00ffff' }}
            itemStyle={{ color: '#00ff00' }}
          />
          <Legend
            wrapperStyle={{ fontSize: '10px', fontFamily: 'Press Start 2P', paddingTop: '20px' }}
            iconType="line"
            verticalAlign="bottom"
          />

          {/* Barrier lines */}
          {gameInfo.barrier && (
            <ReferenceLine
              y={gameInfo.barrier}
              stroke="#ff0000"
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{ value: 'BARRIER', fill: '#ff0000', fontSize: 10, position: 'right' }}
            />
          )}
          {gameInfo.barrier_up && (
            <ReferenceLine
              y={gameInfo.barrier_up}
              stroke="#ff0000"
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{ value: 'UPPER', fill: '#ff0000', fontSize: 10, position: 'right' }}
            />
          )}
          {gameInfo.barrier_down && (
            <ReferenceLine
              y={gameInfo.barrier_down}
              stroke="#ff0000"
              strokeDasharray="5 5"
              strokeWidth={2}
              label={{ value: 'LOWER', fill: '#ff0000', fontSize: 10, position: 'right' }}
            />
          )}

          {/* Strike line */}
          <ReferenceLine
            y={gameInfo.strike}
            stroke="#ffff00"
            strokeDasharray="3 3"
            strokeWidth={1}
            label={{ value: 'STRIKE', fill: '#ffff00', fontSize: 10, position: 'right' }}
          />

          {/* Exercise markers */}
          {playerExerciseDate !== null && currentStep >= playerExerciseDate && (
            <ReferenceLine
              x={playerExerciseDate}
              stroke="#00ff00"
              strokeWidth={3}
              label={{ value: 'YOU', fill: '#00ff00', fontSize: 10, position: 'top' }}
            />
          )}
          {machineExerciseDate !== null && currentStep >= machineExerciseDate && (
            <ReferenceLine
              x={machineExerciseDate}
              stroke="#ff00ff"
              strokeWidth={3}
              label={{ value: 'MACHINE', fill: '#ff00ff', fontSize: 10, position: 'bottom' }}
            />
          )}

          {stockLines}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export default StockChart
