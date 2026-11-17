import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  FiLink2,
  FiPlus,
  FiCheck,
  FiTrash2,
  FiActivity,
  FiExternalLink,
  FiFilter,
  FiX,
  FiShield,
  FiAward,
  FiClock,
  FiFileText,
  FiRefreshCw
} from 'react-icons/fi';
import api from '../api';
import { useCompany } from '../context/CompanyContext';
import PageSkeleton from '../components/PageSkeleton';
import './SourcesPage.css';

export default function SourcesPage() {
  const { company, loadingCompany } = useCompany();
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [crawlingId, setCrawlingId] = useState(null);
  const [crawlingAll, setCrawlingAll] = useState(false);
  const [filterCat, setFilterCat] = useState('all');
  const [filterStatus, setFilterStatus] = useState('all');

  // Add source modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    url: '',
    category: 'competitors',
    reason: '',
    competitor_name: '',
    source_reliability: 0.8,
    relevance_score: 0.8,
  });
  const [adding, setAdding] = useState(false);

  // Health / History modal state
  const [historySource, setHistorySource] = useState(null);
  const [historyData, setHistoryData] = useState(null);
  const [loadingHistory, setLoadingHistory] = useState(false);

  const loadSources = useCallback(async () => {
    if (!company) return;
    setLoading(true);
    try {
      let url = `/companies/${company.id}/sources?`;
      if (filterCat !== 'all') url += `category=${filterCat}&`;
      if (filterStatus !== 'all') url += `status=${filterStatus}&`;

      const res = await api.get(url);
      setSources(res.data);
    } catch (err) {
      console.error('Failed to load sources', err);
    } finally {
      setLoading(false);
    }
  }, [company, filterCat, filterStatus]);

  useEffect(() => {
    loadSources();
  }, [loadSources]);

  async function handleAddSource(e) {
    e.preventDefault();
    if (!formData.name || !formData.url || !formData.reason || adding) return;
    setAdding(true);
    try {
      await api.post(`/companies/${company.id}/sources`, {
        ...formData,
        competitor_name: formData.category === 'competitors' ? formData.competitor_name : null,
      });
      setShowAddModal(false);
      setFormData({
        name: '',
        url: '',
        category: 'competitors',
        reason: '',
        competitor_name: '',
        source_reliability: 0.8,
        relevance_score: 0.8,
      });
      await loadSources();
    } catch (err) {
      console.error('Failed to add custom source', err);
    } finally {
      setAdding(false);
    }
  }

  async function handleApprove(sourceId) {
    try {
      await api.post(`/sources/${sourceId}/approve`);
      await loadSources();
    } catch (err) {
      console.error('Failed to approve source', err);
    }
  }

  async function handleCrawlSource(sourceId) {
    setCrawlingId(sourceId);
    try {
      await api.post(`/sources/${sourceId}/crawl`);
      await loadSources();
    } catch (err) {
      console.error('Failed to crawl source', err);
    } finally {
      setCrawlingId(null);
    }
  }

  async function handleCrawlAll() {
    if (!company || crawlingAll) return;
    setCrawlingAll(true);
    try {
      await api.post(`/companies/${company.id}/crawl`);
      await loadSources();
    } catch (err) {
      console.error('Failed to crawl all sources', err);
    } finally {
      setCrawlingAll(false);
    }
  }

  async function handleRemove(sourceId) {
    try {
      await api.delete(`/sources/${sourceId}`);
      await loadSources();
    } catch (err) {
      console.error('Failed to remove source', err);
    }
  }

  async function openHistory(source) {
    setHistorySource(source);
    setLoadingHistory(true);
    try {
      const res = await api.get(`/sources/${source.id}/history`);
      setHistoryData(res.data);
    } catch (err) {
      console.error('Failed to fetch source history', err);
    } finally {
      setLoadingHistory(false);
    }
  }

  if (loading || loadingCompany) {
    return <PageSkeleton />;
  }

  if (!company) {
    return (
      <div className="sources-page">
        <h1>Source Manager</h1>
        <div className="card sources-empty">
          <p>No active company selected. Please setup a company first.</p>
          <Link to="/" className="btn-primary">Go to Setup</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="sources-page">
      <div className="sources-header">
        <div>
          <h1>Source Manager</h1>
          <p className="sources-subtitle">
            Audit health, approve discovered sensors, and add custom intelligence feeds for <strong>{company.name}</strong>.
          </p>
        </div>

        <div className="stack-actions">
          <button
            className="btn-primary"
            onClick={handleCrawlAll}
            disabled={crawlingAll}
          >
            {crawlingAll ? (
              <><span className="spinner" /> Crawling All…</>
            ) : (
              <><FiActivity /> Crawl Approved</>
            )}
          </button>

          <button className="btn-secondary" onClick={() => setShowAddModal(true)}>
            <FiPlus /> Add Custom Source
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="card sources-filters-card">
        <div className="sources-filter-group">
          <FiFilter style={{ color: 'var(--tertiary)' }} />
          <span className="filter-label">Category:</span>
          <select value={filterCat} onChange={(e) => setFilterCat(e.target.value)}>
            <option value="all">All Categories</option>
            <option value="customers">Customers</option>
            <option value="competitors">Competitors</option>
            <option value="market">Market & Regulatory</option>
            <option value="internal">Internal</option>
          </select>
        </div>

        <div className="sources-filter-group">
          <span className="filter-label">Status:</span>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
            <option value="all">All Active</option>
            <option value="approved">Approved</option>
            <option value="suggested">Suggested</option>
            <option value="inactive">Inactive</option>
            <option value="dead">Dead</option>
          </select>
        </div>

        <span className="sources-count-badge">{sources.length} sources</span>
      </div>

      {/* Sources Table */}
      {loading ? (
        <div className="card sources-loading">
          <span className="spinner" />
          <p>Loading source roster…</p>
        </div>
      ) : sources.length === 0 ? (
        <div className="card sources-empty">
          <p>No sources match the selected filters.</p>
        </div>
      ) : (
        <div className="card sources-table-card">
          <table className="sources-table">
            <thead>
              <tr>
                <th>Source Name</th>
                <th>Category</th>
                <th>URL</th>
                <th>Relevance</th>
                <th>Reliability</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sources.map((source) => {
                const isApproved = source.status === 'approved';

                return (
                  <tr key={source.id}>
                    <td>
                      <div className="source-td-name">
                        <strong>{source.name}</strong>
                        {source.competitor_name && (
                          <span className="source-td-sub">Competitor: {source.competitor_name}</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <span className="source-td-category">{source.category}</span>
                    </td>
                    <td>
                      <a
                        href={source.url.startsWith('http') ? source.url : undefined}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="source-td-url"
                      >
                        {source.url.slice(0, 35)}... <FiExternalLink style={{ fontSize: 11, marginLeft: 2 }} />
                      </a>
                    </td>
                    <td>
                      <span className="source-score-pill">{Math.round((source.relevance_score || 0.8) * 100)}%</span>
                    </td>
                    <td>
                      <span className="source-score-pill">{Math.round((source.source_reliability || 0.8) * 100)}%</span>
                    </td>
                    <td>
                      <span className={`badge ${isApproved ? 'badge-verified' : 'badge-assumed'}`}>
                        {source.status}
                      </span>
                    </td>
                    <td>
                      <div className="source-td-actions">
                        {!isApproved && (
                          <button
                            className="btn-primary table-btn-sm"
                            onClick={() => handleApprove(source.id)}
                            title="Approve source"
                          >
                            <FiCheck />
                          </button>
                        )}
                        {isApproved && (
                          <button
                            className="btn-secondary table-btn-sm"
                            onClick={() => handleCrawlSource(source.id)}
                            disabled={crawlingId === source.id}
                            title="Crawl now"
                          >
                            {crawlingId === source.id ? <span className="spinner" /> : <FiRefreshCw />}
                          </button>
                        )}
                        <button
                          className="btn-secondary table-btn-sm"
                          onClick={() => openHistory(source)}
                          title="View crawl history & health"
                        >
                          <FiActivity />
                        </button>
                        <button
                          className="btn-secondary table-btn-sm table-btn-danger"
                          onClick={() => handleRemove(source.id)}
                          title="Remove source"
                        >
                          <FiTrash2 />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Custom Source Modal */}
      {showAddModal && (
        <div className="modal-backdrop">
          <div className="modal-card card">
            <div className="modal-header">
              <h2>Add Custom Intelligence Source</h2>
              <button className="modal-close-btn" onClick={() => setShowAddModal(false)}>
                <FiX />
              </button>
            </div>

            <form onSubmit={handleAddSource} className="modal-form">
              <div className="form-group">
                <label>Source Name</label>
                <input
                  type="text"
                  placeholder="e.g. Higher Education Policy Institute"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Source URL</label>
                <input
                  type="url"
                  placeholder="https://..."
                  value={formData.url}
                  onChange={(e) => setFormData({ ...formData, url: e.target.value })}
                  required
                />
              </div>

              <div className="form-group">
                <label>Category</label>
                <select
                  value={formData.category}
                  onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                >
                  <option value="competitors">Competitors</option>
                  <option value="customers">Customers</option>
                  <option value="market">Market & Regulatory</option>
                  <option value="internal">Internal</option>
                </select>
              </div>

              {formData.category === 'competitors' && (
                <div className="form-group">
                  <label>Competitor Name</label>
                  <input
                    type="text"
                    placeholder="e.g. IDP Education"
                    value={formData.competitor_name}
                    onChange={(e) => setFormData({ ...formData, competitor_name: e.target.value })}
                  />
                </div>
              )}

              <div className="form-group">
                <label>Reason for Monitoring</label>
                <textarea
                  placeholder="Explain why this source provides decision-relevant intelligence..."
                  value={formData.reason}
                  onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                  rows={3}
                  required
                />
              </div>

              <div className="modal-actions">
                <button type="submit" className="btn-primary" disabled={adding}>
                  {adding ? <span className="spinner" /> : <><FiPlus /> Add Source</>}
                </button>
                <button type="button" className="btn-secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* History / Health Modal */}
      {historySource && (
        <div className="modal-backdrop">
          <div className="modal-card card">
            <div className="modal-header">
              <div>
                <h2>Source Health & History</h2>
                <p className="modal-sub">{historySource.name}</p>
              </div>
              <button className="modal-close-btn" onClick={() => setHistorySource(null)}>
                <FiX />
              </button>
            </div>

            {loadingHistory ? (
              <div className="modal-loading">
                <span className="spinner" />
                <p>Loading crawl telemetry…</p>
              </div>
            ) : (
              <div className="history-content">
                <div className="history-meta-box">
                  <div><strong>URL:</strong> {historySource.url}</div>
                  <div><strong>Reason:</strong> {historySource.reason}</div>
                  <div><strong>Status:</strong> {historySource.status}</div>
                  <div><strong>Last Checked:</strong> {historySource.last_checked ? new Date(historySource.last_checked).toLocaleString() : 'Never'}</div>
                </div>

                <h3>Recent Crawl Runs</h3>
                {historyData?.crawl_runs?.length === 0 ? (
                  <p className="history-empty">No crawl runs recorded yet for this source.</p>
                ) : (
                  <div className="history-runs-list">
                    {historyData?.crawl_runs?.map((run) => (
                      <div key={run.id} className="history-run-item">
                        <span>{new Date(run.started_at).toLocaleString()}</span>
                        <span className={`badge ${run.status === 'success' ? 'badge-verified' : 'badge-assumed'}`}>
                          {run.status} (HTTP {run.http_status || '-'})
                        </span>
                        <span>{run.new_docs} new docs</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
