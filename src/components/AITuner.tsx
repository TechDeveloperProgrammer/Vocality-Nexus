import React, { useState } from 'react';

interface AITunerProps {
  mode: 'auto' | 'manual';
  onModeChange: (mode: 'auto' | 'manual') => void;
  onParameterChange: (params: {
    formants: number;
    pitch: number;
    resonance: number;
    intensity: number;
  }) => void;
  initialParameters: {
    formants: number;
    pitch: number;
    resonance: number;
    intensity: number;
  };
}

const AITuner: React.FC<AITunerProps> = ({
  mode,
  onModeChange,
  onParameterChange,
  initialParameters,
}) => {
  const [parameters, setParameters] = useState(initialParameters);

  const handleSliderChange = (param: keyof typeof parameters, value: number) => {
    const newParams = { ...parameters, [param]: value };
    setParameters(newParams);
    onParameterChange(newParams);
  };

  return (
    <div className="p-4 bg-white dark:bg-gray-900 rounded-lg shadow-md max-w-full">
      <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
        AI Vocal Tuner
      </h2>

      <div className="mb-4">
        <label className="inline-flex items-center">
          <input
            type="radio"
            name="mode"
            value="auto"
            checked={mode === 'auto'}
            onChange={() => onModeChange('auto')}
            className="form-radio"
          />
          <span className="ml-2 text-gray-800 dark:text-gray-200">Automatic Mode</span>
        </label>
        <label className="inline-flex items-center ml-6">
          <input
            type="radio"
            name="mode"
            value="manual"
            checked={mode === 'manual'}
            onChange={() => onModeChange('manual')}
            className="form-radio"
          />
          <span className="ml-2 text-gray-800 dark:text-gray-200">Manual Mode</span>
        </label>
      </div>

      {mode === 'manual' && (
        <div>
          <div className="mb-4">
            <label className="block text-gray-700 dark:text-gray-300 mb-1">
              Formants: {parameters.formants.toFixed(2)}
            </label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={parameters.formants}
              onChange={(e) => handleSliderChange('formants', parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 dark:text-gray-300 mb-1">
              Pitch: {parameters.pitch.toFixed(2)}
            </label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={parameters.pitch}
              onChange={(e) => handleSliderChange('pitch', parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 dark:text-gray-300 mb-1">
              Resonance: {parameters.resonance.toFixed(2)}
            </label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={parameters.resonance}
              onChange={(e) => handleSliderChange('resonance', parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          <div className="mb-4">
            <label className="block text-gray-700 dark:text-gray-300 mb-1">
              Intensity: {parameters.intensity.toFixed(2)}
            </label>
            <input
              type="range"
              min={0}
              max={1}
              step={0.01}
              value={parameters.intensity}
              onChange={(e) => handleSliderChange('intensity', parseFloat(e.target.value))}
              className="w-full"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default AITuner;
