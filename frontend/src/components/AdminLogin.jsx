import React, { useState } from 'react';
import './AdminLogin.css';

const BASE = 'http://localhost:8000/api/auth';

const VIEWS = { LOGIN: 'login', FORGOT: 'forgot', VERIFY: 'verify', RESET: 'reset', SETUP_Q: 'setup_q' };

const AdminLogin = ({ onSuccess, onClose }) => {
  const [view, setView]           = useState(VIEWS.LOGIN);
  const [email, setEmail]         = useState('');
  const [password, setPassword]   = useState('');
  const [answer, setAnswer]       = useState('');
  const [newPass, setNewPass]     = useState('');
  const [confirmPass, setConfirm] = useState('');
  const [resetToken, setResetToken]           = useState('');
  const [securityQuestion, setSecurityQuestion] = useState('');
  const [error, setError]         = useState('');
  const [loading, setLoading]     = useState(false);
  const [showPass, setShowPass]   = useState(false);

  const api = async (path, body) => {
    const res = await fetch(`${BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Request failed');
    return data;
  };

  const clearError = () => setError('');

  // ── Login ──────────────────────────────────
  const handleLogin = async (e) => {
    e.preventDefault();
    clearError();
    if (!email || !password) { setError('Please fill in all fields.'); return; }
    setLoading(true);
    try {
      const data = await api('/login', { email, password });
      localStorage.setItem('adminToken', data.access_token);
      localStorage.setItem('adminName', data.admin_name);
      onSuccess(data.access_token, data.admin_name);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ── Forgot: fetch security question ────────
  const handleForgot = async (e) => {
    e.preventDefault();
    clearError();
    if (!email) { setError('Please enter your email.'); return; }
    setLoading(true);
    try {
      const data = await api('/forgot-password', { email });
      setSecurityQuestion(data.security_question);
      setView(VIEWS.VERIFY);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ── Verify answer ──────────────────────────
  const handleVerify = async (e) => {
    e.preventDefault();
    clearError();
    if (!answer) { setError('Please enter your answer.'); return; }
    setLoading(true);
    try {
      const data = await api('/verify-answer', { email, security_answer: answer.trim().toLowerCase() });
      setResetToken(data.reset_token);
      setView(VIEWS.RESET);
    } catch (err) {
      setError('Incorrect answer. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // ── Reset password ─────────────────────────
  const handleReset = async (e) => {
    e.preventDefault();
    clearError();
    if (newPass !== confirmPass) { setError('Passwords do not match.'); return; }
    if (newPass.length < 8)      { setError('Password must be at least 8 characters.'); return; }
    setLoading(true);
    try {
      await api('/reset-password', { reset_token: resetToken, new_password: newPass });
      setView(VIEWS.LOGIN);
      setPassword('');
      setError('');
      alert('✅ Password reset successfully! Please log in with your new password.');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-overlay">
      <div className="admin-login-card">
        {/* Header */}
        <div className="admin-login-header">
          {onClose && (
            <button
              type="button"
              className="admin-login-close"
              onClick={onClose}
              aria-label="Close login dialog"
            >✕</button>
          )}
          <div className="admin-login-icon">🛡️</div>
          <h1 className="admin-login-title">Admin Access</h1>
          <p className="admin-login-subtitle">
            {view === VIEWS.LOGIN  && 'Sign in to manage EduVerse'}
            {view === VIEWS.FORGOT && 'Recover your account'}
            {view === VIEWS.VERIFY && 'Answer your security question'}
            {view === VIEWS.RESET  && 'Set a new password'}
          </p>
        </div>

        {/* Error */}
        {error && (
          <div className="admin-login-error">
            <span>⚠️ {error}</span>
          </div>
        )}

        {/* ── LOGIN VIEW ── */}
        {view === VIEWS.LOGIN && (
          <form onSubmit={handleLogin} className="admin-login-form">
            <div className="admin-field">
              <label>Email</label>
              <input
                type="email" value={email} onChange={e => setEmail(e.target.value)}
                placeholder="admin@eduverse.edu" autoFocus
              />
            </div>
            <div className="admin-field">
              <label>Password</label>
              <div className="admin-pass-wrap">
                <input
                  type={showPass ? 'text' : 'password'}
                  value={password} onChange={e => setPassword(e.target.value)}
                  placeholder="Enter your password"
                />
                <button type="button" className="admin-pass-toggle"
                  onClick={() => setShowPass(v => !v)}>
                  {showPass ? '🙈' : '👁️'}
                </button>
              </div>
            </div>
            <button type="submit" className="admin-login-btn" disabled={loading}>
              {loading ? <span className="admin-spinner" /> : '🔓 Sign In'}
            </button>
            <button type="button" className="admin-link-btn"
              onClick={() => { clearError(); setView(VIEWS.FORGOT); }}>
              Forgot password?
            </button>
          </form>
        )}

        {/* ── FORGOT VIEW ── */}
        {view === VIEWS.FORGOT && (
          <form onSubmit={handleForgot} className="admin-login-form">
            <div className="admin-field">
              <label>Admin Email</label>
              <input
                type="email" value={email} onChange={e => setEmail(e.target.value)}
                placeholder="admin@eduverse.edu" autoFocus
              />
            </div>
            <button type="submit" className="admin-login-btn" disabled={loading}>
              {loading ? <span className="admin-spinner" /> : '🔍 Get Security Question'}
            </button>
            <button type="button" className="admin-link-btn"
              onClick={() => { clearError(); setView(VIEWS.LOGIN); }}>
              ← Back to Login
            </button>
          </form>
        )}

        {/* ── VERIFY VIEW ── */}
        {view === VIEWS.VERIFY && (
          <form onSubmit={handleVerify} className="admin-login-form">
            <div className="admin-security-question">
              <span className="sq-icon">🔐</span>
              <p>{securityQuestion}</p>
            </div>
            <div className="admin-field">
              <label>Your Answer</label>
              <input
                type="text" value={answer} onChange={e => setAnswer(e.target.value)}
                placeholder="Type your answer (case-insensitive)" autoFocus
              />
            </div>
            <button type="submit" className="admin-login-btn" disabled={loading}>
              {loading ? <span className="admin-spinner" /> : '✅ Verify Answer'}
            </button>
            <button type="button" className="admin-link-btn"
              onClick={() => { clearError(); setView(VIEWS.FORGOT); }}>
              ← Back
            </button>
          </form>
        )}

        {/* ── RESET VIEW ── */}
        {view === VIEWS.RESET && (
          <form onSubmit={handleReset} className="admin-login-form">
            <div className="admin-field">
              <label>New Password</label>
              <input
                type="password" value={newPass} onChange={e => setNewPass(e.target.value)}
                placeholder="At least 8 characters" autoFocus
              />
            </div>
            <div className="admin-field">
              <label>Confirm Password</label>
              <input
                type="password" value={confirmPass} onChange={e => setConfirm(e.target.value)}
                placeholder="Re-enter new password"
              />
            </div>
            <div className="admin-pass-strength">
              {newPass.length > 0 && (
                <div className={`strength-bar ${newPass.length >= 12 ? 'strong' : newPass.length >= 8 ? 'medium' : 'weak'}`} />
              )}
              {newPass.length >= 8 && <span className="strength-label">
                {newPass.length >= 12 ? '💪 Strong' : '✅ Acceptable'}
              </span>}
            </div>
            <button type="submit" className="admin-login-btn" disabled={loading}>
              {loading ? <span className="admin-spinner" /> : '🔑 Reset Password'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
};

export default AdminLogin;
