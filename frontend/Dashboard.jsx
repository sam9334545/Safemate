import React, { useState } from 'react';
import DeepfakeScannerModal from './components/DeepfakeScannerModal';
import EmergencySOSModal from './components/EmergencySOSModal';
import TellOnceModal from './components/TellOnceModal';

/**
 * SafeMate Main Dashboard Component
 * 
 * Connected Workspaces & Modals:
 * 1. AI Deepfake & Manipulation Detector -> DeepfakeScannerModal (via isDeepfakeModalOpen state)
 * 2. Emergency SOS & Instant Real Calling -> EmergencySOSModal (via isSosModalOpen state)
 * 3. Tell-Once Intake (बोलें या लिखें - सिर्फ एक बार) -> TellOnceModal (via isTellOnceModalOpen state)
 */
export default function Dashboard({ 
  apiBaseUrl = 'http://localhost:8000',
  onOpenDeepfake,
  onOpenSos,
  onOpenTellOnce
}) {
  // Reactive boolean state for modals
  const [isDeepfakeModalOpen, setIsDeepfakeModalOpen] = useState(false);
  const [isSosModalOpen, setIsSosModalOpen] = useState(false);
  const [isTellOnceModalOpen, setIsTellOnceModalOpen] = useState(false);
  const [activeFilter, setActiveFilter] = useState('all');

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
      badge: 'Emergency Response',
      badgeBg: 'rgba(15, 23, 42, 0.92)',
      title: 'Emergency SOS & Instant Real Calling',
      desc: 'Direct connection to 112 emergency dispatchers or your trusted safety circle, with verified real-time GPS coordinate broadcasting.',
      tags: ['Call 112', 'Live GPS Broadcast', 'Safe Circle'],
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
      tags: ['Auto Countdown', 'Shareable Trip Token', 'Arrival Check-In'],
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
      tags: ['Covert Audio', 'GPS & Timestamp Stamp', 'Calculator Disguise'],
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
      <header className="navbar" id="navbar" style={{ borderBottom: '1px solid #e2e8f0', padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '6px', backgroundColor: '#090d16', color: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            🛡️
          </div>
          <div>
            <h1 style={{ fontSize: '1.15rem', fontWeight: 800, margin: 0, letterSpacing: '-0.01em' }}>SafeMate</h1>
            <span style={{ fontSize: '0.72rem', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Confidential Survivor Shield</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button 
            type="button" 
            onClick={handleOpenSos}
            style={{ backgroundColor: '#be123c', color: '#ffffff', border: 'none', borderRadius: '6px', padding: '8px 16px', fontSize: '0.82rem', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
          >
            <span>🚨</span>
            <span>Emergency 112</span>
          </button>
        </div>
      </header>

      {/* Hero Motto Section */}
      <section style={{ backgroundColor: '#fafaf9', borderBottom: '1px solid #e2e8f0', padding: '40px 24px', textAlign: 'center' }}>
        <div style={{ maxWidth: '720px', margin: '0 auto' }}>
          <span style={{ fontSize: '0.74rem', fontWeight: 800, color: '#881337', textTransform: 'uppercase', letterSpacing: '0.08em', display: 'block', marginBottom: '8px' }}>
            FREE, CONFIDENTIAL &amp; TRAUMA-INFORMED PLATFORM
          </span>
          <p style={{ fontSize: '1.05rem', lineHeight: '1.6', color: '#334155', margin: 0, fontFamily: "'Karma', 'Alice', Georgia, serif" }}>
            SafeMate is a confidential, trauma-informed digital safety platform that primarily helps women, youth, and families facing domestic violence, intimate image abuse, deepfakes, cyberstalking, or immediate physical distress.
          </p>
        </div>
      </section>

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

    </div>
  );
}
