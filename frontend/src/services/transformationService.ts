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

export const getTransformation = async (id: number): Promise<Transformation> => {
  const response = await api.get<Transformation>(`/transformations/${id}`);
  return response.data;
};

export const deleteTransformation = async (id: number): Promise<void> => {
  await api.delete(`/transformations/${id}`);
};