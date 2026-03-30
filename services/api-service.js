import { API_ENDPOINTS } from './api-config.js';

export class APIService {
  constructor(baseURL = API_ENDPOINTS.BASE_URL) {
    this.baseURL = baseURL;
    this.token = null;
    this.isInitialized = false;
  }

  async initialize() {
    try {
      await this.checkAuthStatus();
      this.isInitialized = true;
      console.log('API Service initialized successfully');
    } catch (error) {
      console.error('Failed to initialize API Service:', error);
      throw error;
    }
  }

  async checkAuthStatus() {
    try {
      const response = await this.request('GET', API_ENDPOINTS.USER_PROFILE);
      return response.data;
    } catch (error) {
      if (error.status === 401) {
        console.log('User not authenticated');
        return null;
      }
      throw error;
    }
  }

  async login(credentials) {
    try {
      const response = await this.request('POST', API_ENDPOINTS.USER_PROFILE, credentials);
      this.token = response.data.token;
      return response.data;
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    }
  }

  async logout() {
    try {
      await this.request('POST', API_ENDPOINTS.USER_PROFILE + '/logout');
      this.token = null;
      return true;
    } catch (error) {
      console.error('Logout failed:', error);
      throw error;
    }
  }

  async getProfile() {
    try {
      const response = await this.request('GET', API_ENDPOINTS.USER_PROFILE);
      return response.data;
    } catch (error) {
      console.error('Failed to get profile:', error);
      throw error;
    }
  }

  async updateProfile(profileData) {
    try {
      const response = await this.request('PUT', API_ENDPOINTS.USER_PROFILE, profileData);
      return response.data;
    } catch (error) {
      console.error('Failed to update profile:', error);
      throw error;
    }
  }

  async getLearningProgress() {
    try {
      const response = await this.request('GET', API_ENDPOINTS.LEARNING_PROGRESS);
      return response.data;
    } catch (error) {
      console.error('Failed to get learning progress:', error);
      throw error;
    }
  }

  async getPredictions() {
    try {
      const response = await this.request('GET', API_ENDPOINTS.PREDICTION_ANALYSIS);
      return response.data;
    } catch (error) {
      console.error('Failed to get predictions:', error);
      throw error;
    }
  }

  async getKnowledgeMap() {
    try {
      const response = await this.request('GET', API_ENDPOINTS.KNOWLEDGE_MAP);
      return response.data;
    } catch (error) {
      console.error('Failed to get knowledge map:', error);
      throw error;
    }
  }

  async getExamSchedule() {
    try {
      const response = await this.request('GET', API_ENDPOINTS.EXAM_SCHEDULE);
      return response.data;
    } catch (error) {
      console.error('Failed to get exam schedule:', error);
      throw error;
    }
  }

  async getExamPredictions(examId) {
    try {
      const response = await this.request('GET', `${API_ENDPOINTS.EXAM_PREDICTIONS}/${examId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get exam predictions:', error);
      throw error;
    }
  }

  async getQuestionBank(params) {
    try {
      const response = await this.request('GET', API_ENDPOINTS.QUESTION_BANK, { params });
      return response.data;
    } catch (error) {
      console.error('Failed to get question bank:', error);
      throw error;
    }
  }

  async startPracticeSession(params) {
    try {
      const response = await this.request('POST', API_ENDPOINTS.PRACTICE_SESSIONS, params);
      return response.data;
    } catch (error) {
      console.error('Failed to start practice session:', error);
      throw error;
    }
  }

  async submitPracticeAnswers(sessionId, answers) {
    try {
      const response = await this.request('POST', `${API_ENDPOINTS.PRACTICE_SESSIONS}/${sessionId}/answers`, answers);
      return response.data;
    } catch (error) {
      console.error('Failed to submit practice answers:', error);
      throw error;
    }
  }

  async getAnalyticsDashboard() {
    try {
      const response = await this.request('GET', API_ENDPOINTS.ANALYTICS_DASHBOARD);
      return response.data;
    } catch (error) {
      console.error('Failed to get analytics dashboard:', error);
      throw error;
    }
  }

  async getPerformanceTrends() {
    try {
      const response = await this.request('GET', API_ENDPOINTS.PERFORMANCE_TRENDS);
      return response.data;
    } catch (error) {
      console.error('Failed to get performance trends:', error);
      throw error;
    }
  }

  async getRealtimeMetrics() {
    try {
      const response = await this.request('GET', API_ENDPOINTS.REALTIME_METRICS);
      return response.data;
    } catch (error) {
      console.error('Failed to get realtime metrics:', error);
      throw error;
    }
  }

  async getNotifications() {
    try {
      const response = await this.request('GET', API_ENDPOINTS.NOTIFICATIONS);
      return response.data;
    } catch (error) {
      console.error('Failed to get notifications:', error);
      throw error;
    }
  }

  async getAIAssistantResponse(query) {
    try {
      const response = await this.request('POST', API_ENDPOINTS.AI_ASSISTANT, { query });
      return response.data;
    } catch (error) {
      console.error('Failed to get AI assistant response:', error);
      throw error;
    }
  }

  async generateQuestions(params) {
    try {
      const response = await this.request('POST', API_ENDPOINTS.AI_GENERATE_QUESTIONS, params);
      return response.data;
    } catch (error) {
      console.error('Failed to generate questions:', error);
      throw error;
    }
  }

  async getAIAnalysis(data) {
    try {
      const response = await this.request('POST', API_ENDPOINTS.AI_ANALYSIS, data);
      return response.data;
    } catch (error) {
      console.error('Failed to get AI analysis:', error);
      throw error;
    }
  }

  async uploadFile(file, params = {}) {
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await this.request('POST', API_ENDPOINTS.FILE_UPLOAD, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        params
      });
      
      return response.data;
    } catch (error) {
      console.error('Failed to upload file:', error);
      throw error;
    }
  }

  async downloadFile(fileId, params = {}) {
    try {
      const response = await this.request('GET', `${API_ENDPOINTS.FILE_DOWNLOAD}/${fileId}`, {
        responseType: 'blob',
        params
      });
      
      return response.data;
    } catch (error) {
      console.error('Failed to download file:', error);
      throw error;
    }
  }

  async request(method, url, data = null, config = {}) {
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': this.token ? `Bearer ${this.token}` : ''
      },
      ...config
    };

    if (data && !config.responseType) {
      options.body = JSON.stringify(data);
    }

    if (config.params) {
      const params = new URLSearchParams(config.params).toString();
      url += `?${params}`;
    }

    try {
      const response = await fetch(`${this.baseURL}${url}`, options);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`HTTP ${response.status}: ${errorData.message || response.statusText}`);
      }

      return {
        data: await response.json(),
        status: response.status,
        headers: response.headers
      };
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  async batchRequest(requests) {
    try {
      const responses = await Promise.allSettled(
        requests.map(req => this.request(req.method, req.url, req.data, req.config))
      );
      
      return responses.map((res, index) => {
        if (res.status === 'fulfilled') {
          return { success: true, data: res.value };
        }
        return { success: false, error: res.reason };
      });
    } catch (error) {
      console.error('Batch request failed:', error);
      throw error;
    }
  }

  async retryRequest(method, url, data = null, config = {}, retries = 3) {
    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        return await this.request(method, url, data, config);
      } catch (error) {
        if (attempt === retries) throw error;
        
        const delay = Math.pow(2, attempt) * 1000;
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  async handleRateLimitError(error) {
    if (error.status === 429) {
      const retryAfter = error.headers.get('Retry-After') || 60;
      await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
      return true;
    }
    return false;
  }

  async handleNetworkError(error) {
    if (!navigator.onLine) {
      console.log('Network is offline, waiting for connection...');
      await new Promise(resolve => {
        const checkConnection = () => {
          if (navigator.onLine) {
            resolve();
          } else {
            setTimeout(checkConnection, 1000);
          }
        };
        checkConnection();
      });
      return true;
    }
    return false;
  }
}