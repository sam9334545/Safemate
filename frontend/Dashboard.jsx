import React, { useState, useEffect } from 'react';
import DeepfakeScannerModal from './components/DeepfakeScannerModal';
import EmergencySOSModal from './components/EmergencySOSModal';
import TellOnceModal from './components/TellOnceModal';
import authState from './authState.js';
import * as demoData from './demoData.js';

/**
 * SafeMate Main Dashboard Component
 * 
 * Supports 3 Distinguishable Access Modes:
 *  - Mode A: Personal Account (Registered user with private data isolation)
 *  - Mode B: Guest Mode (Scoped ephemeral session)
 *  - Mode C: Judge Demo Mode (Instant zero-friction evaluator experience with realistic sample data)
 */
export default function Dashboard({ 
  apiBaseUrl = 'http://localhost:8000',
  onOpenDeepfake,
  onOpenSos,
  onOpenTellOnce
}) {
  // Reactive boolean state for workspace modals
  const [isDeepfakeModalOpen, setIsDeepfakeModalOpen] = useState(false);
  const [isSosModalOpen, setIsSosModalOpen] = useState(false);
  const [isTellOnceModalOpen, setIsTellOnceModalOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState('all');

  // Centralized Auth State
  const [auth, setAuth] = useState(authState.getState());
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const [authTab, setAuthTab] = useState('login'); // 'login' | 'register'
  const [authEmail, setAuthEmail] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authConfirmPassword, setAuthConfirmPassword] = useState('');
  const [authFullName, setAuthFullName] = useState('');
  const [authError, setAuthError] = useState(null);
  const [authLoading, setAuthLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    const unsubscribe = authState.subscribe((st) => setAuth(st));
    authState.init().catch(err => console.warn('Dashboard auth init error:', err));
    return unsubscribe;
  }, []);

  const handleOpenDeepfake = () => {
    setIsDeepfakeModalOpen(true);
    if (onOpenDeepfake) onOpenDeepfake();
    if (typeof window !== 'undefined' && window.openWorkspaceModal) {
      window.openWorkspaceModal('modal-feature-deepfake');
    }
  };

  const handleOpenSos = () => {
    setIsSosModalOpen(true);
    if (onOpenSos) onOpenSos();
    if (typeof window !== 'undefined' && window.openWorkspaceModal) {
      window.openWorkspaceModal('modal-feature-sos');
    }
  };

  const handleOpenTellOnce = () => {
    setIsTellOnceModalOpen(true);
    if (onOpenTellOnce) onOpenTellOnce();
    if (typeof window !== 'undefined' && window.openWorkspaceModal) {
      window.openWorkspaceModal('tell-once-modal');
    }
  };

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setAuthLoading(true);
    setAuthError(null);
    try {
      await authState.login(authEmail, authPassword);
      setIsAuthModalOpen(false);
      setAuthEmail('');
      setAuthPassword('');
    } catch (err) {
      setAuthError(err.message || 'Login failed. You can use "Try Demo Mode" to explore without an account.');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    if (authPassword !== authConfirmPassword) {
      setAuthError('Passwords do not match.');
      return;
    }
    if (authPassword.length < 8) {
      setAuthError('Password must be at least 8 characters long.');
      return;
    }
    setAuthLoading(true);
    setAuthError(null);
    try {
      await authState.register(authEmail, authPassword, authFullName);
      setIsAuthModalOpen(false);
      setAuthEmail('');
      setAuthPassword('');
      setAuthConfirmPassword('');
    } catch (err) {
      setAuthError(err.message || 'Registration failed. You can use "Try Demo Mode" instead.');
    } finally {
      setAuthLoading(false);
    }
  };

  const isDemo = auth.accessMode === 'demo';

  const tools = [
    {
      id: 'tell-once-section',
      cat: 'tell-once',
      badge: 'Tell-Once • Trauma-Informed',
      badgeBg: '#881337',
      title: 'Tell-Once Intake (बोलें या लिखें - सिर्फ एक बार)',
      desc: 'Speak or type once. Our trauma-informed assistant asks one gentle question at a time and automatically generates your Police Zero FIR, 1930 Cyber Brief, and Lawyer Summary.',
      tags: ['Trauma-Informed', '🇮🇳 Hindi & English', '3-in-1 Unified Dossier'],
      btnText: 'Open Tell-Once Intake',
      onClick: handleOpenTellOnce
    },
    {
      id: 'sos-section',
      cat: 'emergency',
      badge: isDemo ? 'Emergency SOS (Simulated Demo)' : 'Emergency Response',
      badgeBg: isDemo ? '#d97706' : 'rgba(15, 23, 42, 0.92)',
      title: 'Emergency SOS & Instant Real Calling',
      desc: isDemo 
        ? 'DEMO MODE: Simulated emergency response with verified sample GPS fix. Will NOT trigger real telephone calls or emergency dispatch.'
        : 'Direct connection to 112 emergency dispatchers or your trusted safety circle, with verified real-time GPS coordinate broadcasting.',
      tags: isDemo ? ['[DEMO DATA]', 'Safe Simulation', 'No Real Calls'] : ['Call 112', 'Live GPS Broadcast', 'Safe Circle'],
      btnText: 'Open Emergency SOS',
      onClick: handleOpenSos
    },
    {
      id: 'safewalk-section',
      cat: 'safewalk',
      badge: 'Personal Escort',
      badgeBg: '#0284c7',
      title: 'SafeWalk Escort & Live Tracking',
      desc: "Walking home alone? Generate a live route monitoring link for friends with an automatic countdown alert if you don't check in on arrival.",
      tags: isDemo ? ['[DEMO DATA]', 'Simulated Escort', 'Breadcrumbs'] : ['Auto Countdown', 'Shareable Trip Token', 'Arrival Check-In'],
      btnText: 'Open SafeWalk Escort',
      onClick: () => {
        if (typeof window !== 'undefined' && window.openWorkspaceModal) {
          window.openWorkspaceModal('modal-feature-safewalk');
        }
      }
    },
    {
      id: 'deepfake-section',
      cat: 'deepfake',
      badge: 'Neural AI Forensics',
      badgeBg: '#059669',
      title: 'AI Deepfake & Manipulation Detector',
      desc: 'Verify whether received photos, morphed screenshots, or videos have been synthetically altered or face-swapped using neural classification.',
      tags: ['Dual AI Models', 'Image & Video Scan', 'Confidence Verdict'],
      btnText: 'OPEN DEEPFAKE SCANNER',
      onClick: handleOpenDeepfake
    },
    {
      id: 'leak-section',
      cat: 'leak',
      badge: 'Leak Tracer',
      badgeBg: '#d97706',
      title: 'Leak Tracer (Invisible Watermarking)',
      desc: 'Embed imperceptible cryptographic recipient signatures before sharing photos. If a photo leaks, extract the watermark to pinpoint who shared it.',
      tags: ['Invisible Signatures', 'Batch ZIP Export', 'Leaker Attribution'],
      btnText: 'Open Leak Tracer',
      onClick: () => {
        if (typeof window !== 'undefined' && window.openWorkspaceModal) {
          window.openWorkspaceModal('modal-feature-leak');
        }
      }
    },
    {
      id: 'vault-section',
      cat: 'vault',
      badge: 'Evidence Locker',
      badgeBg: '#475569',
      title: 'Disguised Evidence Vault',
      desc: 'Discreetly record incident audio or upload files stamped with cryptographic SHA-256 signatures, hidden behind an innocent calculator disguise.',
      tags: isDemo ? ['[DEMO DATA]', '4 Sealed Samples', 'SHA-256 Verified'] : ['Covert Audio', 'GPS & Timestamp Stamp', 'Calculator Disguise'],
      btnText: 'Open Evidence Vault',
      onClick: () => {
        if (typeof window !== 'undefined' && window.openWorkspaceModal) {
          window.openWorkspaceModal('modal-feature-vault');
        }
      }
    },
    {
      id: 'chatbot-section',
      cat: 'chatbot',
      badge: 'Legal & Trauma AI',
      badgeBg: '#4f46e5',
      title: 'Confidential Legal & Rights Assistant',
      desc: 'Ask questions about domestic violence laws, cyber harassment remedies, protection orders, or emergency safe shelter rights anonymously.',
      tags: ['BNS / CrPC / IT Act', 'Trauma-Trained', 'Zero Trace'],
      btnText: 'Open Legal Chatbot',
      onClick: () => {
        if (typeof window !== 'undefined' && window.openWorkspaceModal) {
          window.openWorkspaceModal('chatbot-modal');
        }
      }
    }
  ];

  const filteredTools = activeFilter === 'all' 
    ? tools 
    : tools.filter((t) => t.cat === activeFilter);

  return (
    <div className="safemate-dashboard-layout" style={{ minHeight: '100vh', backgroundColor: '#ffffff', color: '#0f172a', fontFamily: "'Inter', sans-serif" }}>
      
      {/* Top Navbar */}
      <header className="navbar" id="navbar" style={{ borderBottom: '1px solid #e2e8f0', padding: '12px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', backgroundColor: '#ffffff' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '34px', height: '34px', borderRadius: '8px', backgroundColor: '#090d16', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            🛡️
          </div>
          <div>
            <h1 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0, letterSpacing: '-0.02em', color: '#0f172a' }}>SafeMate</h1>
            <span style={{ fontSize: '0.68rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.04em', fontWeight: 700 }}>Confidential Survivor Shield</span>
          </div>
        </div>

        {/* Access Mode Switcher & Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {isDemo ? (
            <>
              <span style={{ backgroundColor: '#fffbeb', color: '#92400e', border: '1px solid #f59e0b', padding: '6px 12px', borderRadius: '4px', fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.03em', textTransform: 'uppercase' }}>
                Demo Mode
              </span>
              <button
                type="button"
                onClick={() => authState.exitDemoMode()}
                style={{ backgroundColor: 'transparent', color: '#0f172a', border: '1px solid #cbd5e1', borderRadius: '4px', padding: '8px 13px', fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer' }}
              >
                Exit Demo
              </button>
            </>
          ) : auth.accessMode === 'guest' ? (
            <>
              <span style={{ backgroundColor: '#f0f9ff', color: '#0369a1', border: '1px solid #38bdf8', padding: '6px 12px', borderRadius: '4px', fontSize: '0.78rem', fontWeight: 700, letterSpacing: '0.03em', textTransform: 'uppercase' }}>
                Guest Mode
              </span>
              <button
                type="button"
                onClick={() => authState.enterDemoMode()}
                style={{ backgroundColor: '#0f172a', color: '#ffffff', border: '1px solid #0f172a', borderRadius: '4px', padding: '8px 14px', fontSize: '0.82rem', fontWeight: 700, cursor: 'pointer' }}
              >
                Try Demo Mode
              </button>
              <button
                type="button"
                onClick={() => { setAuthTab('login'); setIsAuthModalOpen(true); }}
                style={{ backgroundColor: 'transparent', color: '#0f172a', border: '1px solid #cbd5e1', borderRadius: '4px', padding: '8px 13px', fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer' }}
              >
                Sign In
              </button>
            </>
          ) : auth.accessMode === 'authenticated' ? (
            <>
              <span style={{ backgroundColor: '#ecfdf5', color: '#065f46', border: '1px solid #34d399', padding: '6px 12px', borderRadius: '4px', fontSize: '0.78rem', fontWeight: 700 }}>
                {auth.user?.email || 'Personal Account'}
              </span>
              <button
                type="button"
                onClick={() => authState.logout()}
                style={{ backgroundColor: 'transparent', color: '#0f172a', border: '1px solid #cbd5e1', borderRadius: '4px', padding: '8px 13px', fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer' }}
              >
                Sign Out
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                onClick={() => authState.enterDemoMode()}
                style={{ backgroundColor: '#0f172a', color: '#ffffff', border: '1px solid #0f172a', borderRadius: '4px', padding: '8px 14px', fontSize: '0.82rem', fontWeight: 700, letterSpacing: '0.02em', cursor: 'pointer', boxShadow: '0 1px 3px rgba(15, 23, 42, 0.12)' }}
              >
                Try Demo Mode
              </button>
              <button
                type="button"
                onClick={() => authState.enterGuestMode()}
                style={{ backgroundColor: '#f8fafc', color: '#334155', border: '1px solid #cbd5e1', borderRadius: '4px', padding: '8px 13px', fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer' }}
              >
                Guest Mode
              </button>
              <button
                type="button"
                onClick={() => { setAuthTab('login'); setIsAuthModalOpen(true); }}
                style={{ backgroundColor: 'transparent', color: '#0f172a', border: '1px solid #cbd5e1', borderRadius: '4px', padding: '8px 13px', fontSize: '0.82rem', fontWeight: 600, cursor: 'pointer' }}
              >
                Sign In
              </button>
            </>
          )}

          <button 
            type="button" 
            onClick={handleOpenSos}
            style={{ backgroundColor: isDemo ? '#78350f' : '#881337', color: '#ffffff', border: '1.5px solid', borderColor: isDemo ? '#78350f' : '#881337', borderRadius: '4px', padding: '8px 16px', fontSize: '0.82rem', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '7px', boxShadow: '0 2px 8px rgba(136, 19, 55, 0.25)' }}
          >
            <span>{isDemo ? 'Simulated SOS' : 'Emergency 112'}</span>
          </button>
        </div>
      </header>

      {/* Judge Demo Banner */}
      {isDemo && (
        <div style={{ backgroundColor: '#FFFBEB', borderBottom: '2px solid #F59E0B', padding: '10px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <span style={{ backgroundColor: '#F59E0B', color: '#000000', fontWeight: 900, fontSize: '0.72rem', padding: '3px 8px', borderRadius: '4px', textTransform: 'uppercase' }}>
              DEMO MODE
            </span>
            <span style={{ fontSize: '0.84rem', color: '#78350F', fontWeight: 600 }}>
              Operating with verified fictional sample data. Emergency SOS is simulated and will NOT contact real emergency services or contacts.
            </span>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button
              type="button"
              onClick={() => { setAuthTab('login'); setIsAuthModalOpen(true); }}
              style={{ backgroundColor: '#ffffff', border: '1px solid #D97706', color: '#92400E', padding: '5px 12px', borderRadius: '6px', fontSize: '0.78rem', fontWeight: 700, cursor: 'pointer' }}
            >
              Sign In to Account
            </button>
            <button
              type="button"
              onClick={() => authState.exitDemoMode()}
              style={{ backgroundColor: 'transparent', border: 'none', color: '#B45309', padding: '5px 8px', fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer' }}
            >
              ✕ Exit Demo
            </button>
          </div>
        </div>
      )}

      {/* Hero Motto Section */}
      <section style={{ backgroundColor: '#fafaf9', borderBottom: '1px solid #e2e8f0', padding: '36px 24px', textAlign: 'center' }}>
        <div style={{ maxWidth: '720px', margin: '0 auto' }}>
          <span style={{ fontSize: '0.74rem', fontWeight: 800, color: '#881337', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block', marginBottom: '8px' }}>
            FREE, CONFIDENTIAL &amp; TRAUMA-INFORMED PLATFORM
          </span>
          <p style={{ fontSize: '1.05rem', lineHeight: '1.6', color: '#334155', margin: 0, fontFamily: "'Karma', 'Alice', Georgia, serif" }}>
            SafeMate is a confidential, trauma-informed digital safety platform that primarily helps women, youth, and families facing domestic violence, intimate image abuse, deepfakes, cyberstalking, or immediate physical distress.
          </p>
        </div>
      </section>

      {/* Demo Metrics Overview Cards (Rendered when in Demo Mode) */}
      {isDemo && (
        <section style={{ maxWidth: '1200px', margin: '24px auto 0 auto', padding: '0 20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '16px' }}>
            <div style={{ backgroundColor: '#ffffff', border: '1.5px solid #F59E0B', borderRadius: '10px', padding: '16px', boxShadow: '0 2px 8px rgba(245, 158, 11, 0.1)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#92400E', textTransform: 'uppercase' }}>Safety Readiness</span>
                <span style={{ backgroundColor: '#FEF3C7', color: '#92400E', fontSize: '0.65rem', fontWeight: 800, padding: '2px 6px', borderRadius: '4px' }}>DEMO</span>
              </div>
              <div style={{ fontSize: '1.8rem', fontWeight: 900, color: '#090d16', marginTop: '6px' }}>96%</div>
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>4/4 Protection Modules Active</div>
            </div>

            <div style={{ backgroundColor: '#ffffff', border: '1.5px solid #F59E0B', borderRadius: '10px', padding: '16px', boxShadow: '0 2px 8px rgba(245, 158, 11, 0.1)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#92400E', textTransform: 'uppercase' }}>Evidence Vault</span>
                <span style={{ backgroundColor: '#FEF3C7', color: '#92400E', fontSize: '0.65rem', fontWeight: 800, padding: '2px 6px', borderRadius: '4px' }}>DEMO</span>
              </div>
              <div style={{ fontSize: '1.8rem', fontWeight: 900, color: '#090d16', marginTop: '6px' }}>4 Sealed</div>
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Cryptographic SHA-256 Hashes</div>
            </div>

            <div style={{ backgroundColor: '#ffffff', border: '1.5px solid #F59E0B', borderRadius: '10px', padding: '16px', boxShadow: '0 2px 8px rgba(245, 158, 11, 0.1)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#92400E', textTransform: 'uppercase' }}>SafeWalk Escort</span>
                <span style={{ backgroundColor: '#FEF3C7', color: '#92400E', fontSize: '0.65rem', fontWeight: 800, padding: '2px 6px', borderRadius: '4px' }}>SIMULATED</span>
              </div>
              <div style={{ fontSize: '1.8rem', fontWeight: 900, color: '#090d16', marginTop: '6px' }}>1 Active</div>
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>North Campus Residence Walk</div>
            </div>

            <div style={{ backgroundColor: '#ffffff', border: '1.5px solid #F59E0B', borderRadius: '10px', padding: '16px', boxShadow: '0 2px 8px rgba(245, 158, 11, 0.1)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.72rem', fontWeight: 800, color: '#92400E', textTransform: 'uppercase' }}>Safety Circle</span>
                <span style={{ backgroundColor: '#FEF3C7', color: '#92400E', fontSize: '0.65rem', fontWeight: 800, padding: '2px 6px', borderRadius: '4px' }}>SAMPLE</span>
              </div>
              <div style={{ fontSize: '1.8rem', fontWeight: 900, color: '#090d16', marginTop: '6px' }}>3 Guardians</div>
              <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Priya, Legal Counsel, Campus Cell</div>
            </div>
          </div>
        </section>
      )}

      {/* Safety & Legal Hub Section */}
      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '36px 20px' }}>
        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
            Safety &amp; Legal Hub
          </span>
          <h2 style={{ fontSize: '1.75rem', fontWeight: 800, color: '#090d16', marginTop: '4px', letterSpacing: '-0.02em' }}>
            Designed for Real Situations
          </h2>
          <p style={{ fontSize: '0.88rem', color: '#64748b', marginTop: '4px' }}>
            Click any tool below to open its dedicated, distraction-free workspace.
          </p>
        </div>

        {/* Category Filter Tabs */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', justifyContent: 'center', marginBottom: '32px' }}>
          {[
            { id: 'all', label: 'All Tools (7)' },
            { id: 'tell-once', label: 'Tell-Once' },
            { id: 'emergency', label: 'Emergency SOS' },
            { id: 'safewalk', label: 'SafeWalk' },
            { id: 'deepfake', label: 'Deepfake Scan' },
            { id: 'vault', label: 'Evidence Vault' },
            { id: 'leak', label: 'Leak Tracer' },
            { id: 'chatbot', label: 'Legal Chatbot' }
          ].map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => setActiveFilter(tab.id)}
              style={{
                padding: '8px 16px',
                fontSize: '0.8rem',
                fontWeight: activeFilter === tab.id ? 700 : 500,
                color: activeFilter === tab.id ? '#ffffff' : '#334155',
                backgroundColor: activeFilter === tab.id ? '#090d16' : '#f1f5f9',
                border: '1px solid',
                borderColor: activeFilter === tab.id ? '#090d16' : '#cbd5e1',
                borderRadius: '6px',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Feature Cards Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: '20px' }}>
          {filteredTools.map((tool) => (
            <div
              key={tool.id}
              id={tool.id}
              className="feature-card-tile"
              onClick={tool.onClick}
              style={{
                backgroundColor: '#ffffff',
                border: '1.5px solid #e2e8f0',
                borderRadius: '10px',
                padding: '24px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                cursor: 'pointer',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.03)',
                transition: 'all 0.18s ease'
              }}
            >
              <div>
                <span
                  style={{
                    backgroundColor: tool.badgeBg,
                    color: '#ffffff',
                    fontSize: '0.68rem',
                    fontWeight: 700,
                    textTransform: 'uppercase',
                    letterSpacing: '0.04em',
                    padding: '4px 10px',
                    borderRadius: '4px',
                    display: 'inline-block',
                    marginBottom: '14px'
                  }}
                >
                  {tool.badge}
                </span>

                <h3 style={{ fontSize: '1.18rem', fontWeight: 700, color: '#090d16', margin: '0 0 8px 0', letterSpacing: '-0.01em' }}>
                  {tool.title}
                </h3>

                <p style={{ fontSize: '0.84rem', lineHeight: '1.55', color: '#475569', margin: '0 0 16px 0' }}>
                  {tool.desc}
                </p>

                {/* Tags */}
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginBottom: '20px' }}>
                  {tool.tags.map((tag, idx) => (
                    <span
                      key={idx}
                      style={{
                        backgroundColor: '#f1f5f9',
                        color: '#334155',
                        fontSize: '0.72rem',
                        fontWeight: 600,
                        padding: '3px 8px',
                        borderRadius: '4px',
                        border: '1px solid #e2e8f0'
                      }}
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              {/* Action Button */}
              <button
                type="button"
                className="btn-open-workspace"
                onClick={(e) => {
                  e.stopPropagation();
                  tool.onClick();
                }}
                style={{
                  width: '100%',
                  padding: '12px 16px',
                  backgroundColor: '#090d16',
                  color: '#ffffff',
                  border: '1px solid #090d16',
                  borderRadius: '6px',
                  fontSize: '0.82rem',
                  fontWeight: 700,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  cursor: 'pointer'
                }}
              >
                <span>{tool.btnText}</span>
                <span style={{ fontSize: '1rem' }}>→</span>
              </button>
            </div>
          ))}
        </div>
      </main>

      {/* Render Workspace Modals at Root Level via React State */}
      <TellOnceModal
        isOpen={isTellOnceModalOpen}
        onClose={() => setIsTellOnceModalOpen(false)}
        apiBaseUrl={apiBaseUrl}
      />

      <DeepfakeScannerModal
        isOpen={isDeepfakeModalOpen}
        onClose={() => setIsDeepfakeModalOpen(false)}
        apiBaseUrl={apiBaseUrl}
      />

      <EmergencySOSModal
        isOpen={isSosModalOpen}
        onClose={() => setIsSosModalOpen(false)}
        apiBaseUrl={apiBaseUrl}
      />

      {/* Interactive React Auth Modal */}
      {isAuthModalOpen && (
        <div style={{ position: 'fixed', inset: 0, backgroundColor: 'rgba(15, 23, 42, 0.65)', backdropFilter: 'blur(4px)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 10000, padding: '16px' }}>
          <div style={{ backgroundColor: '#ffffff', borderRadius: '16px', maxWidth: '480px', width: '100%', padding: '28px', border: '1px solid #e2e8f0', boxShadow: '0 25px 60px rgba(0,0,0,0.3)', position: 'relative' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div>
                <h3 style={{ margin: 0, fontSize: '1.25rem', fontWeight: 800, color: '#0f172a' }}>SafeMate Access Portal</h3>
                <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Confidential Survivor Shield</span>
              </div>
              <button 
                type="button" 
                onClick={() => setIsAuthModalOpen(false)}
                style={{ background: 'none', border: 'none', fontSize: '1.5rem', cursor: 'pointer', color: '#94a3b8' }}
              >
                &times;
              </button>
            </div>

            {/* Judge Fast Access Box */}
            <div style={{ background: 'linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%)', border: '1.5px solid #F59E0B', borderRadius: '10px', padding: '14px', marginBottom: '18px' }}>
              <span style={{ background: '#F59E0B', color: '#000000', fontSize: '0.68rem', fontWeight: 900, padding: '2px 6px', borderRadius: '4px', textTransform: 'uppercase' }}>
                JUDGE &amp; EVALUATOR FAST ACCESS
              </span>
              <p style={{ margin: '6px 0 10px 0', fontSize: '0.78rem', color: '#78350F', lineHeight: '1.4' }}>
                Explore all features instantly with realistic sample data. No registration or backend setup required.
              </p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => { authState.enterDemoMode(); setIsAuthModalOpen(false); }}
                  style={{ background: '#0f172a', border: '1px solid #0f172a', color: '#ffffff', padding: '9px 12px', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer', transition: 'all 0.2s ease' }}
                >
                  Try Demo Mode
                </button>
                <button
                  type="button"
                  onClick={() => { authState.enterGuestMode(); setIsAuthModalOpen(false); }}
                  style={{ background: '#f8fafc', border: '1px solid #cbd5e1', color: '#334155', padding: '9px 12px', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 600, cursor: 'pointer', transition: 'all 0.2s ease' }}
                >
                  Explore as Guest
                </button>
              </div>
            </div>

            <div style={{ display: 'flex', borderBottom: '1px solid #e2e8f0', marginBottom: '16px' }}>
              <button
                type="button"
                onClick={() => { setAuthTab('login'); setAuthError(null); }}
                style={{ flex: 1, padding: '10px', background: 'none', border: 'none', borderBottom: authTab === 'login' ? '2px solid #881337' : '2px solid transparent', color: authTab === 'login' ? '#881337' : '#64748b', fontWeight: authTab === 'login' ? 700 : 500, fontSize: '0.85rem', cursor: 'pointer' }}
              >
                Sign In
              </button>
              <button
                type="button"
                onClick={() => { setAuthTab('register'); setAuthError(null); }}
                style={{ flex: 1, padding: '10px', background: 'none', border: 'none', borderBottom: authTab === 'register' ? '2px solid #881337' : '2px solid transparent', color: authTab === 'register' ? '#881337' : '#64748b', fontWeight: authTab === 'register' ? 700 : 500, fontSize: '0.85rem', cursor: 'pointer' }}
              >
                Create Account
              </button>
            </div>

            {authError && (
              <div style={{ backgroundColor: '#FEF2F2', border: '1px solid #F87171', color: '#991B1B', padding: '10px 12px', borderRadius: '8px', fontSize: '0.8rem', marginBottom: '14px', lineHeight: '1.4' }}>
                {authError}
              </div>
            )}

            {authTab === 'login' ? (
              <form onSubmit={handleLoginSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#334155', display: 'block', marginBottom: '4px' }}>Email</label>
                  <input
                    type="email"
                    required
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    placeholder="user@example.com"
                    style={{ width: '100%', padding: '10px 12px', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.88rem', boxSizing: 'border-box' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#334155', display: 'block', marginBottom: '4px' }}>Password</label>
                  <div style={{ position: 'relative' }}>
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      value={authPassword}
                      onChange={(e) => setAuthPassword(e.target.value)}
                      placeholder="••••••••"
                      style={{ width: '100%', padding: '10px 12px', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.88rem', boxSizing: 'border-box' }}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', cursor: 'pointer' }}
                    >
                      {showPassword ? '🔒' : '👁'}
                    </button>
                  </div>
                </div>
                <button
                  type="submit"
                  disabled={authLoading}
                  style={{ marginTop: '8px', padding: '12px', backgroundColor: '#881337', color: '#ffffff', border: 'none', borderRadius: '8px', fontSize: '0.88rem', fontWeight: 700, cursor: 'pointer' }}
                >
                  {authLoading ? 'Verifying...' : 'Sign In to Personal Account'}
                </button>
              </form>
            ) : (
              <form onSubmit={handleRegisterSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#334155', display: 'block', marginBottom: '4px' }}>Full Name or Alias (Optional)</label>
                  <input
                    type="text"
                    value={authFullName}
                    onChange={(e) => setAuthFullName(e.target.value)}
                    placeholder="Survivor Alias"
                    style={{ width: '100%', padding: '10px 12px', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.88rem', boxSizing: 'border-box' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#334155', display: 'block', marginBottom: '4px' }}>Email</label>
                  <input
                    type="email"
                    required
                    value={authEmail}
                    onChange={(e) => setAuthEmail(e.target.value)}
                    placeholder="user@example.com"
                    style={{ width: '100%', padding: '10px 12px', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.88rem', boxSizing: 'border-box' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#334155', display: 'block', marginBottom: '4px' }}>Password (min. 8 characters)</label>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    minLength={8}
                    value={authPassword}
                    onChange={(e) => setAuthPassword(e.target.value)}
                    placeholder="••••••••"
                    style={{ width: '100%', padding: '10px 12px', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.88rem', boxSizing: 'border-box' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.78rem', fontWeight: 700, color: '#334155', display: 'block', marginBottom: '4px' }}>Confirm Password</label>
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    minLength={8}
                    value={authConfirmPassword}
                    onChange={(e) => setAuthConfirmPassword(e.target.value)}
                    placeholder="••••••••"
                    style={{ width: '100%', padding: '10px 12px', border: '1px solid #cbd5e1', borderRadius: '8px', fontSize: '0.88rem', boxSizing: 'border-box' }}
                  />
                </div>
                <button
                  type="submit"
                  disabled={authLoading}
                  style={{ marginTop: '8px', padding: '12px', backgroundColor: '#881337', color: '#ffffff', border: 'none', borderRadius: '8px', fontSize: '0.88rem', fontWeight: 700, cursor: 'pointer' }}
                >
                  {authLoading ? 'Creating Account...' : 'Create Confidential Account'}
                </button>
              </form>
            )}

            <div style={{ marginTop: '16px', paddingTop: '12px', borderTop: '1px solid #f1f5f9', textAlign: 'center', fontSize: '0.72rem', color: '#64748b' }}>
              🔒 100% Client-Side Privacy. Isolated credentials &amp; end-to-end data isolation.
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
