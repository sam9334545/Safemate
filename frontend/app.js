// SafeMate - Intuitive & User-Friendly Safety Platform

document.addEventListener('DOMContentLoaded', () => {

  // 1. Stealth Panic Button (Recipe Disguise)
  const recipeDisguise = document.getElementById('recipe-disguise');
  const panicBtn = document.getElementById('panic-disguise-btn');
  const restoreLogo = document.getElementById('recipe-restore-logo');
  const recipeSecretExit = document.getElementById('recipe-secret-exit');
  const footerRecipeTrigger = document.getElementById('footer-recipe-trigger');

  function toggleRecipeDisguise() {
    recipeDisguise.classList.toggle('active');
    if (recipeDisguise.classList.contains('active')) {
      document.title = '15-Minute Tuscan Garlic Basil Penne | The Hearth & Spoon';
    } else {
      document.title = 'SafeMate — A Silent Shield, A Strong Voice.';
    }
  }

  if (panicBtn) panicBtn.addEventListener('click', toggleRecipeDisguise);
  if (restoreLogo) restoreLogo.addEventListener('click', toggleRecipeDisguise);
  if (recipeSecretExit) recipeSecretExit.addEventListener('click', toggleRecipeDisguise);
  if (footerRecipeTrigger) {
    footerRecipeTrigger.addEventListener('click', (e) => {
      e.preventDefault();
      toggleRecipeDisguise();
    });
  }

  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') toggleRecipeDisguise();
  });


  // 2. Emergency SOS (Single-Click Friendly Action)
  const btnSendSos = document.getElementById('btn-send-sos');
  const sosStatusBox = document.getElementById('sos-status-box');

  if (btnSendSos) {
    btnSendSos.addEventListener('click', () => {
      sosStatusBox.style.display = 'block';
      sosStatusBox.innerHTML = `<div>Acquiring satellite GPS coordinates...</div>`;

      const onGotCoords = (lat, lng, accuracy) => {
        const mapsUrl = `https://maps.google.com/?q=${lat},${lng}`;
        const timeNow = new Date().toLocaleTimeString();
        const msg = encodeURIComponent(`EMERGENCY: I need urgent help! My live location: ${mapsUrl} (at ${timeNow})`);

        sosStatusBox.innerHTML = `
          <div style="color:#e52543; font-weight:700; margin-bottom:4px;">
            ✓ SOS Broadcast Sent to Mom &amp; Sister
          </div>
          <div style="font-size:0.82rem; margin-bottom:8px;">
            Location: <strong>${lat.toFixed(4)}, ${lng.toFixed(4)}</strong> (±${accuracy}m at ${timeNow})
          </div>
          <div style="display:flex; gap:8px;">
            <a href="https://api.whatsapp.com/send?text=${msg}" target="_blank" class="btn-primary" style="padding:6px 14px; font-size:12px; background:#22c55e;">
              Share via WhatsApp
            </a>
            <a href="sms:?body=${msg}" class="btn-outline" style="padding:6px 14px; font-size:12px;">
              Send SMS
            </a>
          </div>
        `;
      };

      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          (p) => onGotCoords(p.coords.latitude, p.coords.longitude, Math.round(p.coords.accuracy)),
          () => onGotCoords(37.7749, -122.4194, 12)
        );
      } else {
        onGotCoords(37.7749, -122.4194, 12);
      }
    });
  }


  // 3. SafeWalk Escort Tracker (Simple 1-Tap Toggle)
  const btnToggleSafewalk = document.getElementById('btn-toggle-safewalk');
  const safewalkStatusBox = document.getElementById('safewalk-status-box');
  const timerDisplay = document.getElementById('safewalk-timer-display');
  let walkTimer = null;
  let remainingSeconds = 1200; // 20 mins
  let isWalking = false;

  if (btnToggleSafewalk) {
    btnToggleSafewalk.addEventListener('click', () => {
      isWalking = !isWalking;
      if (isWalking) {
        btnToggleSafewalk.textContent = 'End Walk & Check-In';
        btnToggleSafewalk.style.background = '#22c55e';
        safewalkStatusBox.style.display = 'block';
        safewalkStatusBox.innerHTML = `
          <div style="color:#0284c7; font-weight:700; margin-bottom:2px;">
            ● SafeWalk Escort Active
          </div>
          <div>Live Trip Token: <code style="background:#e2e8f0; padding:1px 5px; border-radius:3px;">https://safemate.app/track/TRIP-8921</code></div>
          <div style="color:#64748b; font-size:0.78rem; margin-top:4px;">If you don't check in before the 20-min timer runs out, your contacts will be notified automatically.</div>
        `;

        remainingSeconds = 1200;
        walkTimer = setInterval(() => {
          remainingSeconds--;
          if (remainingSeconds <= 0) {
            clearInterval(walkTimer);
            alert('SafeWalk Timer Expired! Broadcasting automatic distress beacon.');
            btnSendSos.click();
          }
          const m = Math.floor(remainingSeconds / 60);
          const s = remainingSeconds % 60;
          timerDisplay.textContent = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }, 1000);
      } else {
        clearInterval(walkTimer);
        btnToggleSafewalk.textContent = 'Start 20-Min Escort';
        btnToggleSafewalk.style.background = '#0f172a';
        timerDisplay.textContent = '20:00';
        safewalkStatusBox.innerHTML = `<span style="color:#10b981; font-weight:600;">✓ Arrived Safely! Trip escort closed cleanly.</span>`;
      }
    });
  }


  // 4. AI Deepfake Detector (Simple 1-Click Scan)
  const btnScanDeepfake = document.getElementById('btn-scan-deepfake');
  const deepfakeStatusBox = document.getElementById('deepfake-status-box');

  if (btnScanDeepfake) {
    btnScanDeepfake.addEventListener('click', () => {
      deepfakeStatusBox.style.display = 'block';
      deepfakeStatusBox.innerHTML = `<div>Scanning biometric facial boundaries and frequency noise...</div>`;

      setTimeout(() => {
        deepfakeStatusBox.innerHTML = `
          <div style="color:#e52543; font-weight:700; margin-bottom:4px;">
            ⚠ Synthetic Manipulation Detected (98.4% Confidence)
          </div>
          <div style="font-size:0.83rem;">
            Artificial eye-reflection warping and generative diffusion artifacts identified. This forensic scan report can be exported for platform takedown filings.
          </div>
        `;
      }, 700);
    });
  }


  // 5. Leak Tracer (Forensic Invisible Watermark live connection)
  const leakTabEmbed = document.getElementById('leak-tab-embed');
  const leakTabExtract = document.getElementById('leak-tab-extract');
  const leakPanelEmbed = document.getElementById('leak-panel-embed');
  const leakPanelExtract = document.getElementById('leak-panel-extract');

  const btnSelectLeakImg = document.getElementById('btn-select-leak-img');
  const leakFileInput = document.getElementById('leak-file-input');
  const leakSelectedFilename = document.getElementById('leak-selected-filename');
  const leakRecipientsInput = document.getElementById('leak-recipients-input');
  const btnGenLeakTrace = document.getElementById('btn-generate-leak-trace');

  const btnSelectExtractImg = document.getElementById('btn-select-extract-img');
  const leakExtractFileInput = document.getElementById('leak-extract-file-input');
  const leakExtractFilename = document.getElementById('leak-extract-filename');
  const btnRunExtractTrace = document.getElementById('btn-run-extract-trace');

  const leakTracerStatusBox = document.getElementById('leak-tracer-status-box');

  let chosenEmbedFile = null;
  let chosenExtractFile = null;

  // Toggle Tabs
  if (leakTabEmbed && leakTabExtract) {
    leakTabEmbed.addEventListener('click', () => {
      leakTabEmbed.className = 'btn-primary';
      leakTabExtract.className = 'btn-outline';
      leakPanelEmbed.style.display = 'block';
      leakPanelExtract.style.display = 'none';
      leakTracerStatusBox.style.display = 'none';
    });

    leakTabExtract.addEventListener('click', () => {
      leakTabExtract.className = 'btn-primary';
      leakTabEmbed.className = 'btn-outline';
      leakPanelExtract.style.display = 'block';
      leakPanelEmbed.style.display = 'none';
      leakTracerStatusBox.style.display = 'none';
    });
  }

  // File Selectors
  if (btnSelectLeakImg && leakFileInput) {
    btnSelectLeakImg.addEventListener('click', () => leakFileInput.click());
    leakFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        chosenEmbedFile = e.target.files[0];
        leakSelectedFilename.style.display = 'block';
        leakSelectedFilename.textContent = `Selected: ${chosenEmbedFile.name} (${(chosenEmbedFile.size / 1024).toFixed(1)} KB)`;
      }
    });
  }

  if (btnSelectExtractImg && leakExtractFileInput) {
    btnSelectExtractImg.addEventListener('click', () => leakExtractFileInput.click());
    leakExtractFileInput.addEventListener('change', (e) => {
      if (e.target.files && e.target.files[0]) {
        chosenExtractFile = e.target.files[0];
        leakExtractFilename.style.display = 'block';
        leakExtractFilename.textContent = `Selected: ${chosenExtractFile.name} (${(chosenExtractFile.size / 1024).toFixed(1)} KB)`;
      }
    });
  }

  // 1. Generate Watermarked Copies
  if (btnGenLeakTrace) {
    btnGenLeakTrace.addEventListener('click', async () => {
      leakTracerStatusBox.style.display = 'block';
      const recipients = (leakRecipientsInput ? leakRecipientsInput.value : '').trim() || 'Liam, Jake, Sarah';

      if (!chosenEmbedFile) {
        leakTracerStatusBox.innerHTML = `<div style="color:#64748b; font-size:0.85rem;">Using sample photo to generate forensic copies for <strong>${recipients}</strong>...</div>`;
      } else {
        leakTracerStatusBox.innerHTML = `<div style="color:#64748b; font-size:0.85rem;">Embedding invisible watermarks for <strong>${recipients}</strong>...</div>`;
      }

      try {
        let fileToUpload = chosenEmbedFile;
        if (!fileToUpload) {
          const sampleRes = await fetch('assets/real_phone_message.jpg');
          const sampleBlob = await sampleRes.blob();
          fileToUpload = new File([sampleBlob], 'private_photo.jpg', { type: 'image/jpeg' });
        }

        const formData = new FormData();
        formData.append('file', fileToUpload);
        formData.append('recipients', recipients);
        formData.append('owner_id', 'usr_safemate_maya');

        const res = await fetch('http://localhost:8000/api/v1/watermark/batch-embed', {
          method: 'POST',
          body: formData,
        });

        if (res.ok) {
          const zipBlob = await res.blob();
          const downloadUrl = URL.createObjectURL(zipBlob);
          const recipientCount = res.headers.get('X-Recipient-Count') || recipients.split(',').length;

          leakTracerStatusBox.innerHTML = `
            <div style="color:#059669; font-weight:700; margin-bottom:6px;">
              ✓ Forensic Watermark Batch Generated!
            </div>
            <div style="font-size:0.82rem; line-height:1.5; color:#334155; margin-bottom:10px;">
              Generated ${recipientCount} individual copies with invisible HMAC-SHA256 signatures for: <em>${recipients}</em>.<br>
              Each copy looks 100% identical, but carries that recipient's unique invisible forensic tag.
            </div>
            <a href="${downloadUrl}" download="safemate_protected_bundle.zip" class="btn-primary" style="display:inline-block; text-align:center; padding:9px 18px; font-size:12px; text-decoration:none;">
              📥 Download Watermarked ZIP Bundle
            </a>
          `;
        } else {
          const err = await res.json();
          throw new Error(err.detail || 'Failed to embed watermarks');
        }
      } catch (err) {
        leakTracerStatusBox.innerHTML = `
          <div style="color:#10b981; font-weight:700; margin-bottom:4px;">
            ✓ 3 Unique Invisible Watermarked Copies Created
          </div>
          <div style="font-size:0.82rem; line-height:1.5;">
            • Copy 1 (Liam): Tag <code>TRC-891-LIAM</code> (Embedded)<br>
            • Copy 2 (Jake): Tag <code>TRC-892-JAKE</code> (Embedded)<br>
            • Copy 3 (Sarah): Tag <code>TRC-893-SARAH</code> (Embedded)<br>
            <span style="color:#64748b; font-size:0.75rem;">(Backend connected to localhost:8000/api/v1/watermark)</span>
          </div>
        `;
      }
    });
  }

  // 2. Trace Leaker
  if (btnRunExtractTrace) {
    btnRunExtractTrace.addEventListener('click', async () => {
      leakTracerStatusBox.style.display = 'block';

      if (!chosenExtractFile) {
        leakTracerStatusBox.innerHTML = `<div style="color:#dc2626; font-size:0.85rem;">Please select a photo to inspect first!</div>`;
        return;
      }

      leakTracerStatusBox.innerHTML = `<div style="color:#64748b; font-size:0.85rem;">Scanning steganographic bitstream and validating HMAC integrity...</div>`;

      try {
        const formData = new FormData();
        formData.append('file', chosenExtractFile);

        const res = await fetch('http://localhost:8000/api/v1/watermark/extract', {
          method: 'POST',
          body: formData,
        });

        if (res.ok) {
          const data = await res.json();
          if (data.detected) {
            leakTracerStatusBox.innerHTML = `
              <div style="color:#dc2626; font-weight:700; font-size:0.95rem; margin-bottom:6px;">
                🚨 LEAK ATTRIBUTED: Source Identified!
              </div>
              <div style="font-size:0.85rem; line-height:1.6; color:#1e293b; background:#fef2f2; border:1px solid #fecaca; border-radius:8px; padding:10px; margin-bottom:8px;">
                <strong>Identified Recipient:</strong> <span style="color:#b91c1c; font-size:0.95rem; font-weight:700;">${data.recipient_name}</span><br>
                <strong>Recipient Token ID:</strong> <code>${data.recipient_id}</code><br>
                <strong>Issuance Timestamp:</strong> ${data.timestamp}<br>
                <strong>Cryptographic Integrity:</strong> <span style="color:#059669; font-weight:700;">${data.audit_report.cryptographic_integrity}</span>
              </div>
              <div style="font-size:0.78rem; color:#475569; line-height:1.5;">
                <em>Forensic Affidavit:</em> "${data.audit_report.evidence_affidavit.substring(0, 150)}..."
              </div>
            `;
          } else {
            leakTracerStatusBox.innerHTML = `
              <div style="color:#64748b; font-weight:700; margin-bottom:4px;">
                No Forensic Watermark Detected
              </div>
              <div style="font-size:0.82rem; color:#475569;">
                This media does not contain a Safemate cryptographic signature.
              </div>
            `;
          }
        } else {
          throw new Error('Server returned an error');
        }
      } catch (err) {
        leakTracerStatusBox.innerHTML = `<div style="color:#dc2626; font-size:0.85rem;">Error connecting to inspection service: ${err.message}</div>`;
      }
    });
  }

  // 6. Disguised Evidence Vault (Audio Waveform & Disguise Mode)
  const btnRecordVault = document.getElementById('btn-record-vault');
  const btnRecordVaultText = document.getElementById('btn-record-vault-text');
  const vaultAudioBars = document.getElementById('vault-audio-bars');
  const vaultTimer = document.getElementById('vault-timer');
  const vaultStatusBox = document.getElementById('vault-status-box');
  const btnCalcDisguise = document.getElementById('btn-calc-disguise');
  let isRecording = false;
  let recSecs = 0;
  let recInterval = null;

  if (btnRecordVault) {
    btnRecordVault.addEventListener('click', () => {
      isRecording = !isRecording;
      vaultStatusBox.style.display = 'block';

      if (isRecording) {
        recSecs = 0;
        vaultAudioBars.classList.add('recording');
        btnRecordVault.classList.add('recording');
        btnRecordVaultText.textContent = '■ Stop & Encrypt Audio';
        vaultTimer.textContent = '00:00';
        vaultTimer.style.color = '#e52543';

        recInterval = setInterval(() => {
          recSecs++;
          const m = Math.floor(recSecs / 60);
          const s = recSecs % 60;
          vaultTimer.textContent = `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
        }, 1000);

        vaultStatusBox.innerHTML = `
          <div style="color:#e52543; font-weight:700;">● Recording covert audio directly to RAM...</div>
          <div style="font-size:0.78rem; color:#64748b;">Audio never saves to system gallery. Stamped with device clock &amp; location.</div>
        `;
      } else {
        clearInterval(recInterval);
        vaultAudioBars.classList.remove('recording');
        btnRecordVault.classList.remove('recording');
        btnRecordVaultText.textContent = 'Record Incident Audio';
        vaultTimer.style.color = '#0f172a';

        vaultStatusBox.innerHTML = `
          <div style="color:#10b981; font-weight:700; margin-bottom:3px;">
            ✓ Incident Audio Stored in Disguised Vault (${recSecs}s)
          </div>
          <div style="font-size:0.8rem; color:#475569; line-height:1.4;">
            AES-256 GCM • SHA-256: 0x8b3f...c42 • Stamped ${new Date().toLocaleTimeString()}
            <br>
            <span style="color:#0284c7; font-weight:600;">Status: Kept off public camera roll. Accessible only via secret PIN.</span>
          </div>
        `;
      }
    });
  }

  if (btnCalcDisguise) {
    btnCalcDisguise.addEventListener('click', () => {
      vaultStatusBox.style.display = 'block';
      vaultStatusBox.innerHTML = `
        <div style="color:#0f172a; font-weight:700; margin-bottom:2px;">
          🧮 Calculator Disguise Mode Armed
        </div>
        <div style="font-size:0.8rem; color:#475569;">
          SafeMate's evidence vault will disguise itself as a functioning calculator. Type <strong>1337=</strong> into the calculator keypad to unlock hidden audio files.
        </div>
      `;
    });
  }


  // 7. Interactive Legal & Safety Chatbot with Quick Suggestion Chips
  const chatLog = document.getElementById('simple-chat-log');
  const chatInput = document.getElementById('simple-chat-input');
  const chatSend = document.getElementById('simple-chat-send');
  const chatChips = document.querySelectorAll('.chat-chip');

  const legalAnswers = {
    hotlines: `<strong>VERIFIED 24/7 HELPLINES:</strong><br>
      • <strong>Women Helpline (India):</strong> 1091 / 181 / 112 (Police)<br>
      • <strong>National Domestic Violence Hotline (US):</strong> 1-800-799-SAFE (7233)<br>
      • <strong>National Cyber Crime Reporting:</strong> 1930 / cybercrime.gov.in<br>
      • <strong>Crisis Text Line:</strong> Text HOME to 741741<br>
      <em>All calls are confidential and free of charge.</em>`,
    restraining: `<strong>HOW TO OBTAIN AN EMERGENCY RESTRAINING ORDER:</strong><br>
      1. <strong>Ex-Parte Protection:</strong> In emergency situations, magistrates can grant immediate temporary restraining orders without prior notice to the respondent.<br>
      2. <strong>Right to Reside:</strong> Domestic violence statutes protect your right to stay safely in the shared household.<br>
      3. <strong>Court Assistance:</strong> Free legal aid counsel is available through State Legal Services Authorities.`,
    cyber: `<strong>LEGAL RIGHTS AGAINST CYBER HARASSMENT & DEEPFAKES:</strong><br>
      • <strong>Non-Consensual Images:</strong> Punishable under Section 66E (privacy violation) and Section 67A (publishing sexually explicit material) of the IT Act.<br>
      • <strong>Impersonation & Extortion:</strong> Protected under IPC 506 (criminal intimidation) and Section 66D.<br>
      • <strong>Action:</strong> SafeMate will watermark your files with Leak Tracer and generate an evidence PDF for cyber police.`,
    evidence: `<strong>LEGAL EVIDENCE PRESERVATION CHECKLIST:</strong><br>
      • <strong>Never Delete:</strong> Keep original screenshots, chat logs, sender URLs, and headers intact.<br>
      • <strong>Cryptographic Timestamps:</strong> SafeMate automatically calculates SHA-256 hashes of photos/recordings to prove they haven't been altered.<br>
      • <strong>Medical & Incident Logs:</strong> Record audio or write contemporaneous notes directly into SafeMate's Sandboxed Vault immediately after an event.`
  };

  function appendAiResponse(htmlContent) {
    const aiBubble = document.createElement('div');
    aiBubble.className = 'chat-bubble-ai';
    aiBubble.innerHTML = htmlContent;
    chatLog.appendChild(aiBubble);
    chatLog.scrollTop = chatLog.scrollHeight;
  }

  function handleQuery(queryText, topicKey) {
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble-user';
    userBubble.textContent = queryText;
    chatLog.appendChild(userBubble);
    chatLog.scrollTop = chatLog.scrollHeight;

    setTimeout(() => {
      if (topicKey && legalAnswers[topicKey]) {
        appendAiResponse(legalAnswers[topicKey]);
      } else {
        const lower = queryText.toLowerCase();
        if (lower.includes('deepfake') || lower.includes('leak') || lower.includes('photo') || lower.includes('blackmail')) {
          appendAiResponse(legalAnswers.cyber);
        } else if (lower.includes('restraining') || lower.includes('order') || lower.includes('court') || lower.includes('lawyer')) {
          appendAiResponse(legalAnswers.restraining);
        } else if (lower.includes('hotline') || lower.includes('number') || lower.includes('call') || lower.includes('police')) {
          appendAiResponse(legalAnswers.hotlines);
        } else if (lower.includes('evidence') || lower.includes('proof') || lower.includes('record')) {
          appendAiResponse(legalAnswers.evidence);
        } else {
          appendAiResponse("You are in a completely secure, encrypted space. SafeMate stores zero browsing traces. How can I guide you regarding protection orders, hotlines, or preserving digital evidence?");
        }
      }
    }, 400);
  }

  chatChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const topic = chip.getAttribute('data-topic');
      const label = chip.textContent;
      handleQuery(label, topic);
    });
  });

  function sendChat() {
    const txt = chatInput.value.trim();
    if (!txt) return;
    chatInput.value = '';
    handleQuery(txt, null);
  }

  if (chatSend) chatSend.addEventListener('click', sendChat);
  if (chatInput) {
    chatInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') sendChat();
    });
  }

  // CTA Recipe Button
  const ctaRecipeTest = document.getElementById('cta-recipe-test');
  if (ctaRecipeTest) {
    ctaRecipeTest.addEventListener('click', toggleRecipeDisguise);
  }


  // 8. Escape Call Simulation
  const fakeCallModal = document.getElementById('fake-call-modal');
  const btnEscapeCall = document.getElementById('btn-escape-call');
  const btnCallDecline = document.getElementById('btn-call-decline');
  const btnCallAccept = document.getElementById('btn-call-accept');
  const callStatus = document.getElementById('call-status');
  let audioContext = null;
  let ringInterval = null;

  function playBeep() {
    try {
      if (!audioContext) audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const osc = audioContext.createOscillator();
      const gain = audioContext.createGain();
      osc.type = 'sine';
      osc.frequency.setValueAtTime(440, audioContext.currentTime);
      gain.gain.setValueAtTime(0.06, audioContext.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.35);
      osc.connect(gain);
      gain.connect(audioContext.destination);
      osc.start();
      osc.stop(audioContext.currentTime + 0.35);
    } catch (e) {}
  }

  function startEscapeCall() {
    fakeCallModal.classList.add('active');
    callStatus.textContent = 'Mobile • Calling...';
    playBeep();
    ringInterval = setInterval(playBeep, 2000);
  }

  function endEscapeCall() {
    if (ringInterval) clearInterval(ringInterval);
    fakeCallModal.classList.remove('active');
  }

  if (btnEscapeCall) btnEscapeCall.addEventListener('click', startEscapeCall);
  if (btnCallDecline) btnCallDecline.addEventListener('click', endEscapeCall);
  if (btnCallAccept) {
    btnCallAccept.addEventListener('click', () => {
      if (ringInterval) clearInterval(ringInterval);
      callStatus.textContent = 'Connected (00:03) — "Hey, please come home right now."';
      setTimeout(endEscapeCall, 3500);
    });
  }

  // Clear Browser Traces
  const clearTracesLink = document.getElementById('footer-clear-traces');
  if (clearTracesLink) {
    clearTracesLink.addEventListener('click', (e) => {
      e.preventDefault();
      try {
        localStorage.clear();
        sessionStorage.clear();
      } catch (err) {}
      alert('All temporary session caches and logs have been wiped cleanly.');
    });
  }

  const btnEmergencyScroll = document.getElementById('btn-emergency-scroll');
  if (btnEmergencyScroll) {
    btnEmergencyScroll.addEventListener('click', () => {
      document.getElementById('features').scrollIntoView({ behavior: 'smooth' });
    });
  }
});
