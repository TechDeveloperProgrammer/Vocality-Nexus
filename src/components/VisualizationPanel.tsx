import React from 'react';
import { motion } from 'framer-motion';

interface VisualizationPanelProps {
  pitchData: number[];
  spectrogramData: number[][];
  emotionLevel: number; // 0 to 1 representing emotional intensity
  emotionLabel: string;
}

const VisualizationPanel: React.FC<VisualizationPanelProps> = ({
  pitchData,
  spectrogramData,
  emotionLevel,
  emotionLabel,
}) => {
  // Accessible color based on emotion level
  const getEmotionColor = () => {
    if (emotionLevel < 0.2) return 'bg-gray-400';
    if (emotionLevel < 0.4) return 'bg-blue-400';
    if (emotionLevel < 0.6) return 'bg-green-400';
    if (emotionLevel < 0.8) return 'bg-yellow-400';
    return 'bg-red-400';
  };

  return (
    <div className="p-4 bg-white dark:bg-gray-900 rounded-lg shadow-md max-w-full">
      <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-gray-100">
        Vocal Mirror Visualizations
      </h2>

      {/* Pitch Curve */}
      <div className="mb-4">
        <h3 className="text-lg font-medium mb-1 text-gray-800 dark:text-gray-200">
          Pitch Curve
        </h3>
        <svg
          className="w-full h-24 bg-gray-100 dark:bg-gray-800 rounded"
          viewBox={`0 0 ${pitchData.length} 100`}
          preserveAspectRatio="none"
          aria-label="Pitch curve visualization"
          role="img"
        >
          <polyline
            fill="none"
            stroke="#3b82f6"
            strokeWidth="2"
            points={pitchData
              .map((p, i) => `${i},${100 - p * 100}`)
              .join(' ')}
          />
        </svg>
      </div>

      {/* Spectrogram */}
      <div className="mb-4">
        <h3 className="text-lg font-medium mb-1 text-gray-800 dark:text-gray-200">
          Spectrogram
        </h3>
        <div
          className="w-full h-24 grid grid-cols-64 gap-0.5 rounded overflow-hidden"
          aria-label="Spectrogram visualization"
          role="img"
        >
          {spectrogramData.map((freqSlice, i) =>
            freqSlice.map((intensity, j) => (
              <div
                key={`${i}-${j}`}
                className="w-full h-full"
                style={{
                  backgroundColor: `rgba(59, 130, 246, ${intensity})`,
                }}
              />
            ))
          )}
        </div>
      </div>

      {/* Emotional Bar */}
      <div className="mb-2">
        <h3 className="text-lg font-medium mb-1 text-gray-800 dark:text-gray-200">
          Emotional Intensity: {emotionLabel}
        </h3>
        <motion.div
          className={`h-6 rounded ${getEmotionColor()}`}
          initial={{ width: 0 }}
          animate={{ width: `${emotionLevel * 100}%` }}
          transition={{ duration: 0.5 }}
          aria-live="polite"
          aria-atomic="true"
          role="progressbar"
          aria-valuemin={0}
          aria-valuemax={1}
          aria-valuenow={emotionLevel}
        />
      </div>
    </div>
  );
};

export default VisualizationPanel;
