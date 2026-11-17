import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  FiActivity,
  FiFilter,
  FiTrendingUp,
  FiAlertTriangle,
  FiCheckCircle,
  FiHelpCircle,
  FiExternalLink,
  FiShield,
  FiAward,
  FiClock,
  FiCompass,
  FiLayers,
  FiSearch,
  FiRefreshCw,
  FiUploadCloud,
} from 'react-icons/fi';
import api from '../api';
import { useCompany } from '../context/CompanyContext';
import UploadModal from '../components/UploadModal';
import './FeedPage.css';

const IMPACT_COLORS = {
  opportunity: { label: 'Opportunity', cls: 'badge-opportunity' },
  threat:      { label: 'Threat',      cls: 'badge-threat' },
  neutral:     { label: 'Neutral',     cls: 'badge-neutral' },
};

const VERIF_META = {
  verified:      { label: 'Verified (2+ sources / official)', cls: 'badge-verified' },
  single_source: { label: 'Single Source',                   cls: 'badge-founder' },
  unverified:    { label: 'Unverified / Speculative',         cls: 'badge-assumed' },
};

export default function FeedPage() {
  const { company } = useCompany();
  const [data, setData] = useState({ signals: [], stats: {}, competitors: [] });
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [filters, setFilters] = useState({
    category: 'all',
    competitor: 'all',
    impact: 'all',
    verification: 'all',
    minRelevance: '',
    from: '',
    to: ''
  });

  const loadFeed = useCallback(async () => {
    if (!company) return;
    setLoading(true);
    try {
      let queryStr = `category=${filters.category}&competitor=${filters.competitor}&impact=${filters.impact}&verification=${filters.verification}`;
      if (filters.minRelevance) queryStr += `&min_relevance=${filters.minRelevance}`;
      if (filters.from) queryStr += `&from=${filters.from}`;
      if (filters.to) queryStr += `&to=${filters.to}`;

      const res = await api.get(`/companies/${company.id}/feed?${queryStr}`);
      setData(res.data);
    } catch (err) {
      console.error('Failed to load feed', err);
    } finally {
      setLoading(false);
    }
  }, [company, filters]);

  useEffect(() => {
    loadFeed();
  }, [loadFeed]);

  async function handleTriggerAnalysis() {
    if (!company || analyzing) return;
    setAnalyzing(true);
    try {
      await api.post(`/companies/${company.id}/analyze`);
      await loadFeed();
    } catch (err) {
      console.error('Failed to trigger analysis', err);
    } finally {
      setAnalyzing(false);
    }
  }

  function handleFilterChange(field, val) {
    setFilters((prev) => ({ ...prev, [field]: val }));
  }

  function resetFilters() {
    setFilters({
      category: 'all',
      competitor: 'all',
      impact: 'all',
      verification: 'all',
      minRelevance: '',
      from: '',
      to: ''
    });
  }

  if (!company) {
    return (
      <div className="feed-page">
        <h1>Intelligence Feed</h1>
        <div className="card feed-empty">
          <p>No active company selected. Please setup a company first.</p>
          <Link to="/" className="btn-primary">Go to Setup</Link>
        </div>
      </div>
    );
  }

  const { signals = [], stats = {}, competitors = [] } = data;

  return (
    <div className="feed-page">
      {/* Header */}
      <div className="feed-header">
        <div>
          <h1>Intelligence Feed</h1>
          <p className="feed-subtitle">
            Ranked, decision-relevant business developments monitored for <strong>{company.name}</strong>.
          </p>
        </div>

        <div className="feed-header-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={() => setShowUploadModal(true)}
          >
            <FiUploadCloud /> Upload Internal Intel
          </button>

          <button
            className="btn-primary"
            onClick={handleTriggerAnalysis}
            disabled={analyzing}
          >
            {analyzing ? (
              <><span className="spinner" /> Analyzing Ingested Docs…</>
            ) : (
              <><FiRefreshCw /> Analyze New Documents</>
            )}
          </button>
        </div>
      </div>

      {/* Stats Counter Bar */}
      <div className="feed-stats-grid">
        <div className="card stat-card">
          <span className="stat-label">Total Signals</span>
          <span className="stat-number">{stats.total_signals || 0}</span>
        </div>
        <div className="card stat-card">
          <span className="stat-label">Opportunities</span>
          <span className="stat-number stat-opp">{stats.opportunities || 0}</span>
        </div>
        <div className="card stat-card">
          <span className="stat-label">Threats & Risks</span>
          <span className="stat-number stat-threat">{stats.threats || 0}</span>
        </div>
        <div className="card stat-card">
          <span className="stat-label">Verified Signals</span>
          <span className="stat-number stat-verified">{stats.verified_count || 0}</span>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="card feed-filters-card">
        <div className="filters-row">
          <div className="filter-item">
            <label>Category</label>
            <select
              value={filters.category}
              onChange={(e) => handleFilterChange('category', e.target.value)}
            >
              <option value="all">All Categories</option>
              <option value="customers">Customers</option>
              <option value="competitors">Competitors</option>
              <option value="market">Market & Regulatory</option>
              <option value="internal">Internal</option>
            </select>
          </div>

          <div className="filter-item">
            <label>Impact Type</label>
            <select
              value={filters.impact}
              onChange={(e) => handleFilterChange('impact', e.target.value)}
            >
              <option value="all">All Impacts</option>
              <option value="opportunity">Opportunities</option>
              <option value="threat">Threats</option>
              <option value="neutral">Neutral</option>
            </select>
          </div>

          <div className="filter-item">
            <label>Verification</label>
            <select
              value={filters.verification}
              onChange={(e) => handleFilterChange('verification', e.target.value)}
            >
              <option value="all">All Statuses</option>
              <option value="verified">Verified Only</option>
              <option value="single_source">Single Source</option>
              <option value="unverified">Unverified</option>
            </select>
          </div>

          {competitors.length > 0 && (
            <div className="filter-item">
              <label>Competitor</label>
              <select
                value={filters.competitor}
                onChange={(e) => handleFilterChange('competitor', e.target.value)}
              >
                <option value="all">All Competitors</option>
                {competitors.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
          )}

          <div className="filter-item">
            <label>Min Strategic Relevance</label>
            <select
              value={filters.minRelevance}
              onChange={(e) => handleFilterChange('minRelevance', e.target.value)}
            >
              <option value="">Any Relevance</option>
              <option value="0.7">70% and above</option>
              <option value="0.8">80% and above</option>
              <option value="0.9">90% and above</option>
            </select>
          </div>

          <button className="btn-secondary filter-reset-btn" onClick={resetFilters}>
            Reset Filters
          </button>
        </div>
      </div>

      {/* Signals Feed List */}
      {loading ? (
        <div className="card feed-loading">
          <span className="spinner" />
          <p>Auditing and ranking signals…</p>
        </div>
      ) : signals.length === 0 ? (
        <div className="card feed-empty">
          <p>No signals matched your criteria.</p>
          <button className="btn-primary" onClick={handleTriggerAnalysis} disabled={analyzing}>
            Analyze Ingested Documents
          </button>
        </div>
      ) : (
        <div className="signals-list">
          {signals.map((sig) => {
            const impactMeta = IMPACT_COLORS[sig.impact_type] || IMPACT_COLORS.neutral;
            const verifMeta = VERIF_META[sig.verification_status] || VERIF_META.single_source;
            const rankScore100 = Math.round((sig.rank_score || 0) * 100);

            return (
              <div key={sig.id} className="card signal-feed-card">
                {/* Header Metadata */}
                <div className="signal-card-header">
                  <div className="signal-badges-group">
                    <span className="badge badge-category">{sig.category}</span>
                    {sig.competitor_name && (
                      <span className="badge badge-competitor">
                        ⚔️ {sig.competitor_name}
                      </span>
                    )}
                    <span className={`badge ${impactMeta.cls}`}>
                      {impactMeta.label}
                    </span>
                    <span className={`badge ${verifMeta.cls}`}>
                      {verifMeta.label}
                    </span>
                  </div>

                  {/* Rank Score Pill */}
                  <div className="signal-rank-badge" title={sig.rank_explanation}>
                    <FiAward style={{ marginRight: 4 }} />
                    <span>Rank: <strong>{rankScore100}</strong>/100</span>
                  </div>
                </div>

                {/* What Happened (Headline) */}
                <h3 className="signal-headline">{sig.what_happened}</h3>

                {/* Evidence Snippet (Anti-Fabrication Verbatim Quote) */}
                <div className="signal-evidence-box">
                  <div className="evidence-label-row">
                    <span className="evidence-label">
                      <FiCheckCircle style={{ marginRight: 4, color: 'var(--secondary)' }} />
                      Verified Source Evidence (Verbatim):
                    </span>
                    <a
                      href={sig.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="evidence-source-link"
                    >
                      Original Source <FiExternalLink style={{ fontSize: 11, marginLeft: 2 }} />
                    </a>
                  </div>
                  <blockquote className="evidence-quote">
                    "{sig.evidence_snippet}"
                  </blockquote>
                </div>

                {/* Strategic Implications & Interpretation */}
                <div className="signal-analysis-grid">
                  <div className="analysis-box">
                    <span className="analysis-label">Why It Matters for Leadership:</span>
                    <p className="analysis-text">{sig.why_it_matters}</p>
                  </div>

                  {sig.interpretation && (
                    <div className="analysis-box interpretation-box">
                      <span className="analysis-label">
                        <FiCompass style={{ marginRight: 4 }} /> Strategic Thesis & Industry Signal:
                      </span>
                      <p className="analysis-text">{sig.interpretation}</p>
                    </div>
                  )}
                </div>

                {/* Recommended Action & Affected Area */}
                <div className="signal-footer-row">
                  <div className="signal-action-item">
                    <span className="footer-label">Recommended Action:</span>
                    <span className="footer-val-action">{sig.suggested_action}</span>
                  </div>

                  <div className="signal-action-item">
                    <span className="footer-label">Business Area:</span>
                    <span className="badge badge-founder">{sig.business_area || 'Strategy'}</span>
                  </div>

                  <div className="signal-action-item">
                    <span className="footer-label">Urgency:</span>
                    <span className={`badge urgency-${sig.urgency || 'medium'}`}>
                      {sig.urgency ? sig.urgency.toUpperCase() : 'MEDIUM'}
                    </span>
                  </div>
                </div>

                {/* Multi-Factor Ranking Explanation */}
                <div className="signal-rank-explanation-bar">
                  <span className="rank-expl-text">
                    <strong>Ranking Rationale:</strong> {sig.rank_explanation}
                  </span>
                  <div className="rank-sub-metrics">
                    <span>Relevance: {Math.round((sig.strategic_relevance || 0.8) * 100)}%</span>
                    <span>•</span>
                    <span>Credibility: {Math.round((sig.source_reliability || 0.8) * 100)}%</span>
                    <span>•</span>
                    <span>Evidence: {Math.round((sig.evidence_strength || 0.8) * 100)}%</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <UploadModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        companyId={company.id}
        onSuccess={() => {
          handleFilterChange('category', 'internal');
          loadFeed();
        }}
      />
    </div>
  );
}
