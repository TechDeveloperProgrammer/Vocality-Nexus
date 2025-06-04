import React, { useState, useCallback } from 'react';
import AudioAnalyzer, { AudioFeatures } from './AudioAnalyzer';
import EmotionDetector, { Emotion } from './EmotionDetector';
import VisualizationPanel from './VisualizationPanel';
import VocalGoalPanel from './VocalGoalPanel';
import ProgressPanel from './ProgressPanel';
import AITuner from './AITuner';
import Recorder from './Recorder';
import Exporter from './Exporter';

const Dashboard: React.FC = () => {
  const [audioFeatures, setAudioFeatures] = useState<AudioFeatures>({
    pitch: null,
    timbre: null,
    intensity: null,
    rhythm: null,
    clarity: null,
  });
  const [emotion, setEmotion] = useState<Emotion>('unknown');
  const [preset] = useState({
    name: 'Ideal Vocal Preset',
    description: 'A balanced vocal tone with clarity and warmth.',
    pitchCurve: Array(64).fill(0.5),
    spectrogramData: Array(64).fill(Array(64).fill(0.5)),
    emotionLabel: 'neutral',
  });
  const [progress, setProgress] = useState(0);
  const [feedback, setFeedback] = useState('Start singing to see your progress.');
  const [tunerMode, setTunerMode] = useState<'auto' | 'manual'>('auto');
  const [tunerParams, setTunerParams] = useState({
    formants: 0.5,
    pitch: 0.5,
    resonance: 0.5,
    intensity: 0.5,
  });
  const [recordedAudio, setRecordedAudio] = useState<Blob | null>(null);
  const [subtitles, setSubtitles] = useState('1\n00:00:00,000 --> 00:00:10,000\nSample subtitle text.');

  const handleFeaturesUpdate = useCallback((features: AudioFeatures) => {
    setAudioFeatures(features);
    // Simple progress calculation placeholder
    if (features.pitch !== null) {
      const prog = Math.min(100, Math.max(0, features.pitch * 100));
      setProgress(prog);
      setFeedback(`Pitch accuracy: ${prog.toFixed(1)}%`);
    }
  }, []);

  const handleEmotionDetected = useCallback((detectedEmotion: Emotion) => {
    setEmotion(detectedEmotion);
  }, []);

  const handleModeChange = (mode: 'auto' | 'manual') => {
    setTunerMode(mode);
  };

  const handleParameterChange = (params: typeof tunerParams) => {
    setTunerParams(params);
  };

  const handleRecordingComplete = (blob: Blob) => {
    setRecordedAudio(blob);
  };

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* You Now Panel */}
      <div>
        <h1 className="text-2xl font-bold mb-4 text-gray-900 dark:text-gray-100">You Now</h1>
        <AudioAnalyzer onFeaturesUpdate={handleFeaturesUpdate} />
        <EmotionDetector audioBuffer={null} onEmotionDetected={handleEmotionDetected} />
        <VisualizationPanel
          pitchData={audioFeatures.pitch !== null ? Array(64).fill(audioFeatures.pitch) : Array(64).fill(0)}
          spectrogramData={preset.spectrogramData}
          emotionLevel={emotion === 'unknown' ? 0 : 1}
          emotionLabel={emotion}
        />
      </div>

      {/* Your Vocal Goal Panel */}
      <div>
        <VocalGoalPanel
          presetName={preset.name}
          presetDescription={preset.description}
          pitchCurve={preset.pitchCurve}
          spectrogramData={preset.spectrogramData}
          emotionLabel={preset.emotionLabel}
        />
        <ProgressPanel progressPercentage={progress} feedbackMessage={feedback} />
        <AITuner
          mode={tunerMode}
          onModeChange={handleModeChange}
          onParameterChange={handleParameterChange}
          initialParameters={tunerParams}
        />
      </div>

      {/* Recording and Export Panel */}
      <div>
        <Recorder onRecordingComplete={handleRecordingComplete} />
        <Exporter audioBlob={recordedAudio} visualizationsCanvas={null} subtitles={subtitles} />
      </div>
    </div>
  );
};

export default Dashboard;
