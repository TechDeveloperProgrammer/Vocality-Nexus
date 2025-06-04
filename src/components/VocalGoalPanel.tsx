import React from 'react';

interface VocalGoalPanelProps {
  presetName: string;
  presetDescription: string;
  pitchCurve: number[];
  spectrogramData: number[][];
  emotionLabel: string;
}

const VocalGoalPanel: React.FC<VocalGoalPanelProps> = ({
  presetName,
  presetDescription,
  pitchCurve,
  spectrogramData,
  emotionLabel,
}) => {
  return (
    <div className="p-4 bg-white dark:bg-gray-900 rounded-lg shadow-md max-w-full">
      <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-gray-100">
        Your Vocal Goal: {presetName}
      </h2>
      <p className="mb-4 text-gray-700 dark:text-gray-300">{presetDescription}</p>

      {/* Pitch Curve */}
      <div className="mb-4">
        <h3 className="text-lg font-medium mb-1 text-gray-800 dark:text-gray-200">
          Pitch Curve
        </h3>
        <svg
          className="w-full h-24 bg-gray-100 dark:bg-gray-800 rounded"
          viewBox={`0 0 ${pitchCurve.length} 100`}
          preserveAspectRatio="none"
          aria-label="Preset pitch curve visualization"
          role="img"
        >
          <polyline
            fill="none"
            stroke="#10b981"
            strokeWidth="2"
            points={pitchCurve
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
          aria-label="Preset spectrogram visualization"
          role="img"
        >
          {spectrogramData.map((freqSlice, i) =>
            freqSlice.map((intensity, j) => (
              <div
                key={`${i}-${j}`}
                className="w-full h-full"
                style={{
                  backgroundColor: `rgba(16, 185, 129, ${intensity})`,
                }}
              />
            ))
          )}
        </div>
      </div>

      {/* Emotion Label */}
      <div>
        <h3 className="text-lg font-medium mb-1 text-gray-800 dark:text-gray-200">
          Target Emotion: {emotionLabel}
        </h3>
      </div>
    </div>
  );
};

export default VocalGoalPanel;
