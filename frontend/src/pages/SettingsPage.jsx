import { useState, useEffect } from 'react';
import {
  FiClock,
  FiMail,
  FiPlay,
  FiRefreshCw,
  FiCheckCircle,
  FiAlertCircle,
  FiAlertTriangle,
  FiCalendar,
  FiGlobe,
  FiSliders,
  FiShield,
  FiActivity,
  FiFileText,
  FiChevronDown,
  FiChevronUp,
  FiSave,
  FiExternalLink,
} from 'react-icons/fi';
import { useCompany } from '../context/CompanyContext';
import { useToast } from '../context/ToastContext';
import './SettingsPage.css';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const safeDecode = (url) => {
  if (!url) return '';
  try {
    return decodeURIComponent(url);
  } catch (e) {
    return url;
  }
};

export default function SettingsPage() {
  const { company } = useCompany();
  const { addToast } = useToast();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [runningWeekly, setRunningWeekly] = useState(false);
  const [runningAudit, setRunningAudit] = useState(false);

  // Settings State
  const [settings, setSettings] = useState({
    briefing_day: 'Monday',
    briefing_time: '08:00',
    timezone: 'UTC',
    monitor_frequency: 'daily',
    refresh_frequency: 'weekly',
    monthly_audit_enabled: true,
    email_notifications: false,
    recipient_email: '',
    auto_approve_discovered_sources: false,
  });

  // Job Runs & Audits
  const [jobRuns, setJobRuns] = useState([]);
  const [auditReports, setAuditReports] = useState([]);
  const [expandedErrorId, setExpandedErrorId] = useState(null);

  useEffect(() => {
    if (!company) {
      setLoading(false);
      return;
    }
    fetchSettingsAndLogs();
  }, [company]);

  const fetchSettingsAndLogs = async () => {
    setLoading(true);
    try {
      const [settRes, runsRes, auditRes] = await Promise.all([
        fetch(`${API}/api/companies/${company.id}/settings`),
        fetch(`${API}/api/companies/${company.id}/job-runs?limit=25`),
        fetch(`${API}/api/companies/${company.id}/audit-reports?limit=10`),
      ]);

      if (settRes.ok) {
        const settData = await settRes.json();
        setSettings(settData.settings);
      }
      if (runsRes.ok) {
        const runsData = await runsRes.json();
        setJobRuns(runsData);
      }
      if (auditRes.ok) {
        const auditData = await auditRes.json();
        setAuditReports(auditData);
      }
    } catch (err) {
      console.error('Failed to load settings data:', err);
      addToast('Failed to load settings and run logs', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      const res = await fetch(`${API}/api/companies/${company.id}/settings`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings),
      });

      if (!res.ok) throw new Error('Save failed');
      const data = await res.json();
      setSettings(data.settings);
      addToast('System settings and preferences saved successfully', 'success');
    } catch (err) {
      console.error('Save error:', err);
      addToast('Failed to save settings: ' + err.message, 'error');
    } finally {
      setSaving(false);
    }
  };

  const triggerWeeklyBrief = async () => {
    setRunningWeekly(true);
    addToast('Starting Weekly Brief pipeline...', 'info');
    try {
      const res = await fetch(`${API}/api/jobs/weekly_brief/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_id: company.id }),
      });
      const data = await res.json();
      if (data.status === 'success') {
        addToast('Weekly Brief pipeline completed successfully!', 'success');
      } else {
        addToast(`Weekly Brief run finished: ${data.error || 'Check log'}`, 'warning');
      }
      fetchSettingsAndLogs();
    } catch (err) {
      addToast('Weekly Brief trigger error: ' + err.message, 'error');
    } finally {
      setRunningWeekly(false);
    }
  };

  const triggerMonthlyAudit = async () => {
    setRunningAudit(true);
    addToast('Executing Monthly Signal Stack Audit...', 'info');
    try {
      const res = await fetch(`${API}/api/jobs/monthly_audit/run`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company_id: company.id }),
      });
      const data = await res.json();
      if (data.status === 'success') {
        addToast(`Audit completed! Health Score: ${data.summary?.health_score || 100}/100`, 'success');
      } else {
        addToast('Monthly audit finished with errors', 'warning');
      }
      fetchSettingsAndLogs();
    } catch (err) {
      addToast('Monthly audit error: ' + err.message, 'error');
    } finally {
      setRunningAudit(false);
    }
  };

  if (!company) {
    return (
      <div className="settings-page">
        <div className="card settings-empty">
          <h2>No Active Company Selected</h2>
          <p>Please select or configure a company on the Setup page to view settings and job runs.</p>
        </div>
      </div>
    );
  }

  const latestAudit = auditReports[0];

  return (
    <div className="settings-page">
      {/* Header */}
      <header className="settings-header">
        <div>
          <span className="badge">System Configuration</span>
          <h1 className="settings-title">Settings & Scheduler</h1>
          <p className="settings-subtitle">
            Configure automated briefing schedules, background crawl intervals, and inspect real-time audit logs.
          </p>
        </div>
        <div className="settings-actions">
          <button
            type="button"
            className="btn-secondary"
            onClick={fetchSettingsAndLogs}
            disabled={loading}
          >
            <FiRefreshCw className={loading ? 'spin-icon' : ''} />
            <span>Refresh Logs</span>
          </button>
        </div>
      </header>

      {/* Manual Execution Triggers Bar */}
      <section className="triggers-card card">
        <div className="triggers-info">
          <div className="triggers-icon"><FiActivity /></div>
          <div>
            <h3 className="triggers-heading">Manual Job Execution</h3>
            <p className="triggers-desc">
              Trigger background jobs on demand without waiting for GitHub Actions cron schedules.
            </p>
          </div>
        </div>

        <div className="triggers-buttons">
          <button
            type="button"
            className="btn-primary"
            onClick={triggerWeeklyBrief}
            disabled={runningWeekly || runningAudit}
          >
            {runningWeekly ? <FiRefreshCw className="spin-icon" /> : <FiPlay />}
            <span>{runningWeekly ? 'Running Pipeline...' : 'Generate Brief Now'}</span>
          </button>

          <button
            type="button"
            className="btn-secondary"
            onClick={triggerMonthlyAudit}
            disabled={runningWeekly || runningAudit}
          >
            {runningAudit ? <FiRefreshCw className="spin-icon" /> : <FiShield />}
            <span>{runningAudit ? 'Auditing Stack...' : 'Run Monthly Audit'}</span>
          </button>
        </div>
      </section>

      {/* Main Two-Column Grid */}
      <div className="settings-grid">
        {/* Left Column: Settings Form */}
        <div className="settings-form-col">
          <form className="card settings-form-card" onSubmit={handleSaveSettings}>
            <div className="card-section-header">
              <span className="card-icon"><FiClock /></span>
              <div>
                <h2>Briefing Schedule</h2>
                <p>Define when your executive Monday Morning Brief is generated.</p>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">
                  <FiCalendar /> Briefing Day
                </label>
                <select
                  value={settings.briefing_day}
                  onChange={(e) => setSettings({ ...settings, briefing_day: e.target.value })}
                >
                  <option value="Monday">Monday (Standard)</option>
                  <option value="Tuesday">Tuesday</option>
                  <option value="Wednesday">Wednesday</option>
                  <option value="Thursday">Thursday</option>
                  <option value="Friday">Friday</option>
                  <option value="Sunday">Sunday</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">
                  <FiClock /> Delivery Time
                </label>
                <input
                  type="time"
                  value={settings.briefing_time}
                  onChange={(e) => setSettings({ ...settings, briefing_time: e.target.value })}
                />
              </div>
            </div>

            <div className="form-group">
              <label className="form-label">
                <FiGlobe /> Timezone
              </label>
              <select
                value={settings.timezone}
                onChange={(e) => setSettings({ ...settings, timezone: e.target.value })}
              >
                <option value="UTC">UTC (Coordinated Universal Time)</option>
                <option value="America/New_York">US / Eastern (New York)</option>
                <option value="America/Los_Angeles">US / Pacific (San Francisco)</option>
                <option value="Europe/London">Europe / London (GMT/BST)</option>
                <option value="Asia/Kolkata">Asia / Kolkata (IST)</option>
                <option value="Asia/Singapore">Asia / Singapore (SGT)</option>
              </select>
            </div>

            <div className="settings-divider" />

            <div className="card-section-header">
              <span className="card-icon"><FiSliders /></span>
              <div>
                <h2>Crawling & Audits</h2>
                <p>Manage background monitoring frequencies and health scans.</p>
              </div>
            </div>

            <div className="form-row">
              <div className="form-group">
                <label className="form-label">Monitor Frequency</label>
                <select
                  value={settings.monitor_frequency}
                  onChange={(e) => setSettings({ ...settings, monitor_frequency: e.target.value })}
                >
                  <option value="hourly">Hourly</option>
                  <option value="every_6_hours">Every 6 Hours</option>
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label">Refresh Frequency</label>
                <select
                  value={settings.refresh_frequency}
                  onChange={(e) => setSettings({ ...settings, refresh_frequency: e.target.value })}
                >
                  <option value="daily">Daily</option>
                  <option value="weekly">Weekly</option>
                  <option value="biweekly">Bi-weekly</option>
                  <option value="monthly">Monthly</option>
                </select>
              </div>
            </div>

            <div className="checkboxes-wrap">
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={settings.monthly_audit_enabled}
                  onChange={(e) => setSettings({ ...settings, monthly_audit_enabled: e.target.checked })}
                />
                <span>Enable automatic monthly Signal Stack health audit (dead URLs & duplicate detection)</span>
              </label>

              <label className="checkbox-label">
                <input
                  type="checkbox"
                  className="checkbox-input"
                  checked={settings.auto_approve_discovered_sources}
                  onChange={(e) => setSettings({ ...settings, auto_approve_discovered_sources: e.target.checked })}
                />
                <span>Auto-approve new high-relevance discovered sources (relevance &gt; 0.85)</span>
              </label>
            </div>

            <div className="settings-divider" />

            <div className="card-section-header">
              <span className="card-icon"><FiMail /></span>
              <div>
                <h2>Email Delivery</h2>
                <p>Receive your executive brief directly in your inbox.</p>
              </div>
            </div>

            <label className="checkbox-label">
              <input
                type="checkbox"
                className="checkbox-input"
                checked={settings.email_notifications}
                onChange={(e) => setSettings({ ...settings, email_notifications: e.target.checked })}
              />
              <span>Send HTML brief to recipient on completion</span>
            </label>

            {settings.email_notifications && (
              <div className="form-group" style={{ marginTop: '10px' }}>
                <label className="form-label">Recipient Email</label>
                <input
                  type="email"
                  placeholder="executive@meetuniversity.com"
                  value={settings.recipient_email || ''}
                  onChange={(e) => setSettings({ ...settings, recipient_email: e.target.value })}
                />
              </div>
            )}

            <div className="form-footer">
              <button
                type="submit"
                className="btn-primary"
                disabled={saving}
              >
                <FiSave />
                <span>{saving ? 'Saving...' : 'Save Settings'}</span>
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: Latest Audit Card & Report Details */}
        <div className="audit-col">
          <div className="card audit-summary-card">
            <div className="card-section-header">
              <span className="card-icon"><FiShield /></span>
              <div>
                <h2>Signal Stack Health Audit</h2>
                <p>Status of monitored URLs, dead links, and source coverage.</p>
              </div>
            </div>

            {latestAudit ? (
              <div className="audit-report-body">
                <div className="audit-score-row">
                  <div className="health-score-dial">
                    <span className="health-score-val">{latestAudit.health_score ?? 100}</span>
                    <span className="health-score-label">/ 100</span>
                  </div>
                  <div className="health-meta">
                    <span className="health-status-badge">
                      {latestAudit.health_score >= 80 ? (
                        <>
                          <FiCheckCircle style={{ color: 'var(--secondary)' }} />
                          <span style={{ color: 'var(--secondary)' }}>Healthy Stack</span>
                        </>
                      ) : (
                        <>
                          <FiAlertTriangle style={{ color: 'var(--error)' }} />
                          <span style={{ color: 'var(--error)' }}>Needs Maintenance</span>
                        </>
                      )}
                    </span>
                    <span className="health-date">
                      Last audited: {new Date(latestAudit.created_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>

                <p className="audit-summary-text">{latestAudit.summary}</p>

                {/* Audit breakdown stats */}
                <div className="audit-stats-grid">
                  <div className="audit-stat-item">
                    <span className="audit-stat-num">{latestAudit.content?.total_sources_audited || 0}</span>
                    <span className="audit-stat-lbl">Audited</span>
                  </div>
                  <div className="audit-stat-item">
                    <span className="audit-stat-num" style={{ color: latestAudit.content?.dead_sources?.length ? 'var(--error)' : 'inherit' }}>
                      {latestAudit.content?.dead_sources?.length || 0}
                    </span>
                    <span className="audit-stat-lbl">Dead URLs</span>
                  </div>
                  <div className="audit-stat-item">
                    <span className="audit-stat-num">
                      {latestAudit.content?.duplicate_sources?.length || 0}
                    </span>
                    <span className="audit-stat-lbl">Duplicates</span>
                  </div>
                  <div className="audit-stat-item">
                    <span className="audit-stat-num">
                      {latestAudit.content?.inactive_sources?.length || 0}
                    </span>
                    <span className="audit-stat-lbl">Inactive</span>
                  </div>
                </div>

                {/* Dead sources list */}
                {latestAudit.content?.dead_sources?.length > 0 && (
                  <div className="audit-alert-box negative">
                    <div className="audit-alert-title">
                      <FiAlertCircle /> Dead URLs Detected ({latestAudit.content.dead_sources.length})
                    </div>
                    <ul className="audit-detail-list">
                      {latestAudit.content.dead_sources.map((ds, idx) => {
                        const decodedUrl = safeDecode(ds.url);
                        return (
                          <li key={idx} className="audit-detail-item">
                            <span className="audit-source-name">{ds.name}:</span>{' '}
                            <a
                              href={decodedUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="audit-url-link"
                              title={decodedUrl}
                            >
                              {decodedUrl.length > 55 ? decodedUrl.slice(0, 55) + '...' : decodedUrl}
                              <FiExternalLink />
                            </a>
                            <span className="error-tag"> ({ds.error})</span>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}

                {/* Recommended Additions */}
                {latestAudit.content?.recommended_additions?.length > 0 && (
                  <div className="audit-alert-box info">
                    <div className="audit-alert-title">
                      <FiFileText /> Recommended Additions ({latestAudit.content.recommended_additions.length})
                    </div>
                    <ul className="audit-detail-list">
                      {latestAudit.content.recommended_additions.map((ra, idx) => {
                        const decodedUrl = safeDecode(ra.url);
                        return (
                          <li key={idx} className="audit-detail-item">
                            <span className="audit-source-name">{ra.name}</span>{' '}
                            <span className="audit-cat-tag">({ra.category})</span>:{' '}
                            <a
                              href={decodedUrl}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="audit-url-link"
                              title={decodedUrl}
                            >
                              {decodedUrl.length > 55 ? decodedUrl.slice(0, 55) + '...' : decodedUrl}
                              <FiExternalLink />
                            </a>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <div className="audit-empty">
                <FiShield style={{ fontSize: '2.5rem', color: 'var(--tertiary)' }} />
                <p>No audit reports generated yet.</p>
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={triggerMonthlyAudit}
                  disabled={runningAudit}
                >
                  Run First Health Audit
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Bottom Section: Job Runs Audit Log */}
      <section className="card job-runs-section">
        <div className="job-runs-header">
          <div className="card-section-header" style={{ marginBottom: 0 }}>
            <span className="card-icon"><FiActivity /></span>
            <div>
              <h2>Job Runs & Scheduler Audit Log</h2>
              <p>Chronological history of background tasks, pipeline executions, and errors.</p>
            </div>
          </div>
          <span className="badge">{jobRuns.length} Recorded Runs</span>
        </div>

        {jobRuns.length === 0 ? (
          <div className="runs-empty">
            <p>No job executions logged yet. Run a job to inspect telemetry.</p>
          </div>
        ) : (
          <div className="job-runs-table-wrap">
            <table className="job-runs-table">
              <thead>
                <tr>
                  <th>Job Name</th>
                  <th>Status</th>
                  <th>Started</th>
                  <th>Duration</th>
                  <th>Summary / Telemetry</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {jobRuns.map((run) => {
                  const isSuccess = run.status === 'success';
                  const isFailed = run.status === 'failed';
                  const isRunning = run.status === 'running';

                  let durationStr = '—';
                  if (run.started_at && run.finished_at) {
                    const diffSec = Math.round((new Date(run.finished_at) - new Date(run.started_at)) / 1000);
                    durationStr = `${diffSec}s`;
                  } else if (isRunning) {
                    durationStr = 'Active';
                  }

                  const hasError = !!run.error;
                  const isExpanded = expandedErrorId === run.id;

                  return (
                    <tr key={run.id} className={isFailed ? 'row-failed' : ''}>
                      <td>
                        <span className="job-name-cell">
                          <code>{run.job_name}</code>
                          <span className="run-id">#{run.id}</span>
                        </span>
                      </td>
                      <td>
                        <span className={`status-pill status-${run.status}`}>
                          {isSuccess && <FiCheckCircle />}
                          {isFailed && <FiAlertCircle />}
                          {isRunning && <FiRefreshCw className="spin-icon" />}
                          <span>{run.status.toUpperCase()}</span>
                        </span>
                      </td>
                      <td className="timestamp-cell">
                        {new Date(run.started_at).toLocaleString()}
                      </td>
                      <td>{durationStr}</td>
                      <td className="summary-cell">
                        {isSuccess && run.summary && (
                          <span className="summary-tag">
                            {run.job_name === 'weekly_brief' &&
                              `Brief #${run.summary.brief_id || ''} (${run.summary.sources_crawled || 0} crawled, ${run.summary.signals_created || 0} signals)`}
                            {run.job_name === 'monthly_audit' &&
                              `Health ${run.summary.health_score ?? 0}/100 (${run.summary.total_sources_audited || 0} audited)`}
                            {run.job_name !== 'weekly_brief' && run.job_name !== 'monthly_audit' &&
                              JSON.stringify(run.summary).slice(0, 50)}
                          </span>
                        )}
                        {hasError && (
                          <span className="error-text-snippet">
                            {run.error.split('\n').filter(Boolean).pop()?.slice(0, 70)}
                          </span>
                        )}
                        {isRunning && <span className="running-text">Job currently in progress...</span>}
                      </td>
                      <td>
                        {hasError && (
                          <button
                            type="button"
                            className="btn-icon"
                            onClick={() => setExpandedErrorId(isExpanded ? null : run.id)}
                            title="Toggle error traceback"
                          >
                            {isExpanded ? <FiChevronUp /> : <FiChevronDown />}
                          </button>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Traceback Drawer if expanded */}
        {expandedErrorId && (
          <div className="error-traceback-drawer">
            <h4>Error Traceback for Run #{expandedErrorId}</h4>
            <pre>
              {jobRuns.find((r) => r.id === expandedErrorId)?.error || 'No error details recorded.'}
            </pre>
          </div>
        )}
      </section>
    </div>
  );
}
