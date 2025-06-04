import React, { useState } from 'react';
import { createFFmpeg, fetchFile } from '@ffmpeg/ffmpeg';

interface ExporterProps {
  audioBlob: Blob | null;
  visualizationsCanvas: HTMLCanvasElement | null;
  subtitles: string;
}

const Exporter: React.FC<ExporterProps> = ({ audioBlob, visualizationsCanvas, subtitles }) => {
  const [isExporting, setIsExporting] = useState(false);
  const [exportUrl, setExportUrl] = useState<string | null>(null);

  const ffmpeg = createFFmpeg({ log: true });

  const exportVideo = async () => {
    if (!audioBlob || !visualizationsCanvas) {
      alert('Audio and visualizations are required for export.');
      return;
    }
    setIsExporting(true);

    try {
      if (!ffmpeg.isLoaded()) {
        await ffmpeg.load();
      }

      // Prepare files
      ffmpeg.FS('writeFile', 'audio.wav', await fetchFile(audioBlob));

      // Convert canvas to video frames (simplified: export as image sequence or video)
      // For demo, export canvas as PNG
      const canvasBlob = await new Promise<Blob | null>((resolve) =>
        visualizationsCanvas.toBlob((blob) => resolve(blob), 'image/png')
      );
      if (!canvasBlob) throw new Error('Failed to get canvas blob');
      ffmpeg.FS('writeFile', 'frame.png', await fetchFile(canvasBlob));

      // Write subtitles file
      ffmpeg.FS('writeFile', 'subtitles.srt', subtitles);

      // Run ffmpeg command to create video (simplified example)
      await ffmpeg.run(
        '-loop',
        '1',
        '-i',
        'frame.png',
        '-i',
        'audio.wav',
        '-c:v',
        'libx264',
        '-t',
        '10',
        '-pix_fmt',
        'yuv420p',
        '-vf',
        'subtitles=subtitles.srt',
        'output.mp4'
      );

      const data = ffmpeg.FS('readFile', 'output.mp4');
      const videoBlob = new Blob([data.buffer], { type: 'video/mp4' });
      const url = URL.createObjectURL(videoBlob);
      setExportUrl(url);
    } catch (error) {
      console.error('Export error:', error);
      alert('Failed to export video.');
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <div className="p-4 bg-white dark:bg-gray-900 rounded-lg shadow-md max-w-full">
      <h2 className="text-xl font-semibold mb-4 text-gray-900 dark:text-gray-100">
        Export & Share
      </h2>
      <button
        onClick={exportVideo}
        disabled={isExporting}
        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 focus:outline-none"
      >
        {isExporting ? 'Exporting...' : 'Export Video'}
      </button>
      {exportUrl && (
        <div className="mt-4">
          <video src={exportUrl} controls className="w-full rounded" />
          <a
            href={exportUrl}
            download="vocal_mirror_export.mp4"
            className="block mt-2 text-blue-600 hover:underline"
          >
            Download Video
          </a>
        </div>
      )}
      {/* Sharing buttons (Discord, Twitch, YouTube Shorts) would be implemented here */}
    </div>
  );
};

export default Exporter;
