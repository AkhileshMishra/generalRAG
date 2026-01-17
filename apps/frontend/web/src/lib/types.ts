export interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  citations?: Citation[]
}

export interface Citation {
  id: string
  title: string
  url?: string
  snippet: string
  documentId: string
}

export interface Session {
  id: string
  title: string
  createdAt: Date
  updatedAt: Date
  userId: string
  messages: Message[]
}

export interface User {
  id: string
  email: string
  name: string
  role: 'admin' | 'user'
  createdAt: Date
}

export interface Document {
  id: string
  filename: string
  title: string
  content: string
  uploadedAt: Date
  userId: string
  size: number
  type: string
}

export interface UploadFile {
  file: File
  progress: number
  status: 'pending' | 'uploading' | 'completed' | 'error'
  error?: string
}