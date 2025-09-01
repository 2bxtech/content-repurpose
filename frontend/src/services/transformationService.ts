import api from './authService';
import { Transformation, TransformationList, TransformationCreate } from '../types';

// Transformation API calls
export const createTransformation = async (transformationData: TransformationCreate): Promise<Transformation> => {
  const response = await api.post<Transformation>('/transformations', transformationData);
  return response.data;
};

export const getUserTransformations = async (): Promise<TransformationList> => {
  const response = await api.get<TransformationList>('/transformations');
  return response.data;
};

export const getTransformation = async (id: string): Promise<Transformation> => {
  const response = await api.get<Transformation>(`/transformations/${id}`);
  return response.data;
};

export const deleteTransformation = async (id: string): Promise<void> => {
  await api.delete(`/transformations/${id}`);
};

// Real-time status checking (fallback for non-WebSocket scenarios)
export const getTransformationStatus = async (id: string) => {
  const response = await api.get(`/transformations/${id}/status`);
  return response.data;
};

// Cancel transformation
export const cancelTransformation = async (id: string) => {
  const response = await api.post(`/transformations/${id}/cancel`);
  return response.data;
};

// Polling utility for status updates (fallback when WebSocket is not available)
export const pollTransformationStatus = (
  transformationId: string,
  onUpdate: (status: any) => void,
  onComplete: (finalStatus: any) => void,
  interval: number = 2000
) => {
  let polling = true;
  
  const poll = async () => {
    if (!polling) return;
    
    try {
      const status = await getTransformationStatus(transformationId);
      onUpdate(status);
      
      // Check if transformation is complete
      if (status.database_status === 'completed' || status.database_status === 'failed') {
        polling = false;
        onComplete(status);
        return;
      }
      
      // Continue polling
      setTimeout(poll, interval);
    } catch (error) {
      console.error('Error polling transformation status:', error);
      // Continue polling even on error, unless explicitly stopped
      if (polling) {
        setTimeout(poll, interval * 2); // Back off on error
      }
    }
  };
  
  // Start polling
  poll();
  
  // Return stop function
  return () => {
    polling = false;
  };
};