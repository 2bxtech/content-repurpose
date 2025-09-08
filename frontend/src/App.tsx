import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Container } from '@mui/material';

// Enhanced context providers
import { AuthProvider } from './context/AuthContext';
import { CustomThemeProvider } from './context/ThemeContext';
import { NotificationProvider } from './context/NotificationContext';
import { AccessibilityProvider } from './context/AccessibilityProvider';
// import { WebSocketProvider } from './context/WebSocketContext'; // Will integrate in Session 2

// Enhanced components
import { ErrorBoundary } from './components/ErrorBoundary';
import NavBar from './components/NavBar';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import DocumentUpload from './pages/DocumentUpload';
import DocumentDetail from './pages/DocumentDetail';
import TransformationCreate from './pages/TransformationCreate';
import TransformationDetail from './pages/TransformationDetail';
// import AdminDashboard from './pages/AdminDashboard'; // Will create this next

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <AccessibilityProvider>
        <CustomThemeProvider>
          <AuthProvider>
            {/* WebSocket provider with auth integration - will be enhanced */}
            <NotificationProvider>
              <Router>
                <NavBar />
                <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
                  <Routes>
                    {/* Public routes */}
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    
                    {/* Protected routes */}
                    <Route
                      path="/"
                      element={
                        <ProtectedRoute>
                          <Dashboard />
                        </ProtectedRoute>
                      }
                    />
                    {/* Commented out until we create AdminDashboard
                    <Route
                      path="/admin"
                      element={
                        <ProtectedRoute>
                          <AdminDashboard />
                        </ProtectedRoute>
                      }
                    />
                    */}
                    <Route
                      path="/documents/upload"
                      element={
                        <ProtectedRoute>
                          <DocumentUpload />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/documents/:id"
                      element={
                        <ProtectedRoute>
                          <DocumentDetail />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/transformations/create/:documentId"
                      element={
                        <ProtectedRoute>
                          <TransformationCreate />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/transformations/:id"
                      element={
                        <ProtectedRoute>
                          <TransformationDetail />
                        </ProtectedRoute>
                      }
                    />
                    
                    {/* Fallback route */}
                    <Route path="*" element={<Navigate to="/" replace />} />
                  </Routes>
                </Container>
              </Router>
            </NotificationProvider>
          </AuthProvider>
        </CustomThemeProvider>
      </AccessibilityProvider>
    </ErrorBoundary>
  );
};

export default App;