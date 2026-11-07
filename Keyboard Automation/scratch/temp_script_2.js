

    (function() {

      const API_BASE = (window.location.protocol === 'http:' || window.location.protocol === 'https:')

        ? window.location.origin

        : 'http://127.0.0.1:8501';



      const rawData = JSON.parse(document.getElementById('history-data').textContent || '{}');

      const rawCfg = JSON.parse(document.getElementById('runtime-config-data').textContent || '{}');

      const chats = rawData.chats || {};



      let isAutomationActive = false;

      let logsOpen = false;

      let logLines = 0;

      let audioMuted = localStorage.getItem('asc_audio_muted') === 'true';

      let autoScrollLogs = true;

      let currentActiveTab = localStorage.getItem('asc_dashboard_tab') || 'overview';



      // Elements

      const summaryTbody = document.getElementById('summary-tbody');

      const detailsContainer = document.getElementById('details-container');

      const searchChats = document.getElementById('search-chats');

      const searchQuestions = document.getElementById('search-questions');

      const searchConfig = document.getElementById('search-config');

      const tickerStatusMsg = document.getElementById('ticker-status-msg');



      // Filter Toolbar Elements

      const filterDateFrom = document.getElementById('filter-date-from');

      const filterDateTo = document.getElementById('filter-date-to');

      const filterChat = document.getElementById('filter-chat');

      const filterComplexity = document.getElementById('filter-complexity');

      const filterSpeed = document.getElementById('filter-speed');

      const filterResetBtn = document.getElementById('filter-reset-btn');

      const filterCountEl = document.getElementById('filter-count');

      const filterTotalEl = document.getElementById('filter-total');

      const activeChipsContainer = document.getElementById('active-chips-container');

      const presetBtns = document.querySelectorAll('.preset-btn');



      function escapeHtml(str) {

        if (!str) return '';

        return String(str)

          .replace(/&/g, '&amp;')

          .replace(/</g, '&lt;')

          .replace(/>/g, '&gt;')

          .replace(/"/g, '&quot;')

          .replace(/'/g, '&#039;');

      }



      // Toast notification helper

      function showToast(msg) {

        const t = document.getElementById('toast-notify');

        if (!t) return;

        t.textContent = msg;

        t.style.display = 'block';

        setTimeout(() => { t.style.display = 'none'; }, 2800);

      }



      // Web Audio API Synthesizer (0 external files)

      function playChime(type) {

        if (audioMuted) return;

        try {

          const ctx = new (window.AudioContext || window.webkitAudioContext)();

          const osc = ctx.createOscillator();

          const gain = ctx.createGain();

          osc.connect(gain);

          gain.connect(ctx.destination);

          const now = ctx.currentTime;



          if (type === 'start') {

            osc.frequency.setValueAtTime(440, now);

            osc.frequency.exponentialRampToValueAtTime(880, now + 0.18);

            gain.gain.setValueAtTime(0.08, now);

            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.25);

            osc.start(now);

            osc.stop(now + 0.25);

          } else if (type === 'stop') {

            osc.frequency.setValueAtTime(660, now);

            osc.frequency.exponentialRampToValueAtTime(330, now + 0.22);

            gain.gain.setValueAtTime(0.08, now);

            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.28);

            osc.start(now);

            osc.stop(now + 0.28);

          } else if (type === 'copy') {

            osc.frequency.setValueAtTime(987, now);

            gain.gain.setValueAtTime(0.06, now);

            gain.gain.exponentialRampToValueAtTime(0.001, now + 0.12);

            osc.start(now);

            osc.stop(now + 0.12);

          }

        } catch(e) {}

      }



      // Digital Clock

      function updateClock() {

        const el = document.getElementById('live-clock');

        if (el) {

          const d = new Date();

          el.textContent = d.toTimeString().split(' ')[0];

        }

      }

      setInterval(updateClock, 1000);

      updateClock();



      // Number Count-Up Animation for KPIs

      function runCounters() {

        document.querySelectorAll('.counter-value').forEach(el => {

          const target = parseFloat(el.getAttribute('data-target') || '0');

          if (isNaN(target) || target <= 0) return;

          const duration = 650;

          const start = performance.now();

          function step(now) {

            const progress = Math.min((now - start) / duration, 1);

            const current = Math.floor(progress * target);

            el.textContent = current;

            if (progress < 1) requestAnimationFrame(step);

            else el.textContent = target;

          }

          requestAnimationFrame(step);

        });

      }

      runCounters();



      // Main Horizontal Tabs & Contextual Filter Toolbar visibility

      const tabs = document.querySelectorAll('.tab-btn');

      const panels = document.querySelectorAll('.tab-panel');

      const contextualFilters = document.getElementById('contextual-filter-toolbar');



      function switchTab(targetTab) {

        currentActiveTab = targetTab;

        localStorage.setItem('asc_dashboard_tab', targetTab);



        tabs.forEach(t => {

          const active = t.getAttribute('data-tab') === targetTab;

          t.classList.toggle('active', active);

          t.setAttribute('aria-selected', active);

        });

        panels.forEach(p => {

          const active = p.id === 'tab-' + targetTab;

          p.classList.toggle('active', active);

        });



        // Show filters on overview, chats, and questions; hide on modes and config

        if (contextualFilters) {

          contextualFilters.style.display = (targetTab === 'overview' || targetTab === 'chats' || targetTab === 'questions') ? 'block' : 'none';

        }

      }



      tabs.forEach(btn => {

        btn.addEventListener('click', () => switchTab(btn.getAttribute('data-tab')));

      });

      switchTab(currentActiveTab);



      // Config Sub-Tabs (System Runtime vs Dashboard Preferences)

      const subtabBtns = document.querySelectorAll('.config-subnav-btn');

      const subpanels = document.querySelectorAll('.config-subpanel');

      subtabBtns.forEach(btn => {

        btn.addEventListener('click', () => {

          subtabBtns.forEach(b => b.classList.remove('active'));

          subpanels.forEach(p => p.classList.remove('active'));

          btn.classList.add('active');

          const subId = btn.getAttribute('data-subtab');

          const targetPanel = document.getElementById('subpanel-' + subId);

          if (targetPanel) targetPanel.classList.add('active');

        });

      });



      // Floating SVG Chart Tooltips

      const tooltip = document.getElementById('chart-floating-tooltip');

      document.querySelectorAll('svg rect, svg circle, svg path').forEach(el => {

        const title = el.querySelector('title');

        if (title && title.textContent) {

          const text = title.textContent;

          el.addEventListener('mouseenter', (e) => {

            if (!tooltip) return;

            tooltip.innerHTML = text.replace(/\n/g, '<br>');

            tooltip.style.display = 'block';

            tooltip.style.left = (e.clientX + 14) + 'px';

            tooltip.style.top = (e.clientY + 14) + 'px';

          });

          el.addEventListener('mousemove', (e) => {

            if (!tooltip) return;

            tooltip.style.left = (e.clientX + 14) + 'px';

            tooltip.style.top = (e.clientY + 14) + 'px';

          });

          el.addEventListener('mouseleave', () => {

            if (tooltip) tooltip.style.display = 'none';

          });

        }

      });



      // Multi-Dimensional Filtering Logic

      function formatDate(d) {

        const year = d.getFullYear();

        const month = String(d.getMonth() + 1).padStart(2, '0');

        const day = String(d.getDate()).padStart(2, '0');

        return `${year}-${month}-${day}`;

      }



      function runMatchesFilters(cid, chat, run) {

        const fromVal = filterDateFrom ? filterDateFrom.value : '';

        const toVal = filterDateTo ? filterDateTo.value : '';

        const selChat = filterChat ? filterChat.value : 'all';

        const selComplexity = filterComplexity ? filterComplexity.value : 'all';

        const selSpeed = filterSpeed ? filterSpeed.value : 'all';



        if (selChat !== 'all' && cid !== selChat) return false;



        if (run && run.timestamp) {

          const runDateStr = run.timestamp.split('T')[0];

          if (fromVal && runDateStr < fromVal) return false;

          if (toVal && runDateStr > toVal) return false;

        }



        if (run) {

          const qCount = run.questions_count !== undefined ? run.questions_count : (run.questions ? run.questions.length : 0);

          if (selComplexity === 'single' && qCount !== 1) return false;

          if (selComplexity === 'multi' && qCount < 2) return false;

        }



        if (run) {

          const dur = typeof run.duration_seconds === 'number' ? run.duration_seconds : 0.0;

          if (selSpeed === 'fast' && dur >= 3.0) return false;

          if (selSpeed === 'moderate' && (dur < 3.0 || dur > 8.0)) return false;

          if (selSpeed === 'heavy' && dur <= 8.0) return false;

        }



        return true;

      }



      function updateActiveChips() {

        if (!activeChipsContainer) return;

        let chipsHtml = '<span class="active-chips-label">Active:</span>';



        const activePresetBtn = document.querySelector('.preset-btn.active');

        chipsHtml += `<span class="filter-chip">⚡ ${activePresetBtn ? activePresetBtn.textContent : 'All Time'}</span>`;



        if (filterDateFrom && filterDateFrom.value && filterDateTo && filterDateTo.value) {

          chipsHtml += `<span class="filter-chip">📅 ${filterDateFrom.value} to ${filterDateTo.value} <span class="filter-chip-remove" onclick="clearDateFilter()">✕</span></span>`;

        }



        if (filterChat && filterChat.value !== 'all') {

          const selOpt = filterChat.options[filterChat.selectedIndex];

          chipsHtml += `<span class="filter-chip">📂 ${selOpt ? selOpt.textContent.slice(0, 25) : 'Chat'} <span class="filter-chip-remove" onclick="clearChatFilter()">✕</span></span>`;

        }



        if (filterComplexity && filterComplexity.value !== 'all') {

          chipsHtml += `<span class="filter-chip">🎯 ${filterComplexity.value === 'single' ? 'Single Q' : 'Multi Q'} <span class="filter-chip-remove" onclick="clearComplexityFilter()">✕</span></span>`;

        }



        if (filterSpeed && filterSpeed.value !== 'all') {

          chipsHtml += `<span class="filter-chip">⚡ ${filterSpeed.value} <span class="filter-chip-remove" onclick="clearSpeedFilter()">✕</span></span>`;

        }



        activeChipsContainer.innerHTML = chipsHtml;

      }



      window.clearDateFilter = function() {

        if (filterDateFrom) filterDateFrom.value = '';

        if (filterDateTo) filterDateTo.value = '';

        applyFilters();

      };

      window.clearChatFilter = function() {

        if (filterChat) filterChat.value = 'all';

        applyFilters();

      };

      window.clearComplexityFilter = function() {

        if (filterComplexity) filterComplexity.value = 'all';

        applyFilters();

      };

      window.clearSpeedFilter = function() {

        if (filterSpeed) filterSpeed.value = 'all';

        applyFilters();

      };



      // Render Chats: Dual Engine (Cards Explorer & Data Table)

      const chatsCardGrid = document.getElementById('chats-card-grid');



      function renderChats() {

        const searchVal = (searchChats ? searchChats.value : '').toLowerCase().trim();

        const chatEntries = Object.entries(chats);

        if (summaryTbody) summaryTbody.innerHTML = '';

        if (chatsCardGrid) chatsCardGrid.innerHTML = '';

        let matchCount = 0;



        for (const [cid, chat] of chatEntries) {

          const topic = chat.topic_summary || 'Untitled Conversation';

          const prompt = chat.last_user_prompt || '';

          const runs = chat.runs || [];



          const textMatch = !searchVal ||

            cid.toLowerCase().includes(searchVal) ||

            topic.toLowerCase().includes(searchVal) ||

            prompt.toLowerCase().includes(searchVal);



          if (!textMatch) continue;



          const matchingRuns = runs.filter(run => runMatchesFilters(cid, chat, run));

          const chatFilterMatch = runs.length > 0 ? (matchingRuns.length > 0) : (filterChat ? filterChat.value === 'all' || filterChat.value === cid : true);



          if (chatFilterMatch) {

            matchCount++;

            const displayRunCount = runs.length > 0 ? matchingRuns.length : (chat.run_count || 0);

            const displayQsCount = runs.length > 0 ? matchingRuns.reduce((acc, r) => acc + (r.questions_count || (r.questions ? r.questions.length : 0)), 0) : (chat.total_questions || 0);

            const lastTimeStr = chat.last_run_timestamp ? new Date(chat.last_run_timestamp).toLocaleString() : 'N/A';



            // 1. Classic Table Row (Full feature parity & test assertions)

            if (summaryTbody) {

              const tr = document.createElement('tr');

              tr.innerHTML = `

                <td><span class="chat-id-tag">${escapeHtml(cid)}</span></td>

                <td><strong>${escapeHtml(topic)}</strong></td>

                <td><span class="badge-count">${displayRunCount}</span></td>

                <td><span class="badge-count">${displayQsCount}</span></td>

                <td style="font-family: var(--font-mono); font-size: 0.8rem; color: var(--text-secondary);">${lastTimeStr}</td>

              `;

              summaryTbody.appendChild(tr);

            }



            // 2. High-Tech Visual Conversation Card (Modern Default Experience)

            if (chatsCardGrid) {

              const card = document.createElement('div');

              card.className = 'modern-chat-card';

              card.innerHTML = `

                <div class="chat-card-top-row">

                  <div class="chat-avatar-badge">

                    <div class="chat-avatar-icon">🤖</div>

                    <span class="chat-id-tag" title="Click to copy ID" onclick="navigator.clipboard.writeText('${escapeHtml(cid)}'); showToast('Copied ID: ${escapeHtml(cid)}'); playChime('copy');" style="cursor: pointer;">${escapeHtml(cid)} 📋</span>

                  </div>

                  <span class="chat-metric-pill" style="color: var(--accent-emerald); border-color: rgba(16, 185, 129, 0.35); background: rgba(16, 185, 129, 0.08);">🟢 Automated</span>

                </div>



                <div>

                  <h3 class="chat-topic-title">${escapeHtml(topic)}</h3>

                  <div style="font-size: 0.78rem; color: var(--text-muted); margin-top: 6px; font-family: var(--font-mono);">

                    🕒 Last Active: ${lastTimeStr}

                  </div>

                </div>



                <div class="chat-metrics-bar">

                  <span class="chat-metric-pill">⚡ <strong>${displayRunCount}</strong> Runs</span>

                  <span class="chat-metric-pill">❓ <strong>${displayQsCount}</strong> Questions</span>

                  ${prompt ? `<span class="chat-metric-pill" style="max-width: 160px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(prompt)}">💬 ${escapeHtml(prompt)}</span>` : ''}

                </div>



                <div class="chat-card-actions">

                  <button type="button" class="btn-chat-action" onclick="jumpToChatQuestions('${escapeHtml(cid)}')">

                    <span>❓ View Questions (${displayQsCount})</span>

                  </button>

                  <button type="button" class="btn-chat-action" onclick="navigator.clipboard.writeText('${escapeHtml(cid)}'); showToast('Copied Conversation ID'); playChime('copy');">

                    <span>📋 Copy ID</span>

                  </button>

                </div>

              `;

              chatsCardGrid.appendChild(card);

            }

          }

        }



        if (matchCount === 0) {

          if (summaryTbody) {

            summaryTbody.innerHTML = `<tr><td colspan="5" style="text-align:center; padding: 24px; color: var(--text-muted);">No matching chat records found.</td></tr>`;

          }

          if (chatsCardGrid) {

            chatsCardGrid.innerHTML = `

              <div style="grid-column: 1 / -1; text-align: center; padding: 48px 20px; background: var(--bg-surface); border: 1px dashed var(--border-subtle); border-radius: var(--radius-lg);">

                <div style="font-size: 2.2rem; margin-bottom: 10px;">🔍</div>

                <div style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">No Matching Conversations</div>

                <div style="font-size: 0.84rem; color: var(--text-secondary);">Try clearing your search query or adjusting the date/speed filters above.</div>

              </div>

            `;

          }

        }

      }



      window.setChatsView = function(view) {

        localStorage.setItem('asc_chats_view', view);

        const cardsView = document.getElementById('chats-cards-view');

        const tableView = document.getElementById('chats-table-view');

        const btnCards = document.getElementById('btn-view-cards');

        const btnTable = document.getElementById('btn-view-table');



        if (view === 'table') {

          if (cardsView) cardsView.style.display = 'none';

          if (tableView) tableView.style.display = 'block';

          if (btnCards) { btnCards.classList.remove('active'); btnCards.style.background = 'transparent'; btnCards.style.color = 'var(--text-secondary)'; }

          if (btnTable) { btnTable.classList.add('active'); btnTable.style.background = 'var(--accent-indigo)'; btnTable.style.color = '#fff'; }

        } else {

          if (cardsView) cardsView.style.display = 'block';

          if (tableView) tableView.style.display = 'none';

          if (btnCards) { btnCards.classList.add('active'); btnCards.style.background = 'var(--accent-indigo)'; btnCards.style.color = '#fff'; }

          if (btnTable) { btnTable.classList.remove('active'); btnTable.style.background = 'transparent'; btnTable.style.color = 'var(--text-secondary)'; }

        }

      };



      window.jumpToChatQuestions = function(cid) {

        switchTab('questions');

        if (searchQuestions) {

          searchQuestions.value = cid;

          applyFilters();

        }

        showToast('Filtered Questions for conversation: ' + cid);

        playChime('copy');

      };



      // Render Questions Cards (Developer Decision Studio with Modern Radio Option Cards)

      let currentQFilter = 'all';



      window.setQFilter = function(filterType, btn) {

        currentQFilter = filterType;

        document.querySelectorAll('.q-filter-chip').forEach(b => b.classList.remove('active'));

        if (btn) btn.classList.add('active');

        renderQuestions();

      };



      function renderQuestions() {

        if (!detailsContainer) return;

        const searchVal = (searchQuestions ? searchQuestions.value : '').toLowerCase().trim();

        const chatEntries = Object.entries(chats);

        detailsContainer.innerHTML = '';

        let cardsCount = 0;



        for (const [cid, chat] of chatEntries) {

          const topic = chat.topic_summary || 'Untitled Conversation';

          const runs = chat.runs || [];



          const matchingRuns = runs.filter(run => {

            if (!runMatchesFilters(cid, chat, run)) return false;

            let questions = run.questions || [];

            if (currentQFilter === 'recommended') {

              questions = questions.filter(q => (q.selected_option_text || '').includes('(Recommended)'));

              if (questions.length === 0) return false;

            } else if (currentQFilter === 'multi') {

              questions = questions.filter(q => (q.options || []).length > 2);

              if (questions.length === 0) return false;

            }

            if (!searchVal) return true;

            if (cid.toLowerCase().includes(searchVal) || topic.toLowerCase().includes(searchVal)) return true;

            return questions.some(q =>

              (q.question || '').toLowerCase().includes(searchVal) ||

              (q.options || []).some(opt => opt.toLowerCase().includes(searchVal))

            );

          });



          if (matchingRuns.length > 0) {

            cardsCount++;

            const card = document.createElement('div');

            card.className = 'chat-card';



            let runsHtml = '';

            matchingRuns.forEach((run, rIdx) => {

              const runDate = run.timestamp ? new Date(run.timestamp).toLocaleString() : 'N/A';

              const dur = run.duration_seconds ? run.duration_seconds.toFixed(1) + 's' : 'N/A';

              let questions = run.questions || [];

              if (currentQFilter === 'recommended') {

                questions = questions.filter(q => (q.selected_option_text || '').includes('(Recommended)'));

              } else if (currentQFilter === 'multi') {

                questions = questions.filter(q => (q.options || []).length > 2);

              }



              let qHtml = '';

              questions.forEach((q, qIdx) => {

                let optionsHtml = '';

                const isRecMatched = (q.selected_option_text || '').includes('(Recommended)');



                (q.options || []).forEach((opt, optIdx) => {

                  const isSelected = (optIdx + 1 === q.selected_option_index) ||

                                     (q.selected_option_text && opt.trim() === q.selected_option_text.trim());

                  const isRec = opt.includes('(Recommended)');

                  optionsHtml += `

                    <div class="option-item ${isSelected ? 'selected' : ''}">

                      <div style="display:flex; align-items:center; gap:8px;">

                        <span style="font-size: 0.9rem; color: ${isSelected ? 'var(--accent-emerald)' : 'var(--text-muted)'};">${isSelected ? '◉' : '○'}</span>

                        <span><strong>${optIdx + 1}.</strong> ${escapeHtml(opt)}</span>

                      </div>

                      <div style="display:flex; gap:6px; align-items:center;">

                        ${isSelected ? '<span class="option-badge">✓ Selected Decision</span>' : ''}

                        ${isRec ? '<span style="font-size:0.72rem; font-weight:700; padding:2px 8px; border-radius:9999px; background:rgba(6,182,212,0.18); color:#22d3ee; border:1px solid rgba(6,182,212,0.4);">⭐ Recommended Choice</span>' : ''}

                      </div>

                    </div>

                  `;

                });



                qHtml += `

                  <div class="question-card ${isRecMatched ? 'rec-matched' : ''}" data-question-num="${q.question_index || (qIdx + 1)}">

                    <div class="question-prompt" onclick="toggleQuestionPrompt(this)">

                      <div class="question-prompt-left">

                        <span class="collapse-icon">▸</span>

                        <span class="question-num">Q${q.question_index || (qIdx + 1)}</span>

                        <span>${escapeHtml(q.question)}</span>

                      </div>

                      <div class="question-prompt-right">

                        <button class="btn-copy-qa" onclick="event.stopPropagation(); copyQACard(this)" data-q="${encodeURIComponent(q.question || '')}" data-ans="${encodeURIComponent(q.selected_option_text || '')}">

                          📋 Copy Q&A

                        </button>

                        <span class="badge-count" style="font-size: 0.72rem;">${(q.options || []).length} options</span>

                      </div>

                    </div>

                    <div class="options-list collapsed">

                      ${optionsHtml}

                    </div>

                  </div>

                `;

              });



              runsHtml += `

                <div class="run-block" data-run-id="${escapeHtml(run.run_id || '')}">

                  <div class="run-header" onclick="toggleRunHeader(this)">

                    <div style="display: flex; align-items: center; gap: 8px;">

                      <span class="collapse-icon">▸</span>

                      <span style="font-weight: 700; color: var(--text-primary);">⚡ Run #${rIdx + 1} (${escapeHtml(run.run_id || 'N/A')})</span>

                    </div>

                    <div style="display: flex; align-items: center; gap: 12px;">

                      <span>Duration: ${dur} | ${runDate}</span>

                    </div>

                  </div>

                  <div class="run-body collapsed">

                    ${qHtml}

                  </div>

                </div>

              `;

            });



            const totalFilteredQs = matchingRuns.reduce((acc, r) => acc + (r.questions_count || (r.questions ? r.questions.length : 0)), 0);



            card.innerHTML = `

              <div class="chat-card-header" onclick="toggleChatHeader(this)">

                <div class="chat-card-title">

                  <span class="collapse-icon">▸</span>

                  <span class="chat-id-tag">${escapeHtml(cid)}</span>

                  <span>${escapeHtml(topic)}</span>

                </div>

                <div class="chat-card-meta">

                  <span class="badge-count">${matchingRuns.length} run(s)</span>

                  <span class="badge-count">${totalFilteredQs} question(s)</span>

                </div>

              </div>

              <div class="chat-card-body collapsed">

                ${runsHtml}

              </div>

            `;

            detailsContainer.appendChild(card);

          }

        }



        if (cardsCount === 0) {

          detailsContainer.innerHTML = `

            <div style="text-align:center; padding: 40px; color: var(--text-muted);">

              <div style="font-size: 2rem; margin-bottom: 8px;">📭</div>

              <div style="font-weight: 700; font-size: 1.1rem; color: var(--text-primary); margin-bottom: 4px;">No Questions Found</div>

              <div>No questions match your filter criteria or search query.</div>

            </div>

          `;

        }

      }



      window.toggleChatHeader = function(hdr) {

        const body = hdr.nextElementSibling;

        if (body) {

          const isCollapsed = body.classList.toggle('collapsed');

          const ic = hdr.querySelector('.collapse-icon');

          if (ic) ic.textContent = isCollapsed ? '▸' : '▾';

        }

      };



      window.toggleRunHeader = function(hdr) {

        const body = hdr.nextElementSibling;

        if (body) {

          const isCollapsed = body.classList.toggle('collapsed');

          const ic = hdr.querySelector('.collapse-icon');

          if (ic) ic.textContent = isCollapsed ? '▸' : '▾';

        }

      };



      window.toggleQuestionPrompt = function(hdr) {

        const body = hdr.nextElementSibling;

        if (body) {

          const isCollapsed = body.classList.toggle('collapsed');

          const ic = hdr.querySelector('.collapse-icon');

          if (ic) ic.textContent = isCollapsed ? '▸' : '▾';

        }

      };



      window.copyQACard = function(btn) {

        const q = decodeURIComponent(btn.getAttribute('data-q') || '');

        const ans = decodeURIComponent(btn.getAttribute('data-ans') || '');

        const text = `Question: ${q}\nSelected Answer: ${ans}`;

        navigator.clipboard.writeText(text).then(() => {

          playChime('copy');

          showToast('✅ Question & answer copied to clipboard!');

        });

      };



      // Global Expand All / Collapse All Questions

      const btnExpandAllQ = document.getElementById('btn-expand-all-questions');

      const btnCollapseAllQ = document.getElementById('btn-collapse-all-questions');



      if (btnExpandAllQ) {

        btnExpandAllQ.addEventListener('click', () => {

          if (!detailsContainer) return;

          detailsContainer.querySelectorAll('.chat-card-body, .run-body, .options-list').forEach(el => {

            el.classList.remove('collapsed');

          });

          detailsContainer.querySelectorAll('.collapse-icon').forEach(ic => {

            ic.textContent = '▾';

          });

        });

      }



      if (btnCollapseAllQ) {

        btnCollapseAllQ.addEventListener('click', () => {

          if (!detailsContainer) return;

          detailsContainer.querySelectorAll('.chat-card-body, .run-body, .options-list').forEach(el => {

            el.classList.add('collapsed');

          });

          detailsContainer.querySelectorAll('.collapse-icon').forEach(ic => {

            ic.textContent = '▸';

          });

        });

      }



      function applyFilters() {

        let totalRunsCount = 0;

        let matchingRunsCount = 0;



        for (const [cid, chat] of Object.entries(chats)) {

          const runs = chat.runs || [];

          totalRunsCount += runs.length;

          runs.forEach(run => {

            if (runMatchesFilters(cid, chat, run)) {

              matchingRunsCount++;

            }

          });

        }



        if (filterCountEl) filterCountEl.textContent = matchingRunsCount;

        if (filterTotalEl) filterTotalEl.textContent = totalRunsCount;



        updateActiveChips();

        renderChats();

        renderQuestions();

      }



      // Preset buttons

      presetBtns.forEach(btn => {

        btn.addEventListener('click', () => {

          presetBtns.forEach(b => b.classList.remove('active'));

          btn.classList.add('active');



          const preset = btn.getAttribute('data-preset');

          const now = new Date();



          if (preset === 'all') {

            if (filterDateFrom) filterDateFrom.value = '';

            if (filterDateTo) filterDateTo.value = '';

          } else if (preset === 'today') {

            const todayStr = formatDate(now);

            if (filterDateFrom) filterDateFrom.value = todayStr;

            if (filterDateTo) filterDateTo.value = todayStr;

          } else if (preset === 'yesterday') {

            const y = new Date(now.getTime() - 24 * 3600 * 1000);

            const yStr = formatDate(y);

            if (filterDateFrom) filterDateFrom.value = yStr;

            if (filterDateTo) filterDateTo.value = yStr;

          } else if (preset === '7d') {

            const past7 = new Date(now.getTime() - 7 * 24 * 3600 * 1000);

            if (filterDateFrom) filterDateFrom.value = formatDate(past7);

            if (filterDateTo) filterDateTo.value = formatDate(now);

          } else if (preset === '30d') {

            const past30 = new Date(now.getTime() - 30 * 24 * 3600 * 1000);

            if (filterDateFrom) filterDateFrom.value = formatDate(past30);

            if (filterDateTo) filterDateTo.value = formatDate(now);

          } else if (preset === 'week') {

            const dayOfWeek = (now.getDay() + 6) % 7;

            const mon = new Date(now.getTime() - dayOfWeek * 24 * 3600 * 1000);

            if (filterDateFrom) filterDateFrom.value = formatDate(mon);

            if (filterDateTo) filterDateTo.value = formatDate(now);

          } else if (preset === 'month') {

            const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);

            if (filterDateFrom) filterDateFrom.value = formatDate(firstDay);

            if (filterDateTo) filterDateTo.value = formatDate(now);

          }



          applyFilters();

        });

      });



      if (filterDateFrom) filterDateFrom.addEventListener('change', applyFilters);

      if (filterDateTo) filterDateTo.addEventListener('change', applyFilters);

      if (filterChat) filterChat.addEventListener('change', applyFilters);

      if (filterComplexity) filterComplexity.addEventListener('change', applyFilters);

      if (filterSpeed) filterSpeed.addEventListener('change', applyFilters);



      if (filterResetBtn) {

        filterResetBtn.addEventListener('click', () => {

          if (filterDateFrom) filterDateFrom.value = '';

          if (filterDateTo) filterDateTo.value = '';

          if (filterChat) filterChat.value = 'all';

          if (filterComplexity) filterComplexity.value = 'all';

          if (filterSpeed) filterSpeed.value = 'all';

          presetBtns.forEach(b => b.classList.remove('active'));

          const allBtn = document.querySelector('.preset-btn[data-preset="all"]');

          if (allBtn) allBtn.classList.add('active');

          applyFilters();

          showToast('Filters reset to default.');

        });

      }



      if (searchChats) searchChats.addEventListener('input', renderChats);

      if (searchQuestions) searchQuestions.addEventListener('input', renderQuestions);



      // ======================================================================

      // Tab-Contextual Keyboard Shortcut [/]

      // ======================================================================

      window.addEventListener('keydown', (e) => {

        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;



        if (e.key === '1') switchTab('overview');

        else if (e.key === '2') switchTab('chats');

        else if (e.key === '3') switchTab('questions');

        else if (e.key === '4') switchTab('modes');

        else if (e.key === '5') switchTab('config');

        else if (e.key === '/') {

          e.preventDefault();

          let targetInput = null;

          if (currentActiveTab === 'chats') {

            targetInput = searchChats;

          } else if (currentActiveTab === 'questions') {

            targetInput = searchQuestions;

          } else if (currentActiveTab === 'config') {

            targetInput = searchConfig;

          } else {

            switchTab('chats');

            targetInput = searchChats;

          }

          if (targetInput) {

            targetInput.focus();

            targetInput.select();

          }

        }

        else if (e.key.toLowerCase() === 'l') {

          e.preventDefault();

          toggleLogs();

        }

        else if (e.key.toLowerCase() === 't') {

          if (themeToggle) themeToggle.click();

        }

        else if (e.key.toLowerCase() === 'm') {

          if (btnAudio) btnAudio.click();

        }

        else if (e.key === '?') {

          if (shortcutsModal) shortcutsModal.classList.toggle('open');

        }

        else if (e.key === 'Escape') {

          if (shortcutsModal) shortcutsModal.classList.remove('open');

          if (logsOpen) toggleLogs(false);

        }

      });



      // ======================================================================

      // 3-State Status Polling: Active, Paused (User Active), Inactive

      // ======================================================================

      const toggleBtn = document.getElementById('automation-toggle-btn');

      const controlIcon = document.getElementById('control-icon');

      const controlLabel = document.getElementById('control-label');

      const statusPill = document.getElementById('dashboard-status-pill');

      const statusText = document.getElementById('status-text');



      function updateStatusUI(running, isPaused, idleSec, threshold) {

        isAutomationActive = running;

        if (toggleBtn) {

          toggleBtn.classList.toggle('state-running', running);

          toggleBtn.classList.toggle('state-stopped', !running);

          controlIcon.textContent = running ? '⏹️' : '▶️';

          controlLabel.textContent = running ? 'Stop Automation' : 'Start Automation';

        }

        const modesToggleBtn = document.getElementById('modes-automation-toggle-btn');

        const modesCtrlIcon = document.getElementById('modes-control-icon');

        const modesCtrlLabel = document.getElementById('modes-control-label');

        const modesStatusPill = document.getElementById('modes-status-pill');



        if (modesToggleBtn) {

          modesToggleBtn.classList.toggle('state-running', running);

          modesToggleBtn.classList.toggle('state-stopped', !running);

          if (modesCtrlIcon) modesCtrlIcon.textContent = running ? '⏹️' : '▶️';

          if (modesCtrlLabel) modesCtrlLabel.textContent = running ? 'Stop Automation' : 'Start Automation';

        }



        if (modesStatusPill) {

          if (running) {

            if (isPaused) {

              modesStatusPill.className = 'status-pill status-paused';

              modesStatusPill.textContent = '🟡 Paused (User Active)';

            } else {

              modesStatusPill.className = 'status-pill status-active';

              modesStatusPill.textContent = '🟢 Active (Autonomous)';

            }

          } else {

            modesStatusPill.className = 'status-pill status-idle';

            modesStatusPill.textContent = '⚪ Automation Inactive';

          }

        }



        if (statusPill && statusText) {

          if (running) {

            if (isPaused) {

              statusPill.className = 'status-pill status-paused';

              statusText.textContent = '🟡 Paused (User Active)';

              statusPill.title = `Automation paused: user input detected (idle: ${idleSec || 0}s < ${threshold || 60}s)`;

              if (tickerStatusMsg) {

                tickerStatusMsg.textContent = `[PAUSED] User activity detected (idle: ${idleSec || 0}s < ${threshold || 60}s) • Automation sleeping until 60s inactivity`;

              }

            } else {

              statusPill.className = 'status-pill status-active';

              statusText.textContent = '🟢 Active (Autonomous)';

              statusPill.title = 'Automation active: autonomous background monitoring enabled';

              if (tickerStatusMsg) {

                tickerStatusMsg.textContent = `[ACTIVE] Autonomous engine executing • Background monitoring live (PID: active)`;

              }

            }

          } else {

            statusPill.className = 'status-pill status-idle';

            statusText.textContent = '⚪ Inactive';

            statusPill.title = 'Automation stopped: daemon ready to spawn';

            if (tickerStatusMsg) {

              tickerStatusMsg.textContent = `Complete Automation Daemon Ready • Ready to spawn complete_automation.py`;

            }

          }

        }

      }



      function pollServerStatus() {

        fetch(API_BASE + '/api/automation/status')

          .then(res => res.json())

          .then(data => {

            if (data && data.success && data.data) {

              const d = data.data;

              updateStatusUI(!!d.running, !!d.is_paused, d.idle_seconds, d.pause_threshold);

              if (d.mode && typeof d.mode === 'string') {

                const serverMode = d.mode.trim().toLowerCase();

                if (Date.now() - lastUserModeChangeTime > 4000) {

                  if (serverMode !== currentExecutionMode.toLowerCase()) {

                    currentExecutionMode = serverMode;

                    applyExecutionModeUI(currentExecutionMode);

                  }

                }

              }

            }

          })

          .catch(() => {});

      }

      setInterval(pollServerStatus, 2500);



      // Server-Sent Events (SSE) Live Status Stream with fallback to polling (Phase 03)

      try {

        if (typeof EventSource !== 'undefined') {

          const eventSource = new EventSource(API_BASE + '/api/automation/events');

          eventSource.addEventListener('status', (e) => {

            try {

              const payload = JSON.parse(e.data);

              if (payload && payload.success && payload.data) {

                const d = payload.data;

                updateStatusUI(!!d.running, !!d.is_paused, d.idle_seconds, d.pause_threshold);

                if (d.mode && typeof d.mode === 'string') {

                  const serverMode = d.mode.trim().toLowerCase();

                  if (serverMode !== currentExecutionMode.toLowerCase()) {

                    currentExecutionMode = serverMode;

                    applyExecutionModeUI(currentExecutionMode);

                  }

                }

              }

            } catch (_) {}

          });

          eventSource.onerror = () => {

            // On error or disconnect, EventSource auto-retries while setInterval polling provides fallback

          };

        }

      } catch (_) {}



      if (toggleBtn) {

        toggleBtn.addEventListener('click', () => {

          const endpoint = isAutomationActive ? '/api/automation/stop' : '/api/automation/start';

          toggleBtn.disabled = true;

          const bodyPayload = isAutomationActive ? {} : { mode: currentExecutionMode };

          fetch(API_BASE + endpoint, {

            method: 'POST',

            headers: { 'Content-Type': 'application/json' },

            body: JSON.stringify(bodyPayload)

          })

            .then(res => res.json())

            .then(data => {

              toggleBtn.disabled = false;

              if (data.success) {

                playChime(isAutomationActive ? 'stop' : 'start');

                showToast(isAutomationActive ? '⏹️ Automation stopped' : `▶️ Automation started in ${currentExecutionMode.toUpperCase()} mode!`);

                pollServerStatus();

              }

            })

            .catch(() => {

              toggleBtn.disabled = false;

              showToast('❌ Server request failed. Ensure server is running on port 8501');

            });

        });

      }



      // Live Logs Drawer

      const logsDrawer = document.getElementById('logs-drawer');

      const btnToggleLogs = document.getElementById('btn-toggle-logs');

      const btnCloseLogs = document.getElementById('btn-close-logs');

      const logsTerminal = document.getElementById('logs-terminal');

      const logBadge = document.getElementById('log-count-badge');

      let logsInterval = null;



      function startLogsPolling() {

        if (logsInterval) clearInterval(logsInterval);

        fetchLogs();

        logsInterval = setInterval(fetchLogs, 1500);

      }



      function stopLogsPolling() {

        if (logsInterval) {

          clearInterval(logsInterval);

          logsInterval = null;

        }

      }



      function toggleLogs(forceState) {

        logsOpen = (forceState !== undefined) ? forceState : !logsOpen;

        if (logsDrawer) logsDrawer.classList.toggle('open', logsOpen);

        if (logsOpen) {

          startLogsPolling();

        } else {

          stopLogsPolling();

        }

      }



      if (btnToggleLogs) btnToggleLogs.addEventListener('click', () => toggleLogs());

      if (btnCloseLogs) btnCloseLogs.addEventListener('click', () => toggleLogs(false));



      function fetchLogs() {

        if (!logsOpen) return;

        fetch(API_BASE + '/api/logs/tail?lines=150')

          .then(res => res.json())

          .then(data => {

            let lines = [];

            if (data && data.data) {

              if (Array.isArray(data.data.logs)) {

                lines = data.data.logs;

              } else if (typeof data.data.logs === 'string') {

                lines = data.data.logs.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);

              } else if (typeof data.data.raw === 'string') {

                lines = data.data.raw.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);

              }

            }

            logLines = lines.length;

            if (logBadge) logBadge.textContent = logLines;
            if (!logsOpen) return;

            let colored = '';

            lines.forEach(l => {

              let cls = '';

              const upper = l.toUpperCase();

              if (upper.includes('[ERROR]') || upper.includes('ERROR:')) cls = 'log-line-err';

              else if (upper.includes('[WARNING]') || upper.includes('[WARN]')) cls = 'log-line-warn';

              else if (upper.includes('[SUCCESS]') || upper.includes('PASSED') || upper.includes('SUCCESS:')) cls = 'log-line-ok';

              else if (upper.includes('[STEP') || upper.includes('STEP 0') || upper.includes('STEP 1') || upper.includes('STEP 2') || upper.includes('STEP 3') || upper.includes('STEP 4') || upper.includes('STEP 9')) cls = 'log-line-step';

              else if (upper.includes('[INFO]')) cls = 'log-line-info';

              const escaped = l.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

              colored += `<div class="${cls}">${escaped}</div>`;

            });

            if (logsTerminal) {

              const wasAtBottom = (logsTerminal.scrollHeight - logsTerminal.scrollTop - logsTerminal.clientHeight) <= 40;

              logsTerminal.innerHTML = colored || '<div style="color: #64748b; padding: 6px;">Log file empty. Waiting for automation output...</div>';

              if (autoScrollLogs && wasAtBottom) {

                logsTerminal.scrollTop = logsTerminal.scrollHeight;

              }

            }

          })

          .catch(() => {});

      }



      // Auto-Scroll Toggle

      const btnAutoScroll = document.getElementById('btn-toggle-autoscroll');

      if (btnAutoScroll) {

        btnAutoScroll.addEventListener('click', () => {

          autoScrollLogs = !autoScrollLogs;

          btnAutoScroll.textContent = 'Auto-Scroll: ' + (autoScrollLogs ? 'ON' : 'OFF');

          if (autoScrollLogs && logsTerminal) {

            logsTerminal.scrollTop = logsTerminal.scrollHeight;

          }

        });

      }



      const btnClearLogs = document.getElementById('btn-clear-logs');
      if (btnClearLogs) {
        btnClearLogs.addEventListener('click', () => {
          fetch(API_BASE + '/api/logs/clear', { method: 'POST' })
            .then(res => res.json())
            .then(d => {
              if (logsTerminal) logsTerminal.innerHTML = '<div style="color: #64748b; padding: 6px;">Console cleared. Waiting for next stream tick...</div>';
              logLines = 0;
              if (logBadge) logBadge.textContent = '0';
              showToast('Logs cleared successfully.');
            })
            .catch(err => {
              if (logsTerminal) logsTerminal.innerHTML = '<div style="color: #64748b; padding: 6px;">Console cleared locally.</div>';
              logLines = 0;
              if (logBadge) logBadge.textContent = '0';
            });
        });
      }



      // Mode Switch Controls (Ultra-Modern Interactive Lifecycle Standard)

      const btnSetProd = document.getElementById('btn-set-prod');

      const btnSetTest = document.getElementById('btn-set-test');

      const cardProd = document.getElementById('mode-card-prod') || document.getElementById('banner-card-prod');

      const cardTest = document.getElementById('mode-card-test') || document.getElementById('banner-card-test');

      const bannerBtnProd = document.getElementById('banner-mode-prod-btn');

      const bannerBtnTest = document.getElementById('banner-mode-test-btn');

      const modesToggleBtn = document.getElementById('modes-automation-toggle-btn');



      let lastUserModeChangeTime = 0;

      let currentExecutionMode = localStorage.getItem('asc_execution_mode') || 'production';



      function applyExecutionModeUI(mode) {

        const isTest = (String(mode).toLowerCase() === 'test');

        currentExecutionMode = isTest ? 'test' : 'production';

        localStorage.setItem('asc_execution_mode', currentExecutionMode);

        localStorage.setItem('asc_automation_last_mode', currentExecutionMode);



        // Header Mode Badge Dynamic Sync (Phase 03)

        const headerModeBadge = document.getElementById('header-mode-badge');

        if (headerModeBadge) {

          headerModeBadge.innerHTML = isTest ? '🧪 TEST' : '⚡ LIVE';

          headerModeBadge.style.background = isTest ? 'rgba(245, 158, 11, 0.15)' : 'rgba(16, 185, 129, 0.15)';

          headerModeBadge.style.color = isTest ? '#fbbf24' : '#34d399';

          headerModeBadge.style.borderColor = isTest ? 'rgba(245, 158, 11, 0.35)' : 'rgba(16, 185, 129, 0.35)';

          headerModeBadge.title = isTest ? 'Operating in Single-Run Test Mode (Auto-Stop on Completion) • Click to toggle to LIVE' : 'Operating in Continuous Live Mode (Continuous Loop) • Click to toggle to TEST';

        }



        // 1. Update Segmented Switcher Buttons

        const bannerProd = document.getElementById('banner-mode-prod-btn');

        const bannerTest = document.getElementById('banner-mode-test-btn');

        if (bannerProd) bannerProd.classList.toggle('active', !isTest);

        if (bannerTest) bannerTest.classList.toggle('active', isTest);



        // 2. Update Interactive Lifecycle Cards Highlight

        const cProd = document.getElementById('mode-card-prod') || document.getElementById('banner-card-prod');

        const cTest = document.getElementById('mode-card-test') || document.getElementById('banner-card-test');

        if (cProd) cProd.classList.toggle('active-mode-card', !isTest);

        if (cTest) cTest.classList.toggle('active-mode-card', isTest);



        // 3. Update Active Mode Label and Indicator Dot

        const activeDot = document.getElementById('modes-active-dot');

        const activeText = document.getElementById('modes-active-text');

        if (activeDot) activeDot.style.color = isTest ? '#f59e0b' : '#10b981';

        if (activeText) {

          activeText.innerHTML = `Active Operating Mode: <strong>${isTest ? 'TEST (परीक्षण मोड)' : 'PRODUCTION (उत्पादन मोड)'}</strong>`;

        }



        // 4. Update Mode Switch Tab Badge in Horizontal Tab Navigation

        const tabBadge = document.getElementById('tab-modes-badge');

        if (tabBadge) {

          tabBadge.textContent = isTest ? 'Test' : 'Prod';

          tabBadge.style.background = isTest ? 'rgba(245, 158, 11, 0.2)' : 'rgba(16, 185, 129, 0.2)';

          tabBadge.style.color = isTest ? '#fbbf24' : '#34d399';

        }



        // 5. Update Lifecycle Card Badges

        const badgeTxtProd = document.getElementById('mode-badge-text-prod');

        const badgeTxtTest = document.getElementById('mode-badge-text-test');

        if (badgeTxtProd) badgeTxtProd.textContent = !isTest ? 'CURRENT ACTIVE' : 'Continuous Loop';

        if (badgeTxtTest) badgeTxtTest.textContent = isTest ? 'CURRENT ACTIVE' : 'Single-Run Auto-Stop';



        // 6. Update Card Action Buttons

        const bSetProd = document.getElementById('btn-set-prod');

        const bSetTest = document.getElementById('btn-set-test');

        if (bSetProd) {

          bSetProd.textContent = !isTest ? '✓ Active in Production' : '⚡ Switch to Production Mode';

          bSetProd.className = `lifecycle-card-btn ${!isTest ? 'btn-automation' : 'btn'}`;

        }

        if (bSetTest) {

          bSetTest.textContent = isTest ? '✓ Active in Test Mode' : '⚡ Switch to Test Mode';

          bSetTest.className = `lifecycle-card-btn ${isTest ? 'btn-automation' : 'btn'}`;

          bSetTest.style.background = isTest ? '#d97706' : 'rgba(245,158,11,0.18)';

          bSetTest.style.color = isTest ? '#ffffff' : '#fbbf24';

        }

      }



      function switchMode(newMode) {

        const isTest = (newMode === 'test');

        lastUserModeChangeTime = Date.now();

        playChime('copy');

        applyExecutionModeUI(newMode);

        showToast(isTest ? '🧪 Activated Test Mode (Single-Run & Auto-Stop)' : '⚡ Activated Live Mode (Continuous Autonomous Loop)');



        // Background server persistence & silent dashboard refresh

        let payload = { mode: newMode };

        try {

          const full = collectConfigData();

          payload = Object.assign({}, full, { mode: newMode });

        } catch (_) {}



        fetch(API_BASE + '/api/config/save', {

          method: 'POST',

          headers: { 'Content-Type': 'application/json' },

          body: JSON.stringify(payload)

        })

        .then(res => res.json())

        .then(() => {

          fetch(API_BASE + '/api/dashboard/refresh', { method: 'POST' }).catch(() => {});

        })

        .catch(() => {});

      }



      if (btnSetProd) btnSetProd.addEventListener('click', (e) => { e.stopPropagation(); switchMode('production'); });

      if (btnSetTest) btnSetTest.addEventListener('click', (e) => { e.stopPropagation(); switchMode('test'); });

      if (cardProd) cardProd.addEventListener('click', () => switchMode('production'));

      if (cardTest) cardTest.addEventListener('click', () => switchMode('test'));

      if (bannerBtnProd) bannerBtnProd.addEventListener('click', () => switchMode('production'));

      if (bannerBtnTest) bannerBtnTest.addEventListener('click', () => switchMode('test'));



      // Direct Header Mode Badge Click & Keydown to toggle mode

      const headerModeBadgeEl = document.getElementById('header-mode-badge');

      if (headerModeBadgeEl) {

        headerModeBadgeEl.addEventListener('click', () => {

          const nextMode = (currentExecutionMode === 'test') ? 'production' : 'test';

          switchMode(nextMode);

        });

        headerModeBadgeEl.addEventListener('keydown', (e) => {

          if (e.key === 'Enter' || e.key === ' ') {

            e.preventDefault();

            headerModeBadgeEl.click();

          }

        });

      }



      if (modesToggleBtn) {

        modesToggleBtn.addEventListener('click', () => {

          if (toggleBtn) toggleBtn.click();

        });

      }



      // Config Form Handling & JSON Drawer

      const btnToggleJson = document.getElementById('btn-toggle-json-drawer');

      const jsonDrawer = document.getElementById('json-preview-container');

      if (btnToggleJson && jsonDrawer) {

        btnToggleJson.addEventListener('click', () => {

          const isHidden = jsonDrawer.style.display === 'none';

          jsonDrawer.style.display = isHidden ? 'block' : 'none';

          btnToggleJson.textContent = isHidden ? 'Hide Preview' : 'Toggle Preview';

        });

      }



      function collectConfigData() {

        const reqGrill = document.getElementById('cfg-antigravity-require-grillme');

        const actHrs = document.getElementById('cfg-antigravity-active-hours');

        const logVerb = document.getElementById('cfg-logging-verbose');

        const logF = document.getElementById('cfg-logging-file');



        return {

          mode: currentExecutionMode,

          timing: {

            step0_poll_interval_prod_seconds: parseFloat(document.getElementById('cfg-timing-prod-poll').value) || 1.0,

            step0_poll_interval_test_seconds: parseFloat(document.getElementById('cfg-timing-test-poll').value) || 0.1,

            settle_delay_between_steps_seconds: parseFloat(document.getElementById('cfg-timing-settle').value) || 1.0,

            user_activity_pause_threshold_seconds: parseFloat(document.getElementById('cfg-pause-threshold').value) || 60.0,

            step4_user_activity_delay_seconds: parseFloat(document.getElementById('cfg-timing-activity-delay').value) || 10.0,

            step4_poll_interval_seconds: parseFloat(document.getElementById('cfg-timing-step4-poll').value) || 0.5,

            step1_window_focus_delay_seconds: parseFloat(document.getElementById('cfg-timing-step1-focus').value) || 0.5,

            step2_dom_click_settle_delay_seconds: parseFloat(document.getElementById('cfg-timing-step2-dom-settle').value) || 1.0,

            step3_countdown_seconds: parseInt(document.getElementById('cfg-timing-step3-countdown').value, 10) || 3,

            step3_key_hold_delay_ms: parseInt(document.getElementById('cfg-timing-step3-hold-ms').value, 10) || 80,

            step3_post_keypress_delay_ms: parseInt(document.getElementById('cfg-timing-step3-post-ms').value, 10) || 100,

            step3_inter_question_delay_ms: parseInt(document.getElementById('cfg-timing-step3-inter-q-ms').value, 10) || 200,

            step3_round_completion_pause_ms: parseInt(document.getElementById('cfg-timing-step3-round-ms').value, 10) || 500,

            continuous_loop_delay_seconds: parseFloat(document.getElementById('cfg-continuous-delay').value) || 300.0,

          },

          enabled_steps: {

            step1_find_and_focus: document.getElementById('cfg-step1-enabled').checked,

            step2_gui_chat_select: document.getElementById('cfg-step2-enabled').checked,

            step3_keyboard_automation: document.getElementById('cfg-step3-enabled').checked,

            step4_reporting: document.getElementById('cfg-step4-enabled').checked,

          },

          antigravity: {

            require_grill_me: reqGrill ? reqGrill.checked : true,

            active_hours: actHrs ? (parseFloat(actHrs.value) || 12.0) : 12.0,

          },

          logging: {

            verbose: logVerb ? logVerb.checked : true,

            log_file: logF ? logF.value.trim() : 'complete_automation.log',

          }

        };

      }



      function saveConfigChanges() {

        const payload = collectConfigData();

        fetch(API_BASE + '/api/config/save', {

          method: 'POST',

          headers: { 'Content-Type': 'application/json' },

          body: JSON.stringify(payload)

        })

        .then(res => res.json())

        .then(d => {

          playChime('copy');

          showToast('✅ Configuration successfully saved to config.json!');

          const unsavedDock = document.getElementById('unsaved-changes-dock');

          if (unsavedDock) unsavedDock.classList.remove('visible');

          setTimeout(() => location.reload(), 800);

        })

        .catch(() => showToast('❌ Failed to save configuration to local server.'));

      }



      const btnSaveRuntimeCfg = document.getElementById('btn-save-runtime-config');

      const btnSaveDock = document.getElementById('btn-save-config-dock');

      if (btnSaveRuntimeCfg) btnSaveRuntimeCfg.addEventListener('click', saveConfigChanges);

      if (btnSaveDock) btnSaveDock.addEventListener('click', saveConfigChanges);



      // Copy CLI Command

      const btnCopyCli = document.getElementById('btn-copy-cli-cmd');

      if (btnCopyCli) {

        btnCopyCli.addEventListener('click', () => {

          const cmd = 'python step_9_complete_automation/complete_automation.py';

          navigator.clipboard.writeText(cmd).then(() => {

            playChime('copy');

            showToast('📋 Copied CLI command to clipboard!');

          });

        });

      }



      // Download config.json directly

      const btnDownloadCfg = document.getElementById('btn-download-runtime-cfg');

      if (btnDownloadCfg) {

        btnDownloadCfg.addEventListener('click', () => {

          const payload = collectConfigData();

          const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });

          const url = URL.createObjectURL(blob);

          const a = document.createElement('a');

          a.href = url;

          a.download = 'config.json';

          a.click();

          URL.revokeObjectURL(url);

          playChime('copy');

          showToast('📥 Downloaded config.json successfully.');

        });

      }



      // Export Configuration JSON

      const btnExportCfg = document.getElementById('btn-export-config');

      if (btnExportCfg) {

        btnExportCfg.addEventListener('click', () => {

          const payload = collectConfigData();

          const blob = new Blob([JSON.stringify(payload, null, 2)], { type: 'application/json' });

          const url = URL.createObjectURL(blob);

          const a = document.createElement('a');

          a.href = url;

          a.download = 'config_export.json';

          a.click();

          URL.revokeObjectURL(url);

          showToast('📤 Configuration JSON exported.');

        });

      }



      // Export History JSON

      const btnExportHist = document.getElementById('cfg-export-btn');

      if (btnExportHist) {

        btnExportHist.addEventListener('click', () => {

          const blob = new Blob([JSON.stringify(rawData, null, 2)], { type: 'application/json' });

          const url = URL.createObjectURL(blob);

          const a = document.createElement('a');

          a.href = url;

          a.download = 'automation_history.json';

          a.click();

          URL.revokeObjectURL(url);

          playChime('copy');

          showToast('📥 Exported automation_history.json successfully.');

        });

      }



      // Reset Dashboard Preferences

      const btnResetDash = document.getElementById('cfg-reset-btn');

      if (btnResetDash) {

        btnResetDash.addEventListener('click', () => {

          localStorage.removeItem('asc_theme');

          localStorage.removeItem('asc_dashboard_tab');

          localStorage.removeItem('asc_audio_muted');

          showToast('🔄 Dashboard preferences reset to factory defaults.');

          setTimeout(() => location.reload(), 500);

        });

      }



      // Test Audio Chime Audition

      const btnTestChime = document.getElementById('btn-test-chime');

      if (btnTestChime) {

        btnTestChime.addEventListener('click', () => {

          playChime('start');

          setTimeout(() => playChime('copy'), 220);

          showToast('🔔 Web Audio Chime played!');

        });

      }



      // Filter Toolbar Collapse / Expand Toggle

      const filterCollapseBtn = document.getElementById('filter-collapse-btn');

      const filterToolbar = document.getElementById('contextual-filter-toolbar');

      if (filterCollapseBtn && filterToolbar) {

        filterCollapseBtn.addEventListener('click', () => {

          const isCollapsed = filterToolbar.classList.toggle('collapsed');

          filterCollapseBtn.textContent = isCollapsed ? '▸ Expand' : '▾ Collapse';

        });

      }



      // 1-Click Automation Scripts Modal Controls

      const automationModal = document.getElementById('automation-modal');

      const btnOpenAutoModal = document.getElementById('btn-open-automation-modal');

      const btnCloseAutoModal = document.getElementById('btn-close-automation-modal');

      const btnCloseAutoFooter = document.getElementById('btn-close-automation-modal-footer');



      if (btnOpenAutoModal && automationModal) {

        btnOpenAutoModal.addEventListener('click', () => automationModal.classList.add('open'));

      }

      if (btnCloseAutoModal && automationModal) {

        btnCloseAutoModal.addEventListener('click', () => automationModal.classList.remove('open'));

      }

      if (btnCloseAutoFooter && automationModal) {

        btnCloseAutoFooter.addEventListener('click', () => automationModal.classList.remove('open'));

      }



      // Copy buttons inside automation modal

      document.querySelectorAll('.btn-copy-cmd').forEach(btn => {

        btn.addEventListener('click', () => {

          const cmd = btn.getAttribute('data-cmd') || '';

          navigator.clipboard.writeText(cmd).then(() => {

            playChime('copy');

            showToast('📋 Copied script command to clipboard: ' + cmd);

          });

        });

      });



      // Synchronous Telemetry Refresh via Server API

      const btnHeaderRefresh = document.getElementById('btn-header-refresh');

      if (btnHeaderRefresh) {

        btnHeaderRefresh.addEventListener('click', () => {

          btnHeaderRefresh.disabled = true;

          const spinIcon = document.getElementById('refresh-spin-icon');

          if (spinIcon) spinIcon.style.display = 'inline-block';

          if (spinIcon) spinIcon.style.animation = 'spin 0.6s linear infinite';

          showToast('🔄 Synchronizing telemetry from disk and regenerating dashboard...');

          fetch(API_BASE + '/api/dashboard/refresh', { method: 'POST' })

            .then(res => res.json())

            .then(d => {

              playChime('copy');

              showToast('✅ Telemetry synchronized! Reloading...');

              setTimeout(() => location.reload(), 400);

            })

            .catch(() => {

              location.reload();

            });

        });

      }



      // Config Unsaved Dock

      const unsavedDock = document.getElementById('unsaved-changes-dock');

      const cfgInputs = document.querySelectorAll('.cfg-input, .switch-toggle input');

      cfgInputs.forEach(inp => {

        inp.addEventListener('input', () => {

          if (unsavedDock) unsavedDock.classList.add('visible');

        });

        inp.addEventListener('change', () => {

          if (unsavedDock) unsavedDock.classList.add('visible');

        });

      });

      const btnDiscardCfg = document.getElementById('btn-discard-config');

      if (btnDiscardCfg) {

        btnDiscardCfg.addEventListener('click', () => {

          if (unsavedDock) unsavedDock.classList.remove('visible');

          showToast('Changes discarded.');

          setTimeout(() => location.reload(), 400);

        });

      }



      // Theme Toggle

      const themeToggle = document.getElementById('theme-toggle');

      if (themeToggle) {

        themeToggle.addEventListener('click', () => {

          const cur = document.documentElement.getAttribute('data-theme') || 'dark';

          const next = cur === 'dark' ? 'light' : 'dark';

          document.documentElement.setAttribute('data-theme', next);

          localStorage.setItem('asc_theme', next);

        });

      }

      const savedTheme = localStorage.getItem('asc_theme');

      if (savedTheme) document.documentElement.setAttribute('data-theme', savedTheme);



      // Audio Toggle

      const btnAudio = document.getElementById('btn-audio-toggle');

      if (btnAudio) {

        btnAudio.addEventListener('click', () => {

          audioMuted = !audioMuted;

          localStorage.setItem('asc_audio_muted', audioMuted);

          document.getElementById('audio-icon').textContent = audioMuted ? '🔕' : '🔔';

          showToast(audioMuted ? 'Audio Chimes Muted' : 'Audio Chimes Enabled');

          if (!audioMuted) playChime('copy');

        });

      }



      // Keyboard Shortcuts Modal

      const shortcutsModal = document.getElementById('shortcuts-modal');

      const btnHelp = document.getElementById('btn-help-shortcuts');

      const btnCloseModal = document.getElementById('btn-close-modal');



      if (btnHelp) btnHelp.addEventListener('click', () => shortcutsModal.classList.add('open'));

      if (btnCloseModal) btnCloseModal.addEventListener('click', () => shortcutsModal.classList.remove('open'));



      // Auto-refresh countdown (Dynamic based on configuration / #cfg-auto-refresh)
      const countEl = document.getElementById('refresh-countdown');
      const cfgAutoRefreshSelect = document.getElementById('cfg-auto-refresh');
      let refreshIntervalSeconds = cfgAutoRefreshSelect ? parseInt(cfgAutoRefreshSelect.value, 10) : 10;
      let count = isNaN(refreshIntervalSeconds) ? 10 : refreshIntervalSeconds;

      if (cfgAutoRefreshSelect) {
        cfgAutoRefreshSelect.addEventListener('change', () => {
          refreshIntervalSeconds = parseInt(cfgAutoRefreshSelect.value, 10);
          count = isNaN(refreshIntervalSeconds) ? 10 : refreshIntervalSeconds;
          if (refreshIntervalSeconds <= 0) {
            if (countEl) countEl.textContent = 'OFF';
          } else {
            if (countEl) countEl.textContent = count + 's';
          }
        });
      }

      setInterval(() => {
        if (isNaN(refreshIntervalSeconds) || refreshIntervalSeconds <= 0) {
          if (countEl) countEl.textContent = 'OFF';
          return;
        }
        count--;
        if (countEl) countEl.textContent = count + 's';
        if (count <= 0) {
          count = refreshIntervalSeconds;
          showToast('Auto-refreshing dashboard and telemetry...');
          fetch(API_BASE + '/api/dashboard/refresh', { method: 'POST' })
            .then(res => res.json())
            .then(d => {
              location.reload();
            })
            .catch(() => {
              pollServerStatus();
            });
        }
      }, 1000);



      // Initialize

      pollServerStatus();

      applyFilters();

      applyExecutionModeUI(currentExecutionMode);



    })();

  