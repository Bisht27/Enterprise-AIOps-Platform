import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

export default function ProtectedRoute({
  children,
}: {
  children: ReactNode;
}) {
  const { isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  // Auth state is still resolving (initial /auth/me check on page load).
  // Render nothing yet -- redirecting now would incorrectly bounce a
  // genuinely-authenticated user to /login before we know the answer.
  if (isLoading) {
    return null;
  }

  if (!isAuthenticated) {
    // Preserve the page the user was trying to reach so Login.tsx can
    // send them back after a successful login (it already reads
    // location.state.from for this).
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}