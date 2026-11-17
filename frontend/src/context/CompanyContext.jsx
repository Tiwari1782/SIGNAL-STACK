import { createContext, useContext, useState, useEffect } from 'react';
import api from '../api';

const CompanyContext = createContext(null);

export function CompanyProvider({ children }) {
  const [company, setCompanyState] = useState(() => {
    try {
      const saved = localStorage.getItem('signal_stack_active_company');
      return saved ? JSON.parse(saved) : null;
    } catch {
      return null;
    }
  });

  const [loadingCompany, setLoadingCompany] = useState(!company);

  useEffect(() => {
    // If no company in localStorage or to ensure fresh data, fetch from backend
    async function initCompany() {
      try {
        const res = await api.get('/companies');
        if (res.data && res.data.length > 0) {
          setCompanyState((prev) => {
            if (prev) {
              // verify it still exists in fresh list
              const found = res.data.find((c) => c.id === prev.id);
              if (found) return found;
            }
            const defaultComp = res.data[0];
            try {
              localStorage.setItem('signal_stack_active_company', JSON.stringify(defaultComp));
            } catch {}
            return defaultComp;
          });
        }
      } catch (err) {
        console.error('Failed to init company', err);
      } finally {
        setLoadingCompany(false);
      }
    }

    initCompany();
  }, []);

  const setCompany = (comp) => {
    setCompanyState(comp);
    try {
      if (comp) {
        localStorage.setItem('signal_stack_active_company', JSON.stringify(comp));
      } else {
        localStorage.removeItem('signal_stack_active_company');
      }
    } catch {}
  };

  return (
    <CompanyContext.Provider value={{ company, setCompany, loadingCompany }}>
      {children}
    </CompanyContext.Provider>
  );
}

export function useCompany() {
  const ctx = useContext(CompanyContext);
  if (!ctx) throw new Error('useCompany must be used inside CompanyProvider');
  return ctx;
}
