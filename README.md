# Content Repurposing Tool

A full-stack application that helps users repurpose content into different formats using AI assistance.

## Project Overview

This application consists of:

1. **Backend API (FastAPI)**
   - Document upload and processing
   - Claude API integration for content analysis 
   - Basic user authentication
   - Content transformation endpoints

2. **Frontend (React + TypeScript)**
   - Document upload interface
   - Format selection component
   - Preview and editing area
   - Export functionality

## Getting Started

### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with the required configuration (see .env.example)

4. Run the FastAPI server:
   ```
   uvicorn main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Start the React development server:
   ```
   npm start
   ```

## Features

- User authentication and account management
- Upload various document types (PDF, DOCX, TXT, MD)
- Transform content into different formats:
  - Blog posts
  - Social media content
  - Email sequences
  - Newsletters
  - Summaries
  - Custom formats
- Edit and refine generated content
- Export content in different formats