import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { AuthPage } from './pages/AuthPage';
import { HomePage } from './pages/HomePage';
import { CreateClassPage } from './pages/CreateClassPage';
import { ClassDetailPage } from './pages/ClassDetailPage';
import { PresentationViewPage } from './pages/PresentationViewPage';
import { InstanceReportPage } from './pages/InstanceReportPage';
import { Loader2 } from 'lucide-react';
import './App.css';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/auth" replace />;
  }

  return children;
};

function AppRoutes() {
  return (
    <Routes>
      {/* Auth Route */}
      <Route path="/auth" element={<AuthPage />} />

      {/* Protected Routes */}
      <Route
        path="/home"
        element={
          <ProtectedRoute>
            <HomePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/classes/create"
        element={
          <ProtectedRoute>
            <CreateClassPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/classes/:classId"
        element={
          <ProtectedRoute>
            <ClassDetailPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/classes/:classId/start"
        element={
          <ProtectedRoute>
            <PresentationViewPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/classes/:classId/instances/:instanceId"
        element={
          <ProtectedRoute>
            <InstanceReportPage />
          </ProtectedRoute>
        }
      />

      {/* Redirect to auth for unknown routes */}
      <Route path="*" element={<Navigate to="/auth" replace />} />
    </Routes>
  );
}

function App() {
  return (
    <AuthProvider>
      <Router
        future={{
          v7_startTransition: true,
          v7_relativeSplatPath: true,
        }}
      >
        <AppRoutes />
      </Router>
    </AuthProvider>
  );
}

export default App;
