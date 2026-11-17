import axios from 'axios';

const rawBase = import.meta.env.VITE_API_URL
  ? import.meta.env.VITE_API_URL.replace(/\/+$/, '')
  : '';

const api = axios.create({
  baseURL: rawBase ? `${rawBase}/api` : '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
