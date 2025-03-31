// User and Authentication types
export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
}

export interface UserLogin {
  email: string;
  password: string;
}

export interface UserRegister extends UserLogin {
  username: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}

// Document types
export enum DocumentStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed"
}

export interface Document {
  id: number;
  user_id: number;
  title: string;
  description?: string;
  file_path: string;
  original_filename: string;
  content_type: string;
  status: DocumentStatus;
  created_at: string;
  updated_at: string;
}

export interface DocumentList {
  documents: Document[];
  count: number;
}

// Transformation types
export enum TransformationType {
  BLOG_POST = "blog_post",
  SOCIAL_MEDIA = "social_media",
  EMAIL_SEQUENCE = "email_sequence",
  NEWSLETTER = "newsletter",
  SUMMARY = "summary",
  CUSTOM = "custom"
}

export enum TransformationStatus {
  PENDING = "pending",
  PROCESSING = "processing",
  COMPLETED = "completed",
  FAILED = "failed"
}

export interface TransformationParameters {
  [key: string]: any;
}

export interface Transformation {
  id: number;
  user_id: number;
  document_id: number;
  transformation_type: TransformationType;
  parameters: TransformationParameters;
  status: TransformationStatus;
  result?: string;
  created_at: string;
  updated_at: string;
}

export interface TransformationList {
  transformations: Transformation[];
  count: number;
}

export interface TransformationCreate {
  document_id: number;
  transformation_type: TransformationType;
  parameters: TransformationParameters;
}