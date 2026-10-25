import React, { useState } from 'react';
import DeepfakeScannerModal from './components/DeepfakeScannerModal';
import EmergencySOSModal from './components/EmergencySOSModal';
import TellOnceModal from './components/TellOnceModal';
import Dashboard from './Dashboard';

/**
 * SafeMate Main Application Root Page
 * 
 * Satisfies Wiring Requirements:
 * 1. Import Components: DeepfakeScannerModal, EmergencySOSModal, TellOnceModal
 * 2. State Management: isDeepfakeModalOpen, isSosModalOpen, isTellOnceModalOpen
 * 3. Attach Triggers: Dashboard card triggers open corresponding modals
 * 4. Render Modals: Rendered at the root level of page layout
 */
export default function App() {
  const [isDeepfakeModalOpen, setIsDeepfakeModalOpen] = useState(false);
  const [isSosModalOpen, setIsSosModalOpen] = useState(false);
  const [isTellOnceModalOpen, setIsTellOnceModalOpen] = useState(false);

  return (
    <div className="safemate-app-root">
      <Dashboard 
        onOpenDeepfake={() => setIsDeepfakeModalOpen(true)}
        onOpenSos={() => setIsSosModalOpen(true)}
        onOpenTellOnce={() => setIsTellOnceModalOpen(true)}
      />
      
      {/* Root-Level Workspace Modals */}
      <TellOnceModal
        isOpen={isTellOnceModalOpen}
        onClose={() => setIsTellOnceModalOpen(false)}
      />

      <DeepfakeScannerModal
        isOpen={isDeepfakeModalOpen}
        onClose={() => setIsDeepfakeModalOpen(false)}
      />

      <EmergencySOSModal
        isOpen={isSosModalOpen}
        onClose={() => setIsSosModalOpen(false)}
      />
    </div>
  );
}
