import { useState, useEffect, useCallback } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FiSend,
  FiSkipForward,
  FiCornerDownRight,
  FiCheckCircle,
  FiEdit3,
  FiSave,
  FiX,
  FiArrowRight,
  FiMessageSquare,
  FiAlertCircle
} from 'react-icons/fi';
import api from '../api';
import { useCompany } from '../context/CompanyContext';
import './InterviewPage.css';

export default function InterviewPage() {
  const { company } = useCompany();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [currentQ, setCurrentQ] = useState(null);
  const [history, setHistory] = useState([]);
  const [completed, setCompleted] = useState(false);
  const [answerText, setAnswerText] = useState('');

  // Editing historical answers
  const [editingId, setEditingId] = useState(null);
  const [editAnswerText, setEditAnswerText] = useState('');
  const [savingEdit, setSavingEdit] = useState(false);

  const fetchNextQuestion = useCallback(async () => {
    if (!company) return;
    setLoading(true);
    setError('');
    try {
      const res = await api.get(`/companies/${company.id}/interview/next`);
      setCompleted(res.data.completed);
      setCurrentQ(res.data.current_question);
      setHistory(res.data.history || []);
      setAnswerText('');
    } catch (err) {
      console.error('Failed to load interview question', err);
      setError(err.response?.data?.detail || 'Failed to fetch next question from AI.');
    } finally {
      setLoading(false);
    }
  }, [company]);

  useEffect(() => {
    fetchNextQuestion();
  }, [fetchNextQuestion]);

  async function handleAnswer(e) {
    e.preventDefault();
    if (!answerText.trim() || submitting || !currentQ) return;
    setSubmitting(true);
    setError('');
    try {
      await api.post(`/companies/${company.id}/interview/answer`, {
        seq: currentQ.seq,
        answer: answerText.trim(),
        skip: false,
      });
      await fetchNextQuestion();
    } catch (err) {
      console.error('Failed to submit answer', err);
      setError(err.response?.data?.detail || 'Failed to submit answer');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSkip() {
    if (submitting || !currentQ) return;
    setSubmitting(true);
    setError('');
    try {
      await api.post(`/companies/${company.id}/interview/answer`, {
        seq: currentQ.seq,
        skip: true,
      });
      await fetchNextQuestion();
    } catch (err) {
      console.error('Failed to skip question', err);
      setError(err.response?.data?.detail || 'Failed to skip question');
    } finally {
      setSubmitting(false);
    }
  }

  function startEdit(item) {
    setEditingId(item.id);
    setEditAnswerText(item.answer || '');
  }

  function cancelEdit() {
    setEditingId(null);
    setEditAnswerText('');
  }

  async function saveEdit(qaId) {
    if (!editAnswerText.trim() || savingEdit) return;
    setSavingEdit(true);
    try {
      const res = await api.patch(`/interview/${qaId}`, {
        answer: editAnswerText.trim(),
      });
      setHistory((prev) =>
        prev.map((item) => (item.id === qaId ? { ...item, ...res.data } : item))
      );
      setEditingId(null);
    } catch (err) {
      console.error('Failed to update answer', err);
    } finally {
      setSavingEdit(false);
    }
  }

  if (!company) {
    return (
      <div className="interview-page">
        <h1>Adaptive AI Interview</h1>
        <div className="interview-empty card">
          <p>No active company selected. Please set up or select a company first.</p>
          <Link to="/" className="btn-primary">Go to Setup</Link>
        </div>
      </div>
    );
  }

  const answeredCount = history.filter((q) => q.answer !== null || q.skipped).length;
  const progressPercent = Math.min(100, Math.round((answeredCount / 10) * 100));

  return (
    <div className="interview-page">
      <div className="interview-header">
        <div>
          <h1>Adaptive Founder Interview</h1>
          <p className="interview-subtitle">
            10 contextual questions tailored for <strong>{company.name}</strong> to calibrate your Signal Stack.
          </p>
        </div>
        <div className="interview-progress-pill">
          <span className="interview-progress-count">{answeredCount} / 10 Completed</span>
          <div className="interview-progress-bar-bg">
            <div className="interview-progress-bar-fill" style={{ width: `${progressPercent}%` }} />
          </div>
        </div>
      </div>

      {error && (
        <div className="interview-error">
          <FiAlertCircle style={{ flexShrink: 0, marginTop: '2px' }} />
          <span>{error}</span>
        </div>
      )}

      {/* Transcript of previous Q&As */}
      {history.length > 0 && (
        <div className="interview-transcript">
          <h2>Interview Transcript</h2>
          <div className="transcript-list">
            {history.map((item) => {
              const isCurrentUnanswered = !completed && currentQ && item.id === currentQ.id;
              if (isCurrentUnanswered) return null; // Rendered below in active card

              const isEditing = editingId === item.id;

              return (
                <div key={item.id} className="transcript-item card">
                  <div className="transcript-question-row">
                    <div className="transcript-q-num">Q{item.seq}</div>
                    <div className="transcript-q-content">
                      <div className="transcript-q-text">
                        {item.question}
                        {item.is_followup && (
                          <span className="badge badge-assumed" style={{ marginLeft: 8 }}>
                            <FiCornerDownRight style={{ marginRight: 2 }} /> Follow-up
                          </span>
                        )}
                      </div>

                      {item.skipped ? (
                        <div className="transcript-skipped">
                          <FiSkipForward style={{ marginRight: 4 }} /> Skipped by founder
                        </div>
                      ) : isEditing ? (
                        <div className="transcript-edit-box">
                          <textarea
                            value={editAnswerText}
                            onChange={(e) => setEditAnswerText(e.target.value)}
                            rows={3}
                          />
                          <div className="transcript-edit-actions">
                            <button
                              className="btn-primary"
                              onClick={() => saveEdit(item.id)}
                              disabled={savingEdit}
                            >
                              {savingEdit ? 'Saving…' : <><FiSave /> Save Answer</>}
                            </button>
                            <button className="btn-secondary" onClick={cancelEdit}>
                              <FiX /> Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="transcript-answer-row">
                          <p className="transcript-answer-text">
                            <strong>A:</strong> {item.answer}
                          </p>
                          <button
                            className="transcript-edit-btn"
                            onClick={() => startEdit(item)}
                            title="Edit answer"
                          >
                            <FiEdit3 /> Edit
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Active Question or Completed State */}
      {loading ? (
        <div className="card interview-loading-card">
          <span className="spinner" />
          <p>Analyzing company context & generating next adaptive question with AI…</p>
        </div>
      ) : completed ? (
        <div className="card interview-completed-card">
          <FiCheckCircle className="completed-icon" />
          <h2>Interview Complete!</h2>
          <p>
            You have answered all 10 strategic questions. Your business context, customer priorities, and
            market concerns are now calibrated.
          </p>
          <div className="completed-actions">
            <button className="btn-primary" onClick={() => navigate('/signal-stack')}>
              Build Signal Stack <FiArrowRight style={{ marginLeft: 6 }} />
            </button>
          </div>
        </div>
      ) : currentQ ? (
        <div className="card active-question-card">
          <div className="active-question-header">
            <span className="active-question-badge">
              Question {currentQ.seq} of 10
            </span>
            {currentQ.is_followup && (
              <span className="badge badge-assumed">
                <FiCornerDownRight style={{ marginRight: 4 }} /> Adaptive Follow-up
              </span>
            )}
          </div>

          <h3 className="active-question-title">{currentQ.question}</h3>

          <form onSubmit={handleAnswer} className="active-question-form">
            <textarea
              value={answerText}
              onChange={(e) => setAnswerText(e.target.value)}
              placeholder="Provide strategic details, key metrics, or context (or skip if confidential)…"
              rows={4}
              required
              disabled={submitting}
            />

            <div className="active-question-actions">
              <button
                type="submit"
                className="btn-primary"
                disabled={submitting || !answerText.trim()}
              >
                {submitting ? (
                  <><span className="spinner" /> Submitting…</>
                ) : (
                  <><FiSend /> Submit Answer</>
                )}
              </button>

              <button
                type="button"
                className="btn-secondary"
                onClick={handleSkip}
                disabled={submitting}
                title="Skip if confidential or not applicable"
              >
                <FiSkipForward /> Skip Question
              </button>
            </div>
          </form>
        </div>
      ) : null}
    </div>
  );
}
