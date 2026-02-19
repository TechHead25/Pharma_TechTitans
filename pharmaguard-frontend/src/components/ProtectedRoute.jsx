import React from 'react';
import { Navigate } from 'react-router-dom';

export default function ProtectedRoute({ children, requiredRole = null }) {
  const token = localStorage.getItem('access_token');
  const user = JSON.parse(localStorage.getItem('user') || '{}');

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (requiredRole === 'admin' && !user.is_admin) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
}
