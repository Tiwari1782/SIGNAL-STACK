import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { FiCheck, FiHelpCircle, FiUser, FiExternalLink, FiEdit3, FiSave, FiX } from 'react-icons/fi';
import api from '../api';
import { useCompany } from '../context/CompanyContext';
import './ProfilePage.css';

const STATUS_META = {
  verified:         { label: 'Verified',         cls: 'badge-verified', Icon: FiCheck },
  assumed:          { label: 'Assumed',           cls: 'badge-assumed',  Icon: FiHelpCircle },
  founder_provided: { label: 'Founder Provided', cls: 'badge-founder',  Icon: FiUser },
};

export default function ProfilePage() {
  const { company } = useCompany();
  const [facts, setFacts] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState('');
  const [saving, setSaving] = useState(false);

  const loadFacts = useCallback(async () => {
    if (!company) return;
    try {
      const res = await api.get(`/companies/${company.id}/profile`);
      setFacts(res.data);
    } catch (err) {
      console.error('Failed to load profile facts', err);
    }
  }, [company]);

  useEffect(() => {
    loadFacts();
  }, [loadFacts]);

  function startEdit(fact) {
    setEditingId(fact.id);
    setEditValue(fact.value);
  }

  function cancelEdit() {
    setEditingId(null);
    setEditValue('');
  }

  async function saveEdit(fact) {
    setSaving(true);
    try {
      await api.patch(`/companies/${company.id}/profile`, {
        fact_id: fact.id,
        value: editValue,
        status: 'founder_provided',
      });
      setFacts((prev) =>
        prev.map((f) =>
          f.id === fact.id ? { ...f, value: editValue, status: 'founder_provided' } : f
        )
      );
      setEditingId(null);
    } catch (err) {
      console.error('Failed to update fact', err);
    } finally {
      setSaving(false);
    }
  }

  if (!company) {
    return (
      <div className="profile-page">
        <h1>Company Profile</h1>
        <div className="profile-empty card">
          <p>No company selected.</p>
          <Link to="/" className="btn-primary">Go to Setup</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="profile-page">
      <div className="profile-header">
        <h1>{company.name}</h1>
        <a href={company.website} target="_blank" rel="noopener noreferrer" className="profile-website">
          {company.website} <FiExternalLink style={{ fontSize: '13px', marginLeft: '4px' }} />
        </a>
      </div>

      <h2>Profile Facts</h2>

      {facts.length === 0 ? (
        <p className="profile-empty-text">
          No profile facts yet. Run research from the <Link to="/">Setup</Link> page.
        </p>
      ) : (
        <div className="profile-facts-grid">
          {facts.map((fact) => {
            const meta = STATUS_META[fact.status] || STATUS_META.assumed;
            const StatusIcon = meta.Icon;
            const isEditing = editingId === fact.id;

            return (
              <div key={fact.id} className="card profile-fact-card">
                <div className="profile-fact-header">
                  <span className="profile-fact-label">{fact.field.replace(/_/g, ' ')}</span>
                  <span className={`badge ${meta.cls}`}>
                    <StatusIcon style={{ marginRight: 4 }} /> {meta.label}
                  </span>
                </div>

                {isEditing ? (
                  <div className="profile-fact-edit">
                    <textarea
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      rows={3}
                    />
                    <div className="profile-fact-edit-actions">
                      <button className="btn-primary" onClick={() => saveEdit(fact)} disabled={saving}>
                        {saving ? 'Saving…' : <><FiSave /> Save</>}
                      </button>
                      <button className="btn-secondary" onClick={cancelEdit}><FiX /> Cancel</button>
                    </div>
                  </div>
                ) : (
                  <p className="profile-fact-value" onClick={() => startEdit(fact)} title="Click to edit">
                    {fact.value}
                    <FiEdit3 className="profile-fact-edit-icon" />
                  </p>
                )}

                {fact.evidence_url && (
                  <a
                    href={fact.evidence_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="profile-fact-evidence"
                  >
                    <FiExternalLink style={{ marginRight: 4 }} /> Verified Source
                  </a>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
