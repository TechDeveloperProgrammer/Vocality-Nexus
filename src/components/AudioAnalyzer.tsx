import React, { useEffect, useRef, useState } from 'react';
import * as Tone from 'tone';
import Meyda from 'meyda';

export interface AudioFeatures {
  pitch: number | null;
  timbre: number[] | null;
  intensity: number | null;
  rhythm: number | null;
  clarity: number | null;
}

interface AudioAnalyzerProps {
  onFeaturesUpdate: (features: AudioFeatures) => void;
}

const AudioAnalyzer: React.FC<AudioAnalyzerProps> = ({ onFeaturesUpdate }) => {
  const micRef = useRef<MediaStreamAudioSourceNode | null>(null);
  const analyzerRef = useRef<AnalyserNode | null>(null);
  const meydaAnalyzerRef = useRef<any>(null);
  const [isRunning, setIsRunning] = useState(false);

  useEffect(() => {
    const startAudio = async () => {
      await Tone.start();
      const mic = new Tone.UserMedia();
      await mic.open();
      micRef.current = mic.context.createMediaStreamSource(mic.mediaStream!);
      analyzerRef.current = mic.context.createAnalyser();
      micRef.current.connect(analyzerRef.current);

      meydaAnalyzerRef.current = Meyda.createMeydaAnalyzer({
        audioContext: mic.context,
        source: micRef.current,
        bufferSize: 512,
        featureExtractors: ['rms', 'spectralCentroid', 'spectralFlatness', 'zcr', 'mfcc', 'pitch'],
        callback: (features: any) => {
          // Extract features
          const pitch = features.pitch ? features.pitch : null;
          const timbre = features.mfcc ? features.mfcc : null;
          const intensity = features.rms ? features.rms : null;
          // Rhythm and clarity are more complex; placeholders for now
          const rhythm = null;
          const clarity = null;

          onFeaturesUpdate({
            pitch,
            timbre,
            intensity,
            rhythm,
            clarity,
          });
        },
      });

      meydaAnalyzerRef.current.start();
      setIsRunning(true);
    };

    startAudio().catch(console.error);

    return () => {
      if (meydaAnalyzerRef.current) {
        meydaAnalyzerRef.current.stop();
        meydaAnalyzerRef.current = null;
      }
      if (micRef.current) {
        micRef.current.disconnect();
        micRef.current = null;
      }
      setIsRunning(false);
    };
  }, [onFeaturesUpdate]);

  return (
    <div>
      {isRunning ? (
        <p>Audio Analyzer Running...</p>
      ) : (
        <p>Initializing Audio Analyzer...</p>
      )}
    </div>
  );
};

export default AudioAnalyzer;
