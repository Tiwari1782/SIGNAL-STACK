import { useState } from 'react';
import { Routes, Route, NavLink } from 'react-router-dom';
import {
  FiSliders,
  FiUserCheck,
  FiMessageSquare,
  FiLayers,
  FiLink2,
  FiActivity,
  FiFileText,
  FiSettings,
  FiRadio,
  FiChevronLeft,
  FiChevronRight,
  FiMenu,
} from 'react-icons/fi';
import SetupPage from './pages/SetupPage';
import ProfilePage from './pages/ProfilePage';
import InterviewPage from './pages/InterviewPage';
import SignalStackPage from './pages/SignalStackPage';
import SourcesPage from './pages/SourcesPage';
import FeedPage from './pages/FeedPage';
import BriefPage from './pages/BriefPage';
import SettingsPage from './pages/SettingsPage';
import { useCompany } from './context/CompanyContext';
import { ErrorBoundary } from './components/ErrorBoundary';
import './App.css';

const NAV_ITEMS = [
  { path: '/',             label: 'Setup',        Icon: FiSliders },
  { path: '/profile',      label: 'Profile',      Icon: FiUserCheck },
  { path: '/interview',    label: 'Interview',    Icon: FiMessageSquare },
  { path: '/signal-stack', label: 'Signal Stack', Icon: FiLayers },
  { path: '/sources',      label: 'Sources',      Icon: FiLink2 },
  { path: '/feed',         label: 'Feed',         Icon: FiActivity },
  { path: '/brief',        label: 'Brief',        Icon: FiFileText },
  { path: '/settings',     label: 'Settings',     Icon: FiSettings },
];

export default function App() {
  const { company } = useCompany();
  const [isOpen, setIsOpen] = useState(true);

  return (
    <div className={`app-layout ${isOpen ? 'sidebar-open' : 'sidebar-collapsed'}`}>
      <aside className={`sidebar ${isOpen ? 'sidebar--expanded' : 'sidebar--collapsed'}`}>
        <div className="sidebar-brand">
          <div className="sidebar-brand-main">
            <span className="sidebar-logo"><FiRadio /></span>
            {isOpen && <span className="sidebar-title">Signal Stack</span>}
          </div>
          <button
            type="button"
            className="sidebar-toggle-btn"
            onClick={() => setIsOpen(!isOpen)}
            title={isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
            aria-label={isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            {isOpen ? <FiChevronLeft /> : <FiChevronRight />}
          </button>
        </div>

        {company && (
          <div className="sidebar-company" title={company.name}>
            {isOpen ? (
              <>
                <span className="sidebar-company-label">Active</span>
                <span className="sidebar-company-name">{company.name}</span>
              </>
            ) : (
              <span className="sidebar-company-avatar">
                {company.name.charAt(0).toUpperCase()}
              </span>
            )}
          </div>
        )}

        <nav className="sidebar-nav">
          {NAV_ITEMS.map((item) => {
            const Icon = item.Icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                title={!isOpen ? item.label : undefined}
                className={({ isActive }) =>
                  `sidebar-link${isActive ? ' sidebar-link--active' : ''}`
                }
              >
                <span className="sidebar-link-icon"><Icon /></span>
                {isOpen && <span className="sidebar-link-text">{item.label}</span>}
              </NavLink>
            );
          })}
        </nav>
      </aside>

      <main className="main-content">
        <ErrorBoundary>
          <Routes>
            <Route path="/" element={<SetupPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/interview" element={<InterviewPage />} />
            <Route path="/signal-stack" element={<SignalStackPage />} />
            <Route path="/sources" element={<SourcesPage />} />
            <Route path="/feed" element={<FeedPage />} />
            <Route path="/brief" element={<BriefPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </ErrorBoundary>
      </main>
    </div>
  );
}
