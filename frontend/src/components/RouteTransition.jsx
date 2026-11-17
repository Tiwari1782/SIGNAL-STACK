import React, { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import PageSkeleton from './PageSkeleton';

export default function RouteTransition({ children }) {
  const location = useLocation();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Trigger skeleton loader for at least 1000ms on every route change
    setLoading(true);
    const timer = setTimeout(() => {
      setLoading(false);
    }, 1000);

    return () => clearTimeout(timer);
  }, [location.pathname]);

  if (loading) {
    return <PageSkeleton />;
  }

  return <div className="page-fade-in">{children}</div>;
}
