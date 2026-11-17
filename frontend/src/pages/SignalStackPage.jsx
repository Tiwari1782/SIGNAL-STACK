import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  FiLayers,
  FiCheck,
  FiCheckCircle,
  FiTrash2,
  FiExternalLink,
  FiRefreshCw,
  FiUsers,
  FiTarget,
  FiGlobe,
  FiFolder,
  FiAlertCircle,
  FiShield,
  FiAward,
  FiActivity
} from 'react-icons/fi';
import api from '../api';
import { useCompany } from '../context/CompanyContext';
import PageSkeleton from '../components/PageSkeleton';
import './SignalStackPage.css';

const TABS = [
  { key: 'all',         label: 'All Sources',   Icon: FiLayers },
  { key: 'customers',   label: 'Customers',     Icon: FiUsers },
  { key: 'competitors', label: 'Competitors',   Icon: FiTarget },
  { key: 'market',      label: 'Market & Regs', Icon: FiGlobe },
  { key: 'internal',    label: 'Internal',      Icon: FiFolder },
];

export default function SignalStackPage() {
  const { company, loadingCompany } = useCompany();
  const [loading, setLoading] = useState(true);
  const [building, setBuilding] = useState(false);
  const [crawling, setCrawling] = useState(false);
  const [crawlSummary, setCrawlSummary] = useState(null);
  const [approvingAll, setApprovingAll] = useState(false);
  const [actionId, setActionId] = useState(null);
  const [error, setError] = useState('');
  const [activeTab, setActiveTab] = useState('all');
  const [data, setData] = useState(null);

  const loadSignalStack = useCallback(async () => {
    if (!company) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.get(`/companies/${company.id}/signal-stack`);
      setData(res.data);
    } catch (err) {
      console.error('Failed to load Signal Stack', err);
      setError(err.response?.data?.detail || 'Failed to load Signal Stack');
    } finally {
      setLoading(false);
    }
  }, [company]);

  useEffect(() => {
    loadSignalStack();
  }, [loadSignalStack]);

  async function handleBuildStack() {
    if (!company || building) return;
    setBuilding(true);
    setError('');
    try {
      const res = await api.post(`/companies/${company.id}/signal-stack/build`);
      setData(res.data);
    } catch (err) {
      console.error('Failed to build Signal Stack', err);
      setError(err.response?.data?.detail || 'Failed to discover sources');
    } finally {
      setBuilding(false);
    }
  }

  async function handleCrawl() {
    if (!company || crawling) return;
    setCrawling(true);
    setError('');
    setCrawlSummary(null);
    try {
      const res = await api.post(`/companies/${company.id}/crawl`);
      setCrawlSummary(res.data);
      await loadSignalStack();
    } catch (err) {
      console.error('Failed to crawl sources', err);
      setError(err.response?.data?.detail || 'Crawl failed');
    } finally {
      setCrawling(false);
    }
  }

  async function handleApproveAll() {
    if (!company || approvingAll) return;
    setApprovingAll(true);
    try {
      await api.post(`/companies/${company.id}/sources/approve-all`);
      await loadSignalStack();
    } catch (err) {
      console.error('Failed to approve all', err);
      setError('Failed to approve all sources');
    } finally {
      setApprovingAll(false);
    }
  }

  async function handleApprove(sourceId) {
    setActionId(sourceId);
    try {
      await api.post(`/sources/${sourceId}/approve`);
      await loadSignalStack();
    } catch (err) {
      console.error('Failed to approve source', err);
    } finally {
      setActionId(null);
    }
  }

  async function handleRemove(sourceId) {
    setActionId(sourceId);
    try {
      await api.delete(`/sources/${sourceId}`);
      await loadSignalStack();
    } catch (err) {
      console.error('Failed to remove source', err);
    } finally {
      setActionId(null);
    }
  }

  if (loading || loadingCompany) {
    return <PageSkeleton />;
  }

  if (!company) {
    return (
      <div className="signal-stack-page">
        <h1>Signal Stack</h1>
        <div className="card signal-empty">
          <p>No company selected. Please setup a company first.</p>
          <Link to="/" className="btn-primary">Go to Setup</Link>
        </div>
      </div>
    );
  }

  const stats = data?.stats || { total_sources: 0, approved_count: 0, suggested_count: 0, competitor_count: 0 };
  const categories = data?.categories || { customers: [], competitors: [], market: [], internal: [] };

  const displayedSources =
    activeTab === 'all'
      ? [
          ...categories.customers,
          ...categories.competitors,
          ...categories.market,
          ...categories.internal,
        ]
      : categories[activeTab] || [];

  return (
    <div className="signal-stack-page">
      {/* Header & Controls */}
      <div className="stack-header">
        <div>
          <h1>Signal Stack</h1>
          <p className="stack-subtitle">
            Intelligence sensors monitoring <strong>{company.name}</strong> across Customers, Competitors, Market, and Internal.
          </p>
        </div>

        <div className="stack-actions">
          <button
            className="btn-primary"
            onClick={handleCrawl}
            disabled={crawling || stats.approved_count === 0}
            title="Crawl all approved sources for new documents"
          >
            {crawling ? (
              <><span className="spinner" /> Crawling Sensors…</>
            ) : (
              <><FiActivity /> Crawl Approved Sources</>
            )}
          </button>

          <button
            className="btn-secondary"
            onClick={handleBuildStack}
            disabled={building}
            title="Run dynamic web discovery with AI"
          >
            {building ? (
              <><span className="spinner" /> Discovering Sources…</>
            ) : (
              <><FiRefreshCw /> Run AI Discovery</>
            )}
          </button>

          {stats.suggested_count > 0 && (
            <button
              className="btn-secondary"
              onClick={handleApproveAll}
              disabled={approvingAll}
            >
              {approvingAll ? (
                <><span className="spinner" /> Approving…</>
              ) : (
                <><FiCheckCircle /> Approve All ({stats.suggested_count})</>
              )}
            </button>
          )}
        </div>
      </div>

      {crawlSummary && (
        <div className="card stack-crawl-banner">
          <FiCheckCircle className="crawl-banner-icon" />
          <div className="crawl-banner-text">
            <strong>Crawl Run Completed:</strong> {crawlSummary.total_sources} sensors checked,{' '}
            <span style={{ color: 'var(--secondary)', fontWeight: 700 }}>
              {crawlSummary.successful_crawls} successful
            </span>,{' '}
            {crawlSummary.failed_crawls > 0 && (
              <span style={{ color: 'var(--error)' }}>
                {crawlSummary.failed_crawls} blocked/failed,{' '}
              </span>
            )}
            <strong>{crawlSummary.new_documents_collected} new documents ingested</strong> with SHA-256 deduplication.
          </div>
          <button className="modal-close-btn" onClick={() => setCrawlSummary(null)}>
            ×
          </button>
        </div>
      )}

      {error && (
        <div className="stack-error">
          <FiAlertCircle style={{ flexShrink: 0, marginTop: 2 }} />
          <span>{error}</span>
        </div>
      )}

      {/* Stats Counter Bar */}
      <div className="stack-stats-grid">
        <div className="card stat-card">
          <span className="stat-label">Total Sensors</span>
          <span className="stat-number">{stats.total_sources}</span>
        </div>
        <div className="card stat-card">
          <span className="stat-label">Approved Sources</span>
          <span className="stat-number stat-approved">{stats.approved_count}</span>
        </div>
        <div className="card stat-card">
          <span className="stat-label">Suggested Sources</span>
          <span className="stat-number stat-suggested">{stats.suggested_count}</span>
        </div>
        <div className="card stat-card">
          <span className="stat-label">Competitors Monitored</span>
          <span className="stat-number stat-competitors">{stats.competitor_count}</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="stack-tabs">
        {TABS.map((tab) => {
          const Icon = tab.Icon;
          const count =
            tab.key === 'all'
              ? stats.total_sources
              : (categories[tab.key] || []).length;

          return (
            <button
              key={tab.key}
              className={`stack-tab-btn ${activeTab === tab.key ? 'stack-tab-btn--active' : ''}`}
              onClick={() => setActiveTab(tab.key)}
            >
              <Icon style={{ marginRight: 6 }} />
              <span>{tab.label}</span>
              <span className="stack-tab-count">{count}</span>
            </button>
          );
        })}
      </div>

      {/* Source Cards Grid */}
      {loading ? (
        <div className="card signal-loading">
          <span className="spinner" />
          <p>Loading Signal Stack sources…</p>
        </div>
      ) : displayedSources.length === 0 ? (
        <div className="card signal-empty">
          <p>No sources found in this category.</p>
          <button className="btn-primary" onClick={handleBuildStack} disabled={building}>
            Discover Sources Now
          </button>
        </div>
      ) : (
        <div className="sources-grid">
          {displayedSources.map((source) => {
            const isApproved = source.status === 'approved';
            const isBusy = actionId === source.id;

            return (
              <div
                key={source.id}
                className={`card source-card ${isApproved ? 'source-card--approved' : 'source-card--suggested'}`}
              >
                <div className="source-card-header">
                  <div className="source-title-group">
                    <span className="source-category-tag">{source.category}</span>
                    <h3 className="source-name">{source.name}</h3>
                  </div>

                  <span className={`badge ${isApproved ? 'badge-verified' : 'badge-assumed'}`}>
                    {isApproved ? (
                      <><FiCheck style={{ marginRight: 3 }} /> Approved</>
                    ) : (
                      'Suggested'
                    )}
                  </span>
                </div>

                {source.competitor_name && (
                  <div className="source-competitor-badge">
                    <FiTarget style={{ marginRight: 4 }} /> Competitor: <strong>{source.competitor_name}</strong>
                  </div>
                )}

                <a
                  href={source.url.startsWith('http') ? source.url : undefined}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="source-url"
                >
                  {source.url} {source.url.startsWith('http') && <FiExternalLink style={{ fontSize: 12, marginLeft: 4 }} />}
                </a>

                {/* Justification Reason */}
                <div className="source-reason-box">
                  <span className="source-reason-label">Reason for Inclusion:</span>
                  <p className="source-reason-text">{source.reason}</p>
                </div>

                {/* Metric Indicators */}
                <div className="source-metrics-row">
                  <div className="source-metric" title="Strategic relevance to business context">
                    <FiAward className="metric-icon" />
                    <span>Relevance: <strong>{Math.round((source.relevance_score || 0.8) * 100)}%</strong></span>
                  </div>

                  <div className="source-metric" title="Reliability & credibility of reporting entity">
                    <FiShield className="metric-icon" />
                    <span>Reliability: <strong>{Math.round((source.source_reliability || 0.8) * 100)}%</strong></span>
                  </div>
                </div>

                {/* Actions */}
                <div className="source-actions">
                  {!isApproved && (
                    <button
                      className="btn-primary source-action-btn"
                      onClick={() => handleApprove(source.id)}
                      disabled={isBusy}
                    >
                      {isBusy ? <span className="spinner" /> : <><FiCheck /> Approve</>}
                    </button>
                  )}

                  <button
                    className="btn-secondary source-dismiss-btn"
                    onClick={() => handleRemove(source.id)}
                    disabled={isBusy}
                    title="Dismiss or remove source"
                  >
                    <FiTrash2 /> Dismiss
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
