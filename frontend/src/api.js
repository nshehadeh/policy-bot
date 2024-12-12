import axios from 'axios';
// import { useNavigate } from 'react-router-dom';

const api = axios.create({
  baseURL: '/api',  // Set your API base URL here
});
/*
// Request interceptor to add the token to every request
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token');  // Get the token from local storage
    if (token) {
      config.headers.Authorization = `Token ${token}`;  // Attach the token to the Authorization header
    }
    return config;
  },
  error => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors globally
api.interceptors.response.use(
  response => response,  // Return the response directly if it's successful
  error => {
    if (error.response && error.response.status === 401) {  // Check if the status is 401 Unauthorized
      const navigate = useNavigate();  // Use the navigate hook from react-router-dom
      alert('Your session has expired or you are no longer authenticated. Please log in again.');
      localStorage.removeItem('token');  // Remove the token from local storage
      navigate('/login');  // Redirect to the login screen
    }
    return Promise.reject(error);  // Reject the promise to pass the error to the next handler
  }
);
*/
export default api;

