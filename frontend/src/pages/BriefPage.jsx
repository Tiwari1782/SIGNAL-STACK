import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  FiFileText,
  FiSend,
  FiPrinter,
  FiClock,
  FiCheckCircle,
  FiCircle,
  FiTrendingUp,
  FiAlertTriangle,
  FiTarget,
  FiGlobe,
  FiUsers,
  FiFolder,
  FiAward,
  FiExternalLink,
  FiRefreshCw,
  FiMail,
  FiX,
  FiCheckSquare,
  FiEye
} from 'react-icons/fi';
import api from '../api';
import { useCompany } from '../context/CompanyContext';
import './BriefPage.css';

export default function BriefPage() {
  const { company } = useCompany();
  const [briefsList, setBriefsList] = useState([]);
  const [selectedBriefId, setSelectedBriefId] = useState(null);
  const [briefData, setBriefData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  // Email modal state
  const [showEmailModal, setShowEmailModal] = useState(false);
  const [recipientEmail, setRecipientEmail] = useState('');
  const [sendingEmail, setSendingEmail] = useState(false);
  const [emailStatus, setEmailStatus] = useState(null);

  // Action status update state
  const [updatingActionId, setUpdatingActionId] = useState(null);

  const loadBriefsList = useCallback(async () => {
    if (!company) return;
    try {
      const res = await api.get(`/companies/${company.id}/briefs`);
      setBriefsList(res.data);
      if (res.data.length > 0 && !selectedBriefId) {
        setSelectedBriefId(res.data[0].id);
      }
    } catch (err) {
      console.error('Failed to load briefs list', err);
    }
  }, [company, selectedBriefId]);

  const loadBriefDetail = useCallback(async (bId) => {
    if (!bId) return;
    setLoading(true);
    try {
      const res = await api.get(`/briefs/${bId}`);
      setBriefData(res.data);
    } catch (err) {
      console.error('Failed to load brief details', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadBriefsList();
  }, [loadBriefsList]);

  useEffect(() => {
    if (selectedBriefId) {
      loadBriefDetail(selectedBriefId);
    }
  }, [selectedBriefId, loadBriefDetail]);

  async function handleGenerateBrief() {
    if (!company || generating) return;
    setGenerating(true);
    try {
      const res = await api.post(`/companies/${company.id}/briefs/generate`);
      await loadBriefsList();
      setSelectedBriefId(res.data.id);
    } catch (err) {
      console.error('Failed to generate brief', err);
    } finally {
      setGenerating(false);
    }
  }

  async function handleToggleAction(action) {
    const nextStatus = action.status === 'done' ? 'open' : 'done';
    setUpdatingActionId(action.id);
    try {
      const res = await api.patch(`/actions/${action.id}`, { status: nextStatus });
      setBriefData((prev) => ({
        ...prev,
        actions: prev.actions.map((a) => (a.id === action.id ? res.data : a)),
      }));
    } catch (err) {
      console.error('Failed to update action', err);
    } finally {
      setUpdatingActionId(null);
    }
  }

  async function handleSendEmail(e) {
    e.preventDefault();
    if (!recipientEmail || sendingEmail || !selectedBriefId) return;
    setSendingEmail(true);
    setEmailStatus(null);
    try {
      const res = await api.post(`/briefs/${selectedBriefId}/email`, {
        recipient_email: recipientEmail,
      });
      setEmailStatus({ ok: true, msg: res.data.message });
      setTimeout(() => {
        setShowEmailModal(false);
        setEmailStatus(null);
      }, 2000);
    } catch (err) {
      console.error('Failed to email brief', err);
      setEmailStatus({ ok: false, msg: err.response?.data?.detail || 'Failed to send email' });
    } finally {
      setSendingEmail(false);
    }
  }

  if (!company) {
    return (
      <div className="brief-page">
        <h1>Monday Morning Brief</h1>
        <div className="card brief-empty">
          <p>No active company selected. Please setup a company first.</p>
          <Link to="/" className="btn-primary">Go to Setup</Link>
        </div>
      </div>
    );
  }

  const content = briefData?.content || {};
  const actions = briefData?.actions || [];

  return (
    <div className="brief-page">
      {/* Header Bar */}
      <div className="brief-header">
        <div>
          <h1>Monday Morning Brief</h1>
          <p className="brief-subtitle">
            Executive intelligence briefing and weekly action tracker for <strong>{company.name}</strong>.
          </p>
        </div>

        <div className="brief-header-actions">
          <button
            className="btn-primary"
            onClick={handleGenerateBrief}
            disabled={generating}
          >
            {generating ? (
              <><span className="spinner" /> Synthesizing 10-Section Brief…</>
            ) : (
              <><FiRefreshCw /> Generate Brief Now</>
            )}
          </button>

          {selectedBriefId && (
            <>
              <button
                className="btn-secondary"
                onClick={() => setShowEmailModal(true)}
                title="Email full HTML brief via Gmail"
              >
                <FiMail /> Email Brief
              </button>

              <a
                href={`/api/briefs/${selectedBriefId}/html`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary"
                title="Open printable HTML version"
              >
                <FiPrinter /> HTML / Print
              </a>
            </>
          )}
        </div>
      </div>

      {/* History Selector Bar */}
      {briefsList.length > 1 && (
        <div className="card brief-history-card">
          <FiClock style={{ color: 'var(--tertiary)', marginRight: 6 }} />
          <span className="history-label">Historical Briefs:</span>
          <div className="history-chips">
            {briefsList.map((b) => (
              <button
                key={b.id}
                className={`history-chip ${b.id === selectedBriefId ? 'history-chip--active' : ''}`}
                onClick={() => setSelectedBriefId(b.id)}
              >
                {b.period_start} to {b.period_end} ({new Date(b.created_at).toLocaleDateString()})
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Main Content Area */}
      {loading ? (
        <div className="card brief-loading">
          <span className="spinner" />
          <p>Loading executive briefing…</p>
        </div>
      ) : !briefData ? (
        <div className="card brief-empty">
          <FiFileText style={{ fontSize: 48, color: 'var(--tertiary)' }} />
          <h2>No Brief Generated Yet</h2>
          <p>Synthesize real-time signals, market shifts, and competitor developments into your first Monday Morning Brief.</p>
          <button className="btn-primary" onClick={handleGenerateBrief} disabled={generating}>
            Generate First Brief Now
          </button>
        </div>
      ) : (
        <div className="brief-report-container">
          {/* Cover Header */}
          <div className="brief-cover card">
            <span className="brief-meta-badge">Executive Briefing</span>
            <h2 className="brief-report-title">{content.title}</h2>
            <div className="brief-report-meta">
              <span>Coverage Period: <strong>{content.period}</strong></span>
              <span>•</span>
              <span>Trigger: <strong>{briefData.trigger}</strong></span>
              <span>•</span>
              <span>Published: <strong>{new Date(briefData.created_at).toLocaleString()}</strong></span>
            </div>
          </div>

          {/* Section 1: Executive Summary */}
          <div className="brief-section card section-exec">
            <div className="section-header">
              <span className="section-num">1</span>
              <h3>Executive Summary — Top Developments</h3>
            </div>
            <ul className="exec-summary-list">
              {content.executive_summary?.map((pt, idx) => (
                <li key={idx} className="exec-summary-item">
                  <FiTrendingUp className="exec-summary-icon" />
                  <span>{pt}</span>
                </li>
              ))}
            </ul>
          </div>

          {/* Section 2: Customer Signals */}
          <div className="brief-section card">
            <div className="section-header">
              <span className="section-num">2</span>
              <h3>Customer Signals</h3>
            </div>
            <p className="section-desc">
              {content.customer_signals?.summary || 'No meaningful development this week.'}
            </p>
          </div>

          {/* Section 3: Competitor Intelligence */}
          <div className="brief-section card">
            <div className="section-header">
              <span className="section-num">3</span>
              <h3>Competitor Intelligence</h3>
            </div>
            <p className="section-desc">
              {content.competitor_intelligence?.summary || 'No meaningful development this week.'}
            </p>
          </div>

          {/* Section 4: Market Intelligence */}
          <div className="brief-section card">
            <div className="section-header">
              <span className="section-num">4</span>
              <h3>Market & Regulatory Intelligence</h3>
            </div>
            <p className="section-desc">
              {content.market_intelligence?.summary || 'No meaningful development this week.'}
            </p>
          </div>

          {/* Section 5: Internal Business Intelligence */}
          <div className="brief-section card">
            <div className="section-header">
              <span className="section-num">5</span>
              <h3>Internal Business Intelligence</h3>
            </div>
            <p className="section-desc">
              {content.internal_intelligence?.summary || 'No internal uploads recorded this week.'}
            </p>
          </div>

          {/* Section 6: Opportunities Identified */}
          <div className="brief-section card">
            <div className="section-header">
              <span className="section-num">6</span>
              <h3>Actionable Opportunities</h3>
            </div>
            {content.opportunities?.length === 0 ? (
              <p className="section-empty-msg">No opportunities substantiated by verified evidence this week.</p>
            ) : (
              <div className="brief-cards-grid">
                {content.opportunities?.map((opp, idx) => (
                  <div key={idx} className="brief-sub-card opp-card">
                    <div className="sub-card-top">
                      <strong>{opp.title}</strong>
                      <span className="badge badge-verified">{opp.priority || 'High'} Priority</span>
                    </div>
                    <p className="sub-card-text"><strong>Expected Impact:</strong> {opp.impact}</p>
                    <p className="sub-card-evidence"><strong>Evidence:</strong> "{opp.evidence}"</p>
                    <p className="sub-card-next"><strong>Immediate Next Step:</strong> {opp.next_step}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Section 7: Risks & Threats */}
          <div className="brief-section card">
            <div className="section-header">
              <span className="section-num">7</span>
              <h3>Risks & Strategic Threats</h3>
            </div>
            {content.risks_and_threats?.length === 0 ? (
              <p className="section-empty-msg">No critical negative risks identified this period.</p>
            ) : (
              <div className="brief-cards-grid">
                {content.risks_and_threats?.map((r, idx) => (
                  <div key={idx} className="brief-sub-card threat-card">
                    <div className="sub-card-top">
                      <strong>{r.title}</strong>
                      <span className="badge badge-threat">{r.urgency || 'Medium'} Urgency</span>
                    </div>
                    <p className="sub-card-text"><strong>Possible Impact:</strong> {r.possible_impact}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Section 8: Recommended Actions for This Week */}
          <div className="brief-section card section-actions">
            <div className="section-header">
              <span className="section-num">8</span>
              <div>
                <h3>Recommended Actions for This Week</h3>
                <span className="section-subtitle-tag">Interactive Task Tracker (click checkbox to complete)</span>
              </div>
            </div>

            {actions.length === 0 ? (
              <p className="section-empty-msg">No recommended actions generated.</p>
            ) : (
              <div className="actions-list">
                {actions.map((act) => {
                  const isDone = act.status === 'done';
                  const isBusy = updatingActionId === act.id;

                  return (
                    <div
                      key={act.id}
                      className={`action-item ${isDone ? 'action-item--done' : ''}`}
                      onClick={() => !isBusy && handleToggleAction(act)}
                    >
                      <button className="action-checkbox" disabled={isBusy}>
                        {isDone ? (
                          <FiCheckCircle className="check-icon-done" />
                        ) : (
                          <FiCircle className="check-icon-open" />
                        )}
                      </button>

                      <div className="action-content">
                        <div className="action-title-row">
                          <span className="action-title">{act.title}</span>
                          <span className="badge badge-founder">Owner: {act.owner}</span>
                          <span className="badge badge-category">{act.priority}</span>
                        </div>
                        <p className="action-reason">{act.reason}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Section 9: Watchlist */}
          <div className="brief-section card">
            <div className="section-header">
              <span className="section-num">9</span>
              <h3>What We Should Watch</h3>
            </div>
            {content.watchlist?.length === 0 ? (
              <p className="section-empty-msg">No emerging items flagged for watchlist.</p>
            ) : (
              <div className="watchlist-grid">
                {content.watchlist?.map((w, idx) => (
                  <div key={idx} className="watchlist-card">
                    <strong>{w.topic}</strong>
                    <p>{w.why_watch}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Section 10: Source Appendix */}
          <div className="brief-section card">
            <div className="section-header">
              <span className="section-num">10</span>
              <h3>Source Appendix & Evidence Trace</h3>
            </div>
            {content.source_appendix?.length === 0 ? (
              <p className="section-empty-msg">No external sources cited.</p>
            ) : (
              <div className="appendix-list">
                {content.source_appendix?.map((app, idx) => (
                  <div key={idx} className="appendix-item">
                    <div className="appendix-header">
                      <strong>{app.source_name}</strong>
                      <span className="badge badge-verified">{app.verification_status || 'Verified'}</span>
                    </div>
                    <a href={app.url} target="_blank" rel="noopener noreferrer" className="appendix-url">
                      {app.url} <FiExternalLink style={{ fontSize: 11, marginLeft: 2 }} />
                    </a>
                    <blockquote className="appendix-quote">
                      "{app.evidence_snippet}"
                    </blockquote>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Email Modal */}
      {showEmailModal && (
        <div className="modal-backdrop">
          <div className="modal-card card">
            <div className="modal-header">
              <h2>Email Brief via Gmail</h2>
              <button className="modal-close-btn" onClick={() => setShowEmailModal(false)}>
                <FiX />
              </button>
            </div>

            <form onSubmit={handleSendEmail} className="modal-form">
              <div className="form-group">
                <label>Recipient Email Address</label>
                <input
                  type="email"
                  placeholder="founder@example.com"
                  value={recipientEmail}
                  onChange={(e) => setRecipientEmail(e.target.value)}
                  required
                />
              </div>

              {emailStatus && (
                <div className={`email-status-banner ${emailStatus.ok ? 'status-ok' : 'status-err'}`}>
                  {emailStatus.msg}
                </div>
              )}

              <div className="modal-actions">
                <button type="submit" className="btn-primary" disabled={sendingEmail}>
                  {sendingEmail ? <span className="spinner" /> : <><FiSend /> Send Brief Now</>}
                </button>
                <button type="button" className="btn-secondary" onClick={() => setShowEmailModal(false)}>
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
