import React, { useState, useRef } from 'react';
import axios from 'axios';
import { 
  Button, 
  Slider, 
  Select, 
  Typography, 
  Card, 
  notification 
} from 'antd';

const { Title, Text } = Typography;
const { Option } = Select;

const VoiceModulator = () => {
  const [audioFile, setAudioFile] = useState(null);
  const [transformationParams, setTransformationParams] = useState({
    pitch_shift: 0,
    timbre_style: 'neutral',
    gender_transform: 'original'
  });
  const [transformedAudio, setTransformedAudio] = useState(null);
  const [voiceAnalysis, setVoiceAnalysis] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const audioInputRef = useRef(null);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    setAudioFile(file);
  };

  const handleTransformationParamChange = (key, value) => {
    setTransformationParams(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const transformVoice = async () => {
    if (!audioFile) {
      notification.error({
        message: 'Error',
        description: 'Please upload an audio file first.'
      });
      return;
    }

    const formData = new FormData();
    formData.append('audio', audioFile);
    formData.append('params', JSON.stringify(transformationParams));

    try {
      const response = await axios.post('/api/voice/transform', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setTransformedAudio(response.data.data.output_file_path);
      notification.success({
        message: 'Success',
        description: 'Voice transformation completed successfully!'
      });
    } catch (error) {
      notification.error({
        message: 'Transformation Error',
        description: error.response?.data?.error || 'Voice transformation failed'
      });
    }
  };

  const analyzeVoice = async () => {
    if (!audioFile) {
      notification.error({
        message: 'Error',
        description: 'Please upload an audio file first.'
      });
      return;
    }

    const formData = new FormData();
    formData.append('audio', audioFile);

    try {
      const response = await axios.post('/api/voice/analyze', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      setVoiceAnalysis(response.data.data);
      notification.success({
        message: 'Analysis Complete',
        description: 'Voice characteristics analyzed successfully!'
      });
    } catch (error) {
      notification.error({
        message: 'Analysis Error',
        description: error.response?.data?.error || 'Voice analysis failed'
      });
    }
  };

  const getRecommendations = async () => {
    try {
      const response = await axios.get('/api/voice/recommend', {
        params: {
          user_uuid: 'current_user_uuid', // Replace with actual user UUID
          max_recommendations: 5
        }
      });

      setRecommendations(response.data.data);
      notification.success({
        message: 'Recommendations',
        description: 'Voice profile recommendations retrieved!'
      });
    } catch (error) {
      notification.error({
        message: 'Recommendation Error',
        description: error.response?.data?.error || 'Failed to get recommendations'
      });
    }
  };

  return (
    <Card title="Advanced Voice Modulation">
      <div>
        <input 
          type="file" 
          accept="audio/*" 
          ref={audioInputRef}
          onChange={handleFileUpload}
        />
      </div>

      <div>
        <Title level={4}>Voice Transformation Parameters</Title>
        <div>
          <Text>Pitch Shift (Semitones): </Text>
          <Slider
            min={-12}
            max={12}
            value={transformationParams.pitch_shift}
            onChange={(value) => handleTransformationParamChange('pitch_shift', value)}
          />
        </div>

        <div>
          <Text>Timbre Style: </Text>
          <Select
            style={{ width: 200 }}
            value={transformationParams.timbre_style}
            onChange={(value) => handleTransformationParamChange('timbre_style', value)}
          >
            <Option value="neutral">Neutral</Option>
            <Option value="warm">Warm</Option>
            <Option value="bright">Bright</Option>
            <Option value="dark">Dark</Option>
          </Select>
        </div>

        <div>
          <Text>Gender Transform: </Text>
          <Select
            style={{ width: 200 }}
            value={transformationParams.gender_transform}
            onChange={(value) => handleTransformationParamChange('gender_transform', value)}
          >
            <Option value="original">Original</Option>
            <Option value="masculine">Masculine</Option>
            <Option value="feminine">Feminine</Option>
            <Option value="neutral">Neutral</Option>
          </Select>
        </div>
      </div>

      <div>
        <Button 
          type="primary" 
          onClick={transformVoice}
          disabled={!audioFile}
        >
          Transform Voice
        </Button>
        <Button 
          type="default" 
          onClick={analyzeVoice}
          disabled={!audioFile}
        >
          Analyze Voice
        </Button>
        <Button 
          type="dashed" 
          onClick={getRecommendations}
        >
          Get Recommendations
        </Button>
      </div>

      {transformedAudio && (
        <div>
          <Title level={4}>Transformed Audio</Title>
          <audio controls src={transformedAudio} />
        </div>
      )}

      {voiceAnalysis && (
        <div>
          <Title level={4}>Voice Analysis</Title>
          <pre>{JSON.stringify(voiceAnalysis, null, 2)}</pre>
        </div>
      )}

      {recommendations.length > 0 && (
        <div>
          <Title level={4}>Voice Profile Recommendations</Title>
          {recommendations.map((profile, index) => (
            <Card key={index} style={{ marginBottom: 10 }}>
              <Text strong>{profile.name}</Text>
              <Text>{profile.description}</Text>
            </Card>
          ))}
        </div>
      )}
    </Card>
  );
};

export default VoiceModulator;
