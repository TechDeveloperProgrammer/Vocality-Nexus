import React from 'react';

interface ProgressPanelProps {
  progressPercentage: number; // 0 to 100
  feedbackMessage: string;
}

const ProgressPanel: React.FC<ProgressPanelProps> = ({ progressPercentage, feedbackMessage }) => {
  return (
    <div className="p-4 bg-white dark:bg-gray-900 rounded-lg shadow-md max-w-full">
      <h2 className="text-xl font-semibold mb-2 text-gray-900 dark:text-gray-100">
        Real-time Progress
      </h2>
      <div
        className="w-full h-6 bg-gray-300 dark:bg-gray-700 rounded overflow-hidden mb-2"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={progressPercentage}
        aria-label="Real-time vocal progress"
      >
        <div
          className="h-full bg-green-500 dark:bg-green-400 transition-all duration-500"
          style={{ width: `${progressPercentage}%` }}
        />
      </div>
      <p className="text-gray-700 dark:text-gray-300">{feedbackMessage}</p>
    </div>
  );
};

export default ProgressPanel;
