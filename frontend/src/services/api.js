import axios from 'axios';

const api = axios.create({
  baseURL: '/api',  // Set your API base URL here
});

export default api;

