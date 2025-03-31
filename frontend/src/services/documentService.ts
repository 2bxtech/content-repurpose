import api from './authService';
import { Document, DocumentList } from '../types';

// Document API calls
export const uploadDocument = async (formData: FormData): Promise<Document> => {
  const response = await api.post<Document>('/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getUserDocuments = async (): Promise<DocumentList> => {
  const response = await api.get<DocumentList>('/documents');
  return response.data;
};

export const getDocument = async (id: number): Promise<Document> => {
  const response = await api.get<Document>(`/documents/${id}`);
  return response.data;
};

export const deleteDocument = async (id: number): Promise<void> => {
  await api.delete(`/documents/${id}`);
};