import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '',
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// Auth
export const register = (data) => api.post('/auth/register', data);
export const login = (data) => api.post('/auth/login', data);

// Clients
export const getClients = () => api.get('/clients');
export const getClient = (id) => api.get(`/clients/${id}`);
export const createClient = (data) => api.post('/clients', data);
export const updateClient = (id, data) => api.put(`/clients/${id}`, data);
export const deleteClient = (id) => api.delete(`/clients/${id}`);

// Projects
export const getProjects = () => api.get('/projects');
export const getProject = (id) => api.get(`/projects/${id}`);
export const createProject = (data) => api.post('/projects', data);
export const updateProject = (id, data) => api.put(`/projects/${id}`, data);
export const deleteProject = (id) => api.delete(`/projects/${id}`);

// Time Logs
export const getTimeLogs = (projectId) => api.get(`/projects/${projectId}/timelogs`);
export const createTimeLog = (projectId, data) => api.post(`/projects/${projectId}/timelogs`, data);
export const updateTimeLog = (projectId, id, data) => api.put(`/timelogs/${id}`, data);
export const deleteTimeLog = (projectId, id) => api.delete(`/timelogs/${id}`);

// Timer
export const startTimer = (data) => api.post('/timer/start', data);
export const stopTimer = (timerId) => api.post(`/timer/stop/${timerId}`);

// Invoices
export const getInvoices = () => api.get('/invoices');
export const getInvoice = (id) => api.get(`/invoices/${id}`);
export const generateInvoice = (data) => api.post(`/projects/${data.projectId}/invoice`, data);
export const deleteInvoice = (id) => api.delete(`/invoices/${id}`);

// Dashboard
export const getDashboard = () => api.get('/dashboard');

// Subscription
export const subscribe = (data) => api.post('/subscribe', data);
export const getSubscriberCount = () => api.get('/subscribers');

export default api;
