import { getCurrentUserToken } from '@/lib/firebase';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5000';

// Helper function to get auth headers
const getAuthHeaders = async () => {
  const token = await getCurrentUserToken();
  return {
    'Authorization': token ? `Bearer ${token}` : '',
  };
};

// Helper function to handle API responses
const handleResponse = async (response) => {
  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Error desconocido' }));
    throw new Error(error.error || error.message || `HTTP error! status: ${response.status}`);
  }
  return response.json();
};

// ============================================================================
// AUTH API
// ============================================================================

export const authAPI = {
  // Get current user profile
  getProfile: async () => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/auth/profile`, {
      headers,
    });
    return handleResponse(response);
  },

  // Get current user info
  getMe: async () => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/auth/me`, {
      headers,
    });
    return handleResponse(response);
  },
};

// ============================================================================
// CLASSES API
// ============================================================================

export const classesAPI = {
  // Get all classes
  getAll: async () => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/classes`, {
      headers,
    });
    return handleResponse(response);
  },

  // Get class by ID
  getById: async (classId) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/classes/${classId}`, {
      headers,
    });
    return handleResponse(response);
  },

  // Create new class
  create: async (formData) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/classes`, {
      method: 'POST',
      headers,
      body: formData, // FormData with file
    });
    return handleResponse(response);
  },

  // Update class
  update: async (classId, data) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/classes/${classId}`, {
      method: 'PUT',
      headers: {
        ...headers,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  // Delete class
  delete: async (classId) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/classes/${classId}`, {
      method: 'DELETE',
      headers,
    });
    return handleResponse(response);
  },
};

// ============================================================================
// INSTANCES API
// ============================================================================

export const instancesAPI = {
  // Get all instances for a class
  getAll: async (classId) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/classes/${classId}/instances`, {
      headers,
    });
    return handleResponse(response);
  },

  // Get instance by ID
  getById: async (classId, instanceId) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/classes/${classId}/instances/${instanceId}`, {
      headers,
    });
    return handleResponse(response);
  },

  // Create new instance (start class)
  create: async (classId) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/classes/${classId}/instances`, {
      method: 'POST',
      headers: {
        ...headers,
        'Content-Type': 'application/json',
      },
    });
    return handleResponse(response);
  },

  // Update instance
  update: async (classId, instanceId, data) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/classes/${classId}/instances/${instanceId}`, {
      method: 'PUT',
      headers: {
        ...headers,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },

  // End instance (with optional slide_flow and slide_times data)
  end: async (classId, instanceId, data = {}) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${API_URL}/api/classes/${classId}/instances/${instanceId}/end`, {
      method: 'POST',
      headers: {
        ...headers,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return handleResponse(response);
  },
};

// ============================================================================
// SYNC API (No authentication required - uses sync codes)
// ============================================================================

export const syncAPI = {
  // Get sync code for instance
  getSyncCode: async (classId, instanceId) => {
    const response = await fetch(`${API_URL}/api/sync/${classId}/${instanceId}/code`);
    return handleResponse(response);
  },

  // Get instance status by sync code
  getStatus: async (syncCode) => {
    const response = await fetch(`${API_URL}/api/sync/${syncCode}/status`);
    return handleResponse(response);
  },

  // Control presentation via sync code
  control: async (syncCode, action) => {
    const response = await fetch(`${API_URL}/api/sync/${syncCode}/control`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ action }),
    });
    return handleResponse(response);
  },

  // Update current slide from frontend
  updateSlide: async (syncCode, slideNumber) => {
    const response = await fetch(`${API_URL}/api/sync/${syncCode}/slide`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ slide: slideNumber }),
    });
    return handleResponse(response);
  },
};
