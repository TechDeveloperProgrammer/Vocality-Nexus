# Vocality Nexus API Reference

## Authentication

### User Registration
- **Endpoint**: `/api/auth/register`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "username": "string",
    "email": "string",
    "password": "string",
    "pronouns": "string",
    "preferred_voice_styles": ["string"]
  }
  ```
- **Response**:
  ```json
  {
    "user_uuid": "string",
    "token": "jwt_token"
  }
  ```

### User Login
- **Endpoint**: `/api/auth/login`
- **Method**: `POST`
- **Request Body**:
  ```json
  {
    "email": "string",
    "password": "string"
  }
  ```
- **Response**:
  ```json
  {
    "access_token": "jwt_token",
    "user_profile": {
      "uuid": "string",
      "username": "string"
    }
  }
  ```

## Voice Transformation

### Transform Voice
- **Endpoint**: `/api/voice/transform`
- **Method**: `POST`
- **Request Body** (multipart/form-data):
  - `audio`: Audio file
  - `params`: JSON string with transformation parameters
    ```json
    {
      "pitch_shift": -2,
      "timbre_style": "warm",
      "gender_transform": "feminine"
    }
    ```
- **Response**:
  ```json
  {
    "transform_id": "unique_id",
    "output_file_path": "string",
    "metadata": {
      "device": "cuda/cpu",
      "transformation_params": "object"
    }
  }
  ```

### Analyze Voice Characteristics
- **Endpoint**: `/api/voice/analyze`
- **Method**: `POST`
- **Request Body** (multipart/form-data):
  - `audio`: Audio file
- **Response**:
  ```json
  {
    "pitch": {
      "fundamental_frequency": 220.0,
      "pitch_stability": 0.85,
      "pitch_range": [100, 300]
    },
    "timbre": {
      "brightness": 0.6,
      "harmonicity": 0.75,
      "spectral_centroid": 2500.0
    },
    "gender_characteristics": {
      "masculine_probability": 0.7,
      "feminine_probability": 0.3
    }
  }
  ```

## Recommendations

### Get Voice Profile Recommendations
- **Endpoint**: `/api/voice/recommend`
- **Method**: `GET`
- **Query Parameters**:
  - `user_uuid`: User's unique identifier
  - `max_recommendations`: Maximum number of recommendations (default: 10)
- **Response**:
  ```json
  {
    "recommendations": [
      {
        "name": "Warm Baritone",
        "description": "Deep, resonant voice profile",
        "similarity_score": 0.85
      }
    ]
  }
  ```

### Get Community Event Recommendations
- **Endpoint**: `/api/events/recommend`
- **Method**: `GET`
- **Query Parameters**:
  - `user_uuid`: User's unique identifier
  - `max_recommendations`: Maximum number of recommendations (default: 5)
- **Response**:
  ```json
  {
    "recommendations": [
      {
        "title": "AI Voice Tech Conference",
        "description": "Cutting-edge voice technology symposium",
        "start_time": "2024-07-15T09:00:00Z"
      }
    ]
  }
  ```

## Performance Monitoring

### Get Performance Report
- **Endpoint**: `/api/performance/report`
- **Method**: `GET`
- **Query Parameters**:
  - `duration_hours`: Duration for performance analysis (default: 1)
- **Response**:
  ```json
  {
    "timestamp": "2024-01-01T12:00:00Z",
    "uptime": 3600,
    "system_resources": {
      "cpu_usage": 45.5,
      "memory": {
        "total": 16777216000,
        "available": 8388608000,
        "percent": 50
      }
    },
    "ai_performance": {
      "total_inferences": 1000,
      "average_inference_time": 0.05,
      "model_performance": {
        "voice_transformer": {
          "total_inferences": 500,
          "average_inference_time": 0.03
        }
      }
    }
  }
  ```

## Error Handling
- All endpoints return consistent error responses:
  ```json
  {
    "error": "Error description",
    "code": "ERROR_CODE"
  }
  ```

## Rate Limiting
- Most endpoints are limited to 100 requests per minute per user
- Authenticated endpoints have higher limits

## Authentication Requirements
- 🔒 Indicates endpoint requires JWT authentication
- Provide `Authorization: Bearer <jwt_token>` header

## Versioning
- Current API Version: `v1`
- Base URL: `/api/v1/`

## Pagination
- Endpoints returning lists support:
  - `page`: Page number
  - `per_page`: Items per page (default: 10)

## Webhooks
- Configurable webhooks for:
  - Voice transformation completion
  - Recommendation updates
  - Performance alerts
