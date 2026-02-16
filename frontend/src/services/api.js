/**
 * API service for EduVerse AI backend
 * Base URL: http://localhost:8000
 */

const API_BASE_URL = 'http://localhost:8000';

/**
 * Send a chat message to the backend
 * @param {string} mode - Chat mode (admissions, timetable, fees, regulations, general)
 * @param {string} query - User query
 * @returns {Promise<Object>} Response data
 */
export const sendChatMessage = async (mode, query) => {
  const response = await fetch(`${API_BASE_URL}/api/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      mode,
      query,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to send message');
  }

  return response.json();
};

/**
 * Upload a file to the backend
 * @param {File} file - File to upload
 * @param {string} category - Document category
 * @param {string} department - Academic department
 * @param {string} academicYear - Academic year
 * @returns {Promise<Object>} Response data
 */
export const uploadFile = async (file, category, department, academicYear) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('category', category);
  formData.append('department', department);
  formData.append('academic_year', academicYear);

  const response = await fetch(`${API_BASE_URL}/api/upload/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to upload file');
  }

  return response.json();
};

/**
 * Get today's timetable schedule
 * @returns {Promise<Array>} Today's schedule
 */
export const getTodaySchedule = async () => {
  const response = await fetch(`${API_BASE_URL}/api/timetable/today`, {
    method: 'GET',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch today\'s schedule');
  }

  return response.json();
};

/**
 * Get all admissions information
 * @returns {Promise<Array>} Admissions data
 */
export const getAdmissions = async () => {
  const response = await fetch(`${API_BASE_URL}/api/admissions`, {
    method: 'GET',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch admissions');
  }

  return response.json();
};

/**
 * Get all fee structures
 * @returns {Promise<Array>} Fee data
 */
export const getFees = async () => {
  const response = await fetch(`${API_BASE_URL}/api/fees`, {
    method: 'GET',
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch fees');
  }

  return response.json();
};

/**
 * Download template for a category
 * @param {string} category - Template category
 */
export const downloadTemplate = async (category) => {
  const response = await fetch(`${API_BASE_URL}/api/upload/download-template/${category}`, {
    method: 'GET',
  });

  if (!response.ok) {
    throw new Error('Failed to download template');
  }

  // Download file
  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${category}_template.xlsx`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
};

/**
 * Get template information for a category
 * @param {string} category - Template category
 * @returns {Promise<Object>} Template info
 */
export const getTemplateInfo = async (category) => {
  const response = await fetch(`${API_BASE_URL}/api/upload/template-info/${category}`, {
    method: 'GET',
  });

  if (!response.ok) {
    throw new Error('Failed to fetch template info');
  }

  return response.json();
};
