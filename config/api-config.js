export const API_ENDPOINTS = {
  // 基础API
  BASE_URL: 'https://api.ap-learning.com/v1',
  
  // 用户相关
  USER_PROFILE: '/user/profile',
  USER_SETTINGS: '/user/settings',
  USER_GOALS: '/user/goals',
  USER_SUBJECTS: '/user/subjects',
  
  // 学习数据
  LEARNING_PROGRESS: '/learning/progress',
  PREDICTION_ANALYSIS: '/learning/predict',
  KNOWLEDGE_MAP: '/learning/knowledge-map',
  
  // 考试相关
  EXAM_SCHEDULE: '/exams/schedule',
  EXAM_PREDICTIONS: '/exams/predictions',
  EXAM_ANALYSIS: '/exams/analysis',
  
  // 题库
  QUESTION_BANK: '/questions/bank',
  PRACTICE_SESSIONS: '/questions/practice',
  MOCK_EXAMS: '/questions/mock',
  
  // AI助手
  AI_ASSISTANT: '/ai/assistant',
  AI_GENERATE_QUESTIONS: '/ai/generate-questions',
  AI_ANALYSIS: '/ai/analysis',
  
  // 统计分析
  ANALYTICS_DASHBOARD: '/analytics/dashboard',
  PERFORMANCE_TRENDS: '/analytics/trends',
  COMPARISON_REPORTS: '/analytics/comparison',
  
  // 实时数据
  REALTIME_METRICS: '/realtime/metrics',
  PROGRESS_UPDATES: '/realtime/progress',
  NOTIFICATIONS: '/realtime/notifications'
};

export const MODEL_CONFIG = {
  // 预测模型
  PREDICTION_MODELS: {
    SCORE_PREDICTION: 'score_prediction_v2',
    MASTERY_PREDICTION: 'mastery_prediction_v1',
    TREND_ANALYSIS: 'trend_analysis_v1'
  },
  
  // 知识点模型
  KNOWLEDGE_MODELS: {
    CONCEPT_MAPPING: 'concept_mapping_v2',
    SKILL_DETECTION: 'skill_detection_v1',
    WEAKNESS_IDENTIFICATION: 'weakness_identification_v1'
  },
  
  // 推荐模型
  RECOMMENDATION_MODELS: {
    STUDY_PLAN_RECOMMENDATION: 'study_plan_recommendation_v2',
    QUESTION_RECOMMENDATION: 'question_recommendation_v1',
    RESOURCE_RECOMMENDATION: 'resource_recommendation_v1'
  },
  
  // AI助手模型
  AI_ASSISTANT_MODELS: {
    CHAT_ASSISTANT: 'chat_assistant_v2',
    EXPLANATION_GENERATOR: 'explanation_generator_v1',
    FEEDBACK_PROVIDER: 'feedback_provider_v1'
  },
  
  // 参数配置
  PARAMETERS: {
    // 预测准确度阈值
    PREDICTION_CONFIDENCE_THRESHOLD: 0.75,
    
    // 知识点更新频率
    KNOWLEDGE_UPDATE_INTERVAL: 300000, // 5分钟
    
    // 推荐更新频率
    RECOMMENDATION_UPDATE_INTERVAL: 600000, // 10分钟
    
    // AI助手响应时间
    AI_RESPONSE_TIMEOUT: 8000, // 8秒
    
    // 数据缓存时间
    DATA_CACHE_TTL: 1800000, // 30分钟
    
    // 批量请求大小
    BATCH_REQUEST_SIZE: 50
  }
};

export const AUTH_CONFIG = {
  // 认证方式
  AUTH_METHODS: {
    TOKEN: 'token',
    OAUTH2: 'oauth2',
    SAML: 'saml',
    LDAP: 'ldap'
  },
  
  // 权限级别
  PERMISSIONS: {
    STUDENT: 'student',
    TEACHER: 'teacher',
    ADMIN: 'admin',
    VIEWER: 'viewer'
  },
  
  // 角色权限
  ROLE_PERMISSIONS: {
    student: ['view_progress', 'practice_questions', 'view_predictions'],
    teacher: ['view_progress', 'practice_questions', 'view_predictions', 'manage_students', 'view_analytics'],
    admin: ['view_progress', 'practice_questions', 'view_predictions', 'manage_students', 'view_analytics', 'manage_content', 'system_settings'],
    viewer: ['view_progress', 'view_predictions']
  }
};

export const ERROR_HANDLING = {
  // 错误码
  ERROR_CODES: {
    NETWORK_ERROR: 'network_error',
    AUTH_ERROR: 'auth_error',
    VALIDATION_ERROR: 'validation_error',
    SERVER_ERROR: 'server_error',
    TIMEOUT_ERROR: 'timeout_error',
    RATE_LIMIT_ERROR: 'rate_limit_error'
  },
  
  // 重试配置
  RETRY_CONFIG: {
    MAX_RETRIES: 3,
    BASE_DELAY: 1000,
    MAX_DELAY: 30000,
    EXPONENTIAL_BACKOFF: true
  },
  
  // 超时配置
  TIMEOUT_CONFIG: {
    API_TIMEOUT: 30000,
    AI_TIMEOUT: 15000,
    FILE_UPLOAD_TIMEOUT: 60000
  }
};

export const DATA_VALIDATION = {
  // 数据验证规则
  VALIDATION_RULES: {
    EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, 
    PASSWORD: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$/,
    USERNAME: /^[a-zA-Z0-9_]{3,20}$/,
    PHONE: /^\+?[1-9]\d{1,14}$/
  },
  
  // 数据格式
  DATA_FORMATS: {
    DATE: 'YYYY-MM-DD',
    DATETIME: 'YYYY-MM-DD HH:mm:ss',
    TIME: 'HH:mm:ss',
    TIMESTAMP: 'x' // Unix时间戳
  }
};

export const LOGGING_CONFIG = {
  // 日志级别
  LOG_LEVELS: {
    DEBUG: 'debug',
    INFO: 'info',
    WARN: 'warn',
    ERROR: 'error',
    FATAL: 'fatal'
  },
  
  // 日志配置
  LOG_CONFIG: {
    ENABLE_DEBUG: false,
    ENABLE_API_LOGGING: true,
    ENABLE_ERROR_REPORTING: true,
    LOG_TO_CONSOLE: true,
    LOG_TO_SERVER: true,
    LOG_LEVEL: 'info'
  }
};

export const PERFORMANCE_METRICS = {
  // 性能指标
  METRICS: {
    API_RESPONSE_TIME: 'api_response_time',
    API_SUCCESS_RATE: 'api_success_rate',
    PAGE_LOAD_TIME: 'page_load_time',
    USER_INTERACTION_TIME: 'user_interaction_time',
    MEMORY_USAGE: 'memory_usage',
    CPU_USAGE: 'cpu_usage'
  },
  
  // 性能阈值
  THRESHOLDS: {
    API_RESPONSE_TIME: 2000, // 2秒
    PAGE_LOAD_TIME: 3000, // 3秒
    USER_INTERACTION_TIME: 500, // 0.5秒
    MEMORY_USAGE: 500, // 500MB
    CPU_USAGE: 80 // 80%
  }
};