import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: `${API_BASE_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const setAuthToken = (token: string | null) => {
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete api.defaults.headers.common['Authorization'];
  }
};

export interface Resume {
  id: number;
  filename: string;
  file_path: string;
  parsed_data?: any;
  created_at: string;
  updated_at?: string;
}

export interface JobListing {
  id: string | number;
  title: string;
  company: string;
  description: string;
  requirements?: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  job_type?: string;
  remote?: string;
  url?: string;
  source?: string;
  skills_required?: string[];
  created_at?: string;
  updated_at?: string;
}

export interface JobMatch {
  id?: string | number;
  title: string;
  company: string;
  description: string;
  location?: string;
  salary_min?: number;
  salary_max?: number;
  job_type?: string;
  remote?: string;
  url?: string;
  source?: string;
  match_score: number;
  matching_skills: string[];
}

export interface LiveJobSearchRequest {
  resume_text: string;
  location?: string;
  max_jobs?: number;
  timeout?: number;
}

export interface LiveJobSearchResponse {
  jobs: JobMatch[];
  metadata: {
    total_fetched: number;
    open_jobs: number;
    valid_links: number;
    unique_jobs: number;
    returned: number;
    duration_seconds: number;
    sources_queried: number;
    timestamp: string;
  };
}

export const resumeApi = {
  uploadResume: (file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return api.post<Resume>('/resumes/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  getResumes: () => api.get<Resume[]>('/resumes/'),

  getResume: (id: number) => api.get<Resume>(`/resumes/${id}`),

  parseResume: (id: number) => api.post(`/resumes/${id}/parse`),

  deleteResume: (id: number) => api.delete(`/resumes/${id}`),
};

export const jobApi = {
  getJobs: (params?: {
    skip?: number;
    limit?: number;
    company?: string;
    location?: string;
    job_type?: string;
    remote?: string;
  }) => api.get<JobListing[]>('/jobs/', { params }),

  getJob: (id: number) => api.get<JobListing>(`/jobs/${id}`),

  createJob: (job: Omit<JobListing, 'id' | 'created_at' | 'updated_at'>) => 
    api.post<JobListing>('/jobs/', job),
};

export const liveJobApi = {
  searchLiveJobs: (request: LiveJobSearchRequest) => 
    api.post<LiveJobSearchResponse>('/jobs/live', request),

  healthCheck: () => api.get('/jobs/live/health'),

  prewarm: () => api.post('/jobs/live/prewarm'),
};

export const matchApi = {
  findMatches: (resumeId: number, limit?: number) => 
    api.post<JobMatch[]>(`/matches/${resumeId}`, {}, { params: { limit } }),

  getMatches: (resumeId: number) => 
    api.get<JobMatch[]>(`/matches/${resumeId}`),
};