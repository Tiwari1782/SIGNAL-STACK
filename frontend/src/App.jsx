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

  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <span className="sidebar-logo"><FiRadio /></span>
          <span className="sidebar-title">Signal Stack</span>
        </div>

        {company && (
          <div className="sidebar-company">
            <span className="sidebar-company-label">Active</span>
            <span className="sidebar-company-name">{company.name}</span>
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
                className={({ isActive }) =>
                  `sidebar-link${isActive ? ' sidebar-link--active' : ''}`
                }
              >
                <span className="sidebar-link-icon"><Icon /></span>
                <span>{item.label}</span>
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
