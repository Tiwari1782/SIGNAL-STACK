import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiPlus, FiSearch, FiCheck, FiExternalLink, FiCheckSquare, FiSquare } from 'react-icons/fi';
import api from '../api';
import { useCompany } from '../context/CompanyContext';
import { useToast } from '../context/ToastContext';
import PageSkeleton from '../components/PageSkeleton';
import './SetupPage.css';

export default function SetupPage() {
  const [name, setName] = useState('');
  const [website, setWebsite] = useState('');
  const [companies, setCompanies] = useState([]);
  const [fetchingCompanies, setFetchingCompanies] = useState(true);
  const [loading, setLoading] = useState(false);
  const [researchingId, setResearchingId] = useState(null);
  const [error, setError] = useState('');
  const { company, setCompany } = useCompany();
  const toast = useToast();
  const navigate = useNavigate();

  useEffect(() => {
    fetchCompanies();
  }, []);

  async function fetchCompanies() {
    setFetchingCompanies(true);
    try {
      const res = await api.get('/companies');
      setCompanies(res.data);
      // If no company is selected yet and companies exist, select the first one
      if (!company && res.data.length > 0) {
        setCompany(res.data[0]);
      }
    } catch (err) {
      console.error('Failed to load companies', err);
      toast.error('Failed to connect to database to fetch companies.');
    } finally {
      setFetchingCompanies(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!name.trim() || !website.trim()) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.post('/companies', { name: name.trim(), website: website.trim() });
      setCompanies((prev) => [...prev, res.data]);
      setCompany(res.data);
      toast.success(`Registered ${res.data.name} successfully!`);
      setName('');
      setWebsite('');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Failed to create company';
      setError(msg);
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  }

  async function handleResearch(companyItem) {
    setResearchingId(companyItem.id);
    setError('');
    toast.info(`Crawling ${companyItem.name} site & running AI fact extraction...`, 6000);
    try {
      await api.post(`/companies/${companyItem.id}/research`);
      setCompany(companyItem);
      toast.success(`Research complete for ${companyItem.name}! Facts extracted.`);
      navigate('/profile');
    } catch (err) {
      const msg = err.response?.data?.detail || 'Research crawl failed';
      setError(msg);
      toast.error(msg);
    } finally {
      setResearchingId(null);
    }
  }

  function handleSelectCompany(companyItem) {
    setCompany(companyItem);
    toast.info(`Switched active organization to ${companyItem.name}`);
  }

  if (fetchingCompanies) {
    return <PageSkeleton />;
  }

  return (
    <div className="setup-page">
      <h1>Company Setup</h1>
      <p className="setup-subtitle">Select or add a company to run AI-powered research and calibrate intelligence.</p>

      <form className="setup-form card" onSubmit={handleSubmit}>
        <div className="setup-form-fields">
          <div className="form-group">
            <label htmlFor="company-name">Company / University Name</label>
            <input
              id="company-name"
              type="text"
              placeholder="e.g. MeetUniversity"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="company-website">Website URL</label>
            <input
              id="company-website"
              type="url"
              placeholder="https://www.meetuniversity.com"
              value={website}
              onChange={(e) => setWebsite(e.target.value)}
              required
            />
          </div>
        </div>
        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? <><span className="spinner" /> Adding…</> : <><FiPlus /> Add Company</>}
        </button>
      </form>

      {error && <div className="setup-error">{error}</div>}

      <h2>Registered Companies</h2>
      {companies.length === 0 ? (
        <p className="setup-empty">No companies yet. Add one above to get started.</p>
      ) : (
        <div className="setup-company-grid">
          {companies.map((c) => {
            const isSelected = company?.id === c.id;

            return (
              <div
                key={c.id}
                className={`card setup-company-card ${isSelected ? 'setup-company-card--active' : ''}`}
                onClick={() => handleSelectCompany(c)}
              >
                <div className="setup-company-card-header">
                  <div className="company-selection-check-wrap">
                    <button
                      type="button"
                      className={`company-check-btn ${isSelected ? 'company-check-btn--checked' : ''}`}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelectCompany(c);
                      }}
                      title={isSelected ? 'Active Company' : 'Click to select this company'}
                    >
                      {isSelected ? <FiCheckSquare /> : <FiSquare />}
                    </button>
                    <h3>{c.name}</h3>
                  </div>

                  {isSelected && (
                    <span className="badge badge-verified">
                      <FiCheck style={{ marginRight: 3 }} /> Selected
                    </span>
                  )}
                </div>

                <a
                  href={c.website}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="setup-company-url"
                  onClick={(e) => e.stopPropagation()}
                >
                  {c.website} <FiExternalLink style={{ fontSize: '12px', marginLeft: '4px' }} />
                </a>

                <span className="setup-company-date">
                  Registered {new Date(c.created_at).toLocaleDateString()}
                </span>

                <button
                  className="btn-primary setup-research-btn"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleResearch(c);
                  }}
                  disabled={researchingId === c.id}
                >
                  {researchingId === c.id ? (
                    <><span className="spinner" /> Researching…</>
                  ) : (
                    <><FiSearch /> Run AI Research</>
                  )}
                </button>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
