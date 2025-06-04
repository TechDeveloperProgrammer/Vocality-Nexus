import React, { useEffect, useRef, useState } from 'react';
import WaveSurfer from 'wavesurfer.js';

interface RecorderProps {
  onRecordingComplete: (blob: Blob) => void;
}

const Recorder: React.FC<RecorderProps> = ({ onRecordingComplete }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const waveSurferRef = useRef<WaveSurfer | null>(null);
  const waveformContainerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (waveformContainerRef.current) {
      waveSurferRef.current = WaveSurfer.create({
        container: waveformContainerRef.current,
        waveColor: '#3b82f6',
        progressColor: '#10b981',
        height: 80,
        responsive: true,
      });
    }
    return () => {
      waveSurferRef.current?.destroy();
    };
  }, []);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorderRef.current = new MediaRecorder(stream);
    audioChunksRef.current = [];

    mediaRecorderRef.current.ondataavailable = (event) => {
      audioChunksRef.current.push(event.data);
    };

    mediaRecorderRef.current.onstop = () => {
      const blob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
      setRecordedBlob(blob);
      onRecordingComplete(blob);
      if (waveSurferRef.current) {
        waveSurferRef.current.loadBlob(blob);
      }
    };

    mediaRecorderRef.current.start();
    setIsRecording(true);
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  const playRecording = () => {
    waveSurferRef.current?.playPause();
  };

  return (
    <div className="p-4 bg-white dark:bg-gray-900 rounded-lg shadow-md max-w-full">
      <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
        Recorder
      </h2>
      <div ref={waveformContainerRef} className="mb-4" aria-label="Audio waveform" />
      <div className="flex space-x-4">
        {!isRecording ? (
          <button
            onClick={startRecording}
            className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 focus:outline-none"
          >
            Start Recording
          </button>
        ) : (
          <button
            onClick={stopRecording}
            className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 focus:outline-none"
          >
            Stop Recording
          </button>
        )}
        {recordedBlob && (
          <button
            onClick={playRecording}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none"
          >
            Play / Pause
          </button>
        )}
      </div>
    </div>
  );
};

export default Recorder;
