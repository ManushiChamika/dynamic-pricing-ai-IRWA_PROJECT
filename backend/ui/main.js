(function(){
  const qs = s=>document.querySelector(s);
  const qsa = s=>Array.from(document.querySelectorAll(s));
  const $threads = qs('#threadsList');
  const $msgs = qs('#messages');
  const $title = qs('#threadTitle');
  const $send = qs('#send');
  const $input = qs('#input');
  const $user = qs('#userName');
  const $stream = qs('#streaming');
  const $thinking = qs('#showThinking');
  const $newThread = qs('#newThreadBtn');
  const $exportBtn = qs('#exportBtn');
  const $importFile = qs('#importFile');
  const $themeToggle = qs('#themeToggle');
  const $settingsBtn = qs('#settingsBtn');
  const $renameTitle = qs('#renameThreadBtn');
  const $deleteThreadBtn = qs('#deleteThreadBtn');
  const $settingsPanel = qs('#settingsPanel');
  const $closeSettings = qs('#closeSettings');
  const $optShowModel = qs('#optShowModel');
  const $optShowTimestamps = qs('#optShowTimestamps');
  const $optShowMeta = qs('#optShowMeta');
  const $optShowThinking = qs('#optShowThinking');
  const $optMode = qs('#optMode');
  const $optStreaming = qs('#optStreaming');
  const $sidebar = qs('#sidebar');
  const $collapseSidebar = qs('#collapseSidebar');
  const $authBtn = qs('#authBtn');
  const $authPanel = qs('#authPanel');
  const $closeAuth = qs('#closeAuth');
  const $authEmail = qs('#authEmail');
  const $authPassword = qs('#authPassword');
  const $loginBtn = qs('#loginBtn');
  const $registerBtn = qs('#registerBtn');
  const $logoutBtn = qs('#logoutBtn');
  const $authLoggedOut = qs('#authLoggedOut');
  const $authLoggedIn = qs('#authLoggedIn');
  const $authUser = qs('#authUser');
  const $toasts = qs('#toasts');
  const $confirmPanel = qs('#confirmPanel');
  const $confirmMessage = qs('#confirmMessage');
  const $confirmOk = qs('#confirmOk');
  const $confirmCancel = qs('#confirmCancel');
  const $closeConfirm = qs('#closeConfirm');
  const $promptPanel = qs('#promptPanel');
  const $promptTitle = qs('#promptTitle');
  const $promptLabel = qs('#promptLabel');
  const $promptInput = qs('#promptInput');
  const $promptTextarea = qs('#promptTextarea');
  const $promptOk = qs('#promptOk');
  const $promptCancel = qs('#promptCancel');
  const $closePrompt = qs('#closePrompt');
  const $stopBtn = qs('#stopBtn');

  const state = {
    theme: localStorage.getItem('theme') || 'dark',
    showModel: true,
    showTimestamps: false,
    showThinking: false,
    showMeta: false,
    mode: 'user',
    streaming: 'sse',
    threadId: null,
    messages: [],
    token: localStorage.getItem('token') || '',
    streamController: null,
    streamingActive: false
  };

  function setStreamingActive(active){
    state.streamingActive = !!active;
    if($stopBtn) $stopBtn.classList.toggle('hidden', !state.streamingActive);
    if($send) $send.classList.toggle('hidden', state.streamingActive);
    if($input) $input.disabled = state.streamingActive;
    if($user) $user.disabled = state.streamingActive;
    if($stream) $stream.disabled = state.streamingActive;
    if($thinking) $thinking.disabled = state.streamingActive;
  }

  function getToken(){ return state.token || ''; }


  function setToken(t){
    state.token = t || '';
    if(state.token){ localStorage.setItem('token', state.token); }
    else { localStorage.removeItem('token'); }
    // Refresh settings to reflect server-side preferences if any
    initSettings();
  }

  function applyTheme(){
    const root = document.documentElement;
    if(state.theme === 'light') root.classList.add('light'); else root.classList.remove('light');
  }
  applyTheme();

  function applySidebarCollapsed(collapsed){
    if(collapsed){
      $sidebar.classList.add('collapsed');
      if($collapseSidebar) $collapseSidebar.textContent = '⮞';
    } else {
      $sidebar.classList.remove('collapsed');
      if($collapseSidebar) $collapseSidebar.textContent = '⮜';
    }
  }

  // Toasts
  function toast(msg, isError){
    if(!$toasts) return;
    const el = document.createElement('div');
    el.className = 'toast' + (isError?' error':'');
    el.textContent = msg;
    $toasts.appendChild(el);
    setTimeout(()=>{ el.remove(); }, 1800);
  }

  // Centralized fetch with unified error handling
  async function apiFetch(url, opts){
    opts = opts || {};
    const init = { method: opts.method || 'GET', headers: {...(opts.headers||{})} };
    if(opts.json){
      init.headers['content-type'] = 'application/json';
      init.body = JSON.stringify(opts.json);
    } else if(opts.body != null){
      init.body = opts.body;
    }
    try{
      const r = await fetch(url, init);
      let data = null;
      const ct = r.headers.get('content-type')||'';
      if(ct.includes('application/json')){ try{ data = await r.json(); }catch(e){} }
      if(!r.ok && !opts.silent){
        const msg = (data && (data.detail || data.error)) || `${init.method} ${url} failed (${r.status})`;
        toast(msg, true);
      }
      return {ok:r.ok, status:r.status, data, response:r};
    }catch(e){
      if(!opts.silent) toast('Network error', true);
      return {ok:false, status:0, data:null, error:e};
    }
  }

  // Confirm modal
  const confirmState = { resolve: null, lastFocus: null };
  function confirmDialog(message, opts){
    opts = opts || {};
    if(!$confirmPanel) return Promise.resolve(window.confirm(message));
    $confirmMessage.textContent = message || 'Are you sure?';
    if(opts.okText) $confirmOk.textContent = opts.okText;
    else $confirmOk.textContent = 'OK';
    if(opts.cancelText) $confirmCancel.textContent = opts.cancelText;
    else $confirmCancel.textContent = 'Cancel';
    $confirmPanel.classList.remove('hidden');
    confirmState.lastFocus = document.activeElement;
    setTimeout(()=>{ $confirmOk.focus(); }, 0);
    return new Promise((resolve)=>{ confirmState.resolve = resolve; });
  }
  function closeConfirm(result){
    if($confirmPanel) $confirmPanel.classList.add('hidden');
    const r = confirmState.resolve; confirmState.resolve = null;
    if(confirmState.lastFocus && confirmState.lastFocus.focus) confirmState.lastFocus.focus();
    if(r) r(!!result);
  }
  if($confirmPanel){
    $confirmPanel.addEventListener('click', (e)=>{ if(e.target === $confirmPanel) closeConfirm(false); });
    $confirmPanel.addEventListener('keydown', (e)=>{
      if(e.key==='Escape'){ e.preventDefault(); closeConfirm(false); }
      if(e.key==='Enter'){ e.preventDefault(); closeConfirm(true); }
    });
  }
  if($confirmOk) $confirmOk.addEventListener('click', ()=>closeConfirm(true));
  if($confirmCancel) $confirmCancel.addEventListener('click', ()=>closeConfirm(false));
  if($closeConfirm) $closeConfirm.addEventListener('click', ()=>closeConfirm(false));

  // Input modal
  const inputState = { resolve: null, lastFocus: null, multiline: false };
  function inputDialog(opts){
    opts = opts || {};
    if(!$promptPanel){
      const val = window.prompt(opts.title || 'Input', opts.defaultValue || '');
      return Promise.resolve(val==null?null:String(val));
    }
    $promptTitle.textContent = opts.title || 'Input';
    $promptLabel.textContent = opts.label || 'Value';
    $promptInput.classList.toggle('hidden', !!opts.multiline);
    $promptTextarea.classList.toggle('hidden', !opts.multiline);
    inputState.multiline = !!opts.multiline;
    if(opts.placeholder){
      $promptInput.placeholder = opts.placeholder;
      $promptTextarea.placeholder = opts.placeholder;
    } else {
      $promptInput.placeholder = '';
      $promptTextarea.placeholder = '';
    }
    const def = opts.defaultValue != null ? String(opts.defaultValue) : '';
    $promptInput.value = def;
    $promptTextarea.value = def;
    $promptOk.textContent = opts.okText || 'OK';
    $promptCancel.textContent = opts.cancelText || 'Cancel';

    inputState.lastFocus = document.activeElement;
    $promptPanel.classList.remove('hidden');
    setTimeout(()=>{
      if(inputState.multiline){ $promptTextarea.focus(); $promptTextarea.selectionStart=0; $promptTextarea.selectionEnd=($promptTextarea.value||'').length; }
      else { $promptInput.focus(); $promptInput.select(); }
    }, 0);

    return new Promise((resolve)=>{ inputState.resolve = resolve; });
  }
  function closePrompt(resultOk){
    if($promptPanel) $promptPanel.classList.add('hidden');
    const r = inputState.resolve; inputState.resolve = null;
    if(inputState.lastFocus && inputState.lastFocus.focus) inputState.lastFocus.focus();
    if(!r) return;
    if(resultOk){
      const val = inputState.multiline ? $promptTextarea.value : $promptInput.value;
      r(String(val));
    } else {
      r(null);
    }
  }
  if($promptPanel){
    $promptPanel.addEventListener('click', (e)=>{ if(e.target === $promptPanel) closePrompt(false); });
    $promptPanel.addEventListener('keydown', (e)=>{
      if(e.key==='Escape'){ e.preventDefault(); closePrompt(false); }
      if(!inputState.multiline && e.key==='Enter'){ e.preventDefault(); closePrompt(true); }
      if(inputState.multiline && (e.key==='Enter' && (e.ctrlKey||e.metaKey))){ e.preventDefault(); closePrompt(true); }
    });
  }
  if($promptOk) $promptOk.addEventListener('click', ()=>closePrompt(true));
  if($promptCancel) $promptCancel.addEventListener('click', ()=>closePrompt(false));
  if($closePrompt) $closePrompt.addEventListener('click', ()=>closePrompt(false));
  if($promptInput){
    $promptInput.addEventListener('keydown', (e)=>{
      if(e.key==='Enter'){ e.preventDefault(); closePrompt(true); }
    });
  }

  async function updateSettings(partial){
    // Update server settings if token exists; always mirror locally
    Object.assign(state, partial || {});
    if(partial && partial.theme){ localStorage.setItem('theme', partial.theme); }
    if(getToken()){
      await apiFetch('/api/settings', {method:'PUT', json:{token: getToken(), settings: partial}});
    }
  }

  async function initSettings(){
    const t = getToken();
    const url = t ? `/api/settings?token=${encodeURIComponent(t)}` : '/api/settings';
    const {ok, data} = await apiFetch(url);
    if(ok && data && data.settings){
      state.showThinking = !!data.settings.show_thinking;
      state.showTimestamps = !!data.settings.show_timestamps;
      state.showModel = !!data.settings.show_model_tag;
      state.showMeta = !!data.settings.show_metadata_panel;
      state.theme = data.settings.theme || state.theme;
      state.streaming = data.settings.streaming || state.streaming;
      state.mode = data.settings.mode || state.mode;
    }
    applyTheme();
    syncSettingsUI();
  }

  function syncSettingsUI(){
    if($thinking) $thinking.checked = !!state.showThinking;
    if($optShowThinking) $optShowThinking.checked = !!state.showThinking;
    if($optShowModel) $optShowModel.checked = !!state.showModel;
    if($optShowTimestamps) $optShowTimestamps.checked = !!state.showTimestamps;
    if($optShowMeta) $optShowMeta.checked = !!state.showMeta;
    if($optMode) $optMode.value = state.mode || 'user';
    if($optStreaming) $optStreaming.value = state.streaming || 'sse';
    if($stream) $stream.checked = (state.streaming === 'sse');
  }

  $themeToggle.addEventListener('click', async ()=>{
    state.theme = (state.theme === 'light' ? 'dark' : 'light');
    applyTheme();
    localStorage.setItem('theme', state.theme);
    await updateSettings({theme: state.theme});
  });

  $thinking.addEventListener('change', async ()=>{
    state.showThinking = !!$thinking.checked;
    if($optShowThinking) $optShowThinking.checked = state.showThinking;
    await updateSettings({show_thinking: state.showThinking});
  });

  if($settingsBtn){
    $settingsBtn.addEventListener('click', (e)=>{
      e.preventDefault();
      syncSettingsUI();
      $settingsPanel.classList.remove('hidden');
    });
  }
  if($authBtn){
    $authBtn.addEventListener('click', async ()=>{
      // Check session
      const t = getToken();
      if(t){
        try{
          const {ok, data} = await apiFetch(`/api/me?token=${encodeURIComponent(t)}`);
          if(ok && data && data.ok){
            $authUser.textContent = data.user.email || '';
            $authLoggedOut.classList.add('hidden');
            $authLoggedIn.classList.remove('hidden');
          } else {
            $authLoggedOut.classList.remove('hidden');
            $authLoggedIn.classList.add('hidden');
          }
        }catch(e){
          $authLoggedOut.classList.remove('hidden');
          $authLoggedIn.classList.add('hidden');
        }
      } else {
        $authLoggedOut.classList.remove('hidden');
        $authLoggedIn.classList.add('hidden');
      }
      $authPanel.classList.remove('hidden');
    });
  }
  if($closeAuth){
    $closeAuth.addEventListener('click', ()=> $authPanel.classList.add('hidden'));
  }
  if($authPanel){
    $authPanel.addEventListener('click', (e)=>{ if(e.target === $authPanel) $authPanel.classList.add('hidden'); });
  }
  if($loginBtn){
    $loginBtn.addEventListener('click', async ()=>{
      const email = ($authEmail.value||'').trim();
      const password = ($authPassword.value||'').trim();
      if(!email || !password){ toast('Email and password required', true); return; }
      const {ok, data} = await apiFetch('/api/login', {method:'POST', json:{email, password}});
      if(!ok || !data || !data.ok){ toast((data && data.detail) || 'Login failed', true); return; }
      setToken(data.token);
      $authPanel.classList.add('hidden');
    });
  }
  if($registerBtn){
    $registerBtn.addEventListener('click', async ()=>{
      const email = ($authEmail.value||'').trim();
      const password = ($authPassword.value||'').trim();
      if(!email || !password){ toast('Email and password required', true); return; }
      const {ok, data} = await apiFetch('/api/register', {method:'POST', json:{email, password}});
      if(!ok || !data || !data.ok){ toast((data && data.detail) || 'Register failed', true); return; }
      setToken(data.token);
      $authPanel.classList.add('hidden');
    });
  }
  if($logoutBtn){
    $logoutBtn.addEventListener('click', async ()=>{
      const t = getToken();
      if(!t){ $authPanel.classList.add('hidden'); return; }
      await apiFetch('/api/logout', {method:'POST', json:{token: t}});
      setToken('');
      $authPanel.classList.add('hidden');
    });
  }
  if($closeSettings){
    $closeSettings.addEventListener('click', ()=>{
      $settingsPanel.classList.add('hidden');
    });
  }
  if($settingsPanel){
    $settingsPanel.addEventListener('click', (e)=>{
      if(e.target === $settingsPanel){ $settingsPanel.classList.add('hidden'); }
    });
  }

  if($optShowModel){
    $optShowModel.addEventListener('change', async ()=>{
      state.showModel = !!$optShowModel.checked;
      await updateSettings({show_model_tag: state.showModel});
      await refreshMessages();
    });
  }
  if($optShowTimestamps){
    $optShowTimestamps.addEventListener('change', async ()=>{
      state.showTimestamps = !!$optShowTimestamps.checked;
      await updateSettings({show_timestamps: state.showTimestamps});
      await refreshMessages();
    });
  }
  if($optShowMeta){
    $optShowMeta.addEventListener('change', async ()=>{
      state.showMeta = !!$optShowMeta.checked;
      await updateSettings({show_metadata_panel: state.showMeta});
      await refreshMessages();
    });
  }
  if($optShowThinking){
    $optShowThinking.addEventListener('change', async ()=>{
      state.showThinking = !!$optShowThinking.checked;
      if($thinking) $thinking.checked = state.showThinking;
      await updateSettings({show_thinking: state.showThinking});
    });
  }
  if($optMode){
    $optMode.addEventListener('change', async ()=>{
      state.mode = $optMode.value || 'user';
      await updateSettings({mode: state.mode});
    });
  }
  if($optStreaming){
    $optStreaming.addEventListener('change', async ()=>{
      state.streaming = $optStreaming.value || 'sse';
      if($stream) $stream.checked = (state.streaming === 'sse');
      await updateSettings({streaming: state.streaming});
    });
  }

  if($collapseSidebar){
    // Initialize from localStorage
    const collapsed = localStorage.getItem('sidebarCollapsed') === '1';
    applySidebarCollapsed(collapsed);
    $collapseSidebar.addEventListener('click', ()=>{
      const now = !$sidebar.classList.contains('collapsed');
      applySidebarCollapsed(now);
      localStorage.setItem('sidebarCollapsed', now ? '1' : '0');
    });
  }

  function li(text, id){
    const el = document.createElement('li');
    el.textContent = text;
    if(id) el.dataset.id = id;
    el.addEventListener('click', ()=>selectThread(Number(el.dataset.id)));
    el.addEventListener('dblclick', async ()=>{
      // Sidebar rename on double-click
      if(!el.dataset.id) return;
      const old = el.textContent || '';
      const val = await inputDialog({title:'Rename thread', label:'Title', defaultValue: old});
      if(val==null) return;
      const newTitle = val.trim();
      if(!newTitle || newTitle===old) return;
      try{
        const {ok} = await apiFetch(`/api/threads/${el.dataset.id}`, {method:'PATCH', json:{title:newTitle}});
        if(!ok) throw new Error('rename failed');
        await listThreads();
        if(state.threadId === Number(el.dataset.id)) $title.textContent = newTitle;
      }catch(e){ /* handled by apiFetch toast */ }
    });
    return el;
  }

  async function listThreads(){
    const {ok, data} = await apiFetch('/api/threads');
    if(!ok || !Array.isArray(data)) return;
    $threads.innerHTML = '';
    data.forEach(t=>{
      const el = li(t.title || ('Thread #' + t.id), t.id);
      if (state.threadId === t.id) el.classList.add('active');
      $threads.appendChild(el);
    });
    // If a thread is selected, update header title to actual title
    if(state.threadId){
      const cur = data.find(x=>x.id===state.threadId);
      if(cur){ $title.textContent = cur.title || ('Thread #' + cur.id); }
    }
    // If no thread selected, restore lastThreadId if present
    if(!state.threadId){
      const last = Number(localStorage.getItem('lastThreadId')||'');
      if(last && data.some(x=>x.id===last)){
        await selectThread(last);
      }
    }
  }

  async function createThread(){
    const title = await inputDialog({title:'Create thread', label:'Title', defaultValue:'New Thread'});
    if(title==null) return;
    const trimmed = title.trim();
    const {ok, data} = await apiFetch('/api/threads', {method:'POST', json:{title: trimmed || 'New Thread'}});
    if(!ok || !data) return;
    await listThreads();
    await selectThread(data.id);
  }

  async function selectThread(id){
    state.threadId = id;
    localStorage.setItem('lastThreadId', String(id));
    // Try to reflect actual title by reading from current list item
    const activeLi = qsa('.threads li').find(li=>Number(li.dataset.id)===id);
    $title.textContent = activeLi ? activeLi.textContent : ('Thread #' + id);
    qsa('.threads li').forEach(li=>li.classList.toggle('active', Number(li.dataset.id)===id));
    await refreshMessages();
  }

  function renderMessage(m){
    const div = document.createElement('div');
    div.className = 'msg ' + (m.role||'');
    const created = m.created_at ? new Date(m.created_at).toLocaleString() : '';
    const modelComputed = m.model || (m.metadata && m.metadata.provider ? (m.metadata.provider + (m.model?(':'+m.model):'')) : '');
    const info = [];
    if (created) info.push(`time ${created}`);
    if (modelComputed) info.push(`model ${modelComputed}`);
    if (m.token_in!=null || m.token_out!=null) info.push(`tokens ${m.token_in||0}/${m.token_out||0}`);
    if (m.cost_usd!=null) info.push(`$${m.cost_usd}`);
    if (m.api_calls!=null) info.push(`${m.api_calls} api`);
    if (m.agents && typeof m.agents==='object' && m.agents.count!=null) info.push(`${m.agents.count} agents`);
    if (m.tools && typeof m.tools==='object' && m.tools.count!=null) info.push(`${m.tools.count} tools`);

    const agentsActivated = (m && m.agents && Array.isArray(m.agents.activated)) ? m.agents.activated : [];
    const agentsHtml = (agentsActivated.length>0)
      ? `<div class="agents" title="Agents activated">${agentsActivated.join(', ')}</div>`
      : '';

    const actionsHtml = `
      <div class="actions">
        <button data-act="copy" title="Copy message">Copy</button>
        ${m.role==='user'?'<button data-act="edit" title="Edit your message">Edit</button>':''}
        <button data-act="delete" title="Delete message">Del</button>
        <button data-act="branch" title="Start a new branch here">Branch</button>
      </div>`;

    const metaHtml = `
      <div class="meta">
        ${state.showTimestamps?`<span class="time" title="${created}">${created}</span>`:''}
        ${state.showMeta && info.length?`<span class="info" title="${info.join('\n')}">ℹ️</span>`:''}
        ${(m.role==='assistant' && state.showModel && modelComputed)?`<span class="model" title="${modelComputed}">${modelComputed}</span>`:''}
      </div>`;

    div.innerHTML = `
      ${agentsHtml}
      <div class="bubble">${escapeHtml(m.content||'')}</div>
      ${actionsHtml}
      ${metaHtml}`;

    div.setAttribute('tabindex','0');
    div.addEventListener('keydown', (e)=>{
      if(e.key==='c' && !e.shiftKey && !e.altKey && !e.ctrlKey){ e.preventDefault(); onCopy(m); }
      if(e.key==='e' && !e.shiftKey && !e.altKey && !e.ctrlKey){ e.preventDefault(); const btn=div.querySelector('[data-act="edit"]'); if(btn) onEdit(m); }
      if(e.key==='Delete'){ e.preventDefault(); onDelete(m); }
    });

    const btnEdit = div.querySelector('[data-act="edit"]');
    if(btnEdit) btnEdit.addEventListener('click', ()=>onEdit(m));
    const btnCopy = div.querySelector('[data-act="copy"]');
    if(btnCopy) btnCopy.addEventListener('click', ()=>onCopy(m));
    div.querySelector('[data-act="delete"]').addEventListener('click', ()=>onDelete(m));
    div.querySelector('[data-act="branch"]').addEventListener('click', ()=>onBranch(m));
    return div;
  }

  async function refreshMessages(){
    if(!state.threadId){
      $msgs.innerHTML = '<div class="empty">Select or create a thread to begin.</div>';
      return;
    }
    const {ok, data} = await apiFetch(`/api/threads/${state.threadId}/messages`);
    if(!ok || !Array.isArray(data)) return;
    state.messages = data;
    $msgs.innerHTML = '';
    if(data.length===0){
      $msgs.innerHTML = '<div class="empty">No messages yet. Say hello!</div>';
    } else {
      data.forEach(m=> $msgs.appendChild(renderMessage(m)) );
    }
    $msgs.scrollTop = $msgs.scrollHeight;
  }

  function escapeHtml(s){
    return String(s).replace(/[&<>]/g, c=>({"&":"&amp;","<":"&lt;",
      ">":"&gt;"}[c]))
  }

  async function send(){
    if(!state.threadId){
      toast('Select or create a thread first', true);
      return;
    }
    const content = $input.value.trim();
    if(!content) return;
    const user_name = $user.value || 'user';

    if($stream && $stream.checked){
      await streamPost(content, user_name);
    } else {
      const r = await apiFetch(`/api/threads/${state.threadId}/messages?token=${encodeURIComponent(getToken())}`, {
        method:'POST', json:{user_name, content}
      });
      if(!r.ok) return;
      await refreshMessages();
    }
    $input.value = '';
  }

  async function streamPost(content, user_name){
    const showThinking = $thinking && $thinking.checked;
    const ctrl = new AbortController();
    state.streamController = ctrl;
    setStreamingActive(true);
    let aborted = false;
    try{
      const resp = await fetch(`/api/threads/${state.threadId}/messages/stream?token=${encodeURIComponent(getToken())}`, {
        method:'POST', headers:{'content-type':'application/json'},
        body: JSON.stringify({user_name, content}),
        signal: ctrl.signal
      });
      if(!resp.ok){ toast('Stream failed', true); return; }

      // Render placeholder
      await refreshMessages();

      const reader = resp.body.getReader();
      const decoder = new TextDecoder();
      let buf = '';
      let assistantId = null;

      let thinkingEl = null;

      function emit(frame){
        const lines = frame.split('\n').filter(Boolean);
        let ev=null, data=null;
        for(const ln of lines){
          if(ln.startsWith('event:')) ev = ln.split(':',2)[1].trim();
          if(ln.startsWith('data:')) data = ln.slice(5).trim();
        }
        if(ev==='thinking' && showThinking){
          if(!thinkingEl){
            thinkingEl = document.createElement('div');
            thinkingEl.className='msg assistant thinking';
            thinkingEl.textContent='Thinking...';
            $msgs.appendChild(thinkingEl); $msgs.scrollTop=$msgs.scrollHeight;
          }
          return;
        }
        if(ev==='message' && data){
          try{
            const obj = JSON.parse(data);
            if(obj.delta){
              if(thinkingEl){ thinkingEl.remove(); thinkingEl = null; }
              if(assistantId==null && obj.id){ assistantId = obj.id; }
              const last = $msgs.querySelector('.msg.assistant:last-of-type .bubble');
              if(last){ last.textContent += obj.delta; $msgs.scrollTop=$msgs.scrollHeight; }
            } else if(obj.id){
              assistantId = obj.id;
              if(thinkingEl){ thinkingEl.remove(); thinkingEl = null; }
              refreshMessages();
            }
          }catch(e){}
        }
      }

      try{
        while(true){
          const {done, value} = await reader.read();
          if(done) break;
          buf += decoder.decode(value, {stream:true});
          let idx;
          while((idx = buf.indexOf('\n\n')) !== -1){
            const frame = buf.slice(0, idx); buf = buf.slice(idx+2);
            emit(frame);
          }
        }
      } catch(e){
        if(e && e.name === 'AbortError'){ aborted = true; }
        else { toast('Stream interrupted', true); }
      }
    } finally {
      state.streamController = null;
      setStreamingActive(false);
    }
    await refreshMessages();
  }

  async function onCopy(m){
    try{
      await navigator.clipboard.writeText(m.content || '');
      toast('Copied');
    }catch(e){
      const ta = document.createElement('textarea');
      ta.value = m.content || '';
      document.body.appendChild(ta);
      ta.select();
      let ok=false; try{ ok=document.execCommand('copy'); }catch(e2){}
      document.body.removeChild(ta);
      toast(ok?'Copied':'Copy failed', !ok);
    }
  }

  async function onEdit(m){
    const content = await inputDialog({title:'Edit message', label:'Content', defaultValue: m.content, multiline:true, placeholder:'Update your message'});
    if(content==null) return;
    const {ok} = await apiFetch(`/api/messages/${m.id}`, {method:'PATCH', json:{content, branch:true}});
    if(!ok){ return; }
    await refreshMessages();
  }

  async function onDelete(m){
    const yes = await confirmDialog('Delete this message? This cannot be undone.', {okText:'Delete', cancelText:'Cancel'});
    if(!yes) return;
    const {ok} = await apiFetch(`/api/messages/${m.id}`, {method:'DELETE'});
    if(!ok){ return; }
    await refreshMessages();
  }

  async function onBranch(m){
    // Create a new user message with parent_id = m.id
    const user_name = $user.value || 'user';
    const content = await inputDialog({title:'Branch here', label:'Your message', placeholder:'Type your message', multiline:true});
    if(!content) return;
    const {ok} = await apiFetch(`/api/threads/${state.threadId}/messages`, {method:'POST', json:{user_name, content, parent_id: m.id}});
    if(!ok){ /* error toast shown */ return; }
    await refreshMessages();
  }

  $send.addEventListener('click', send);
  $input.addEventListener('keydown', (e)=>{ if(e.key==='Enter' && !e.shiftKey){ e.preventDefault(); send(); }});
  $newThread.addEventListener('click', createThread);

  if($stopBtn){
    $stopBtn.addEventListener('click', ()=>{
      if(state.streamController){
        try { state.streamController.abort(); } catch(e){}
        state.streamController = null;
      }
      setStreamingActive(false);
    });
  }

  // Rename thread: double-click title or click ✎ to prompt for new name
  async function promptRename(){
    if(!state.threadId) return;
    const old = $title.textContent || '';
    const val = await inputDialog({title:'Rename thread', label:'Title', defaultValue: old});
    if(val==null) return; // cancelled
    const newTitle = val.trim();
    if(!newTitle || newTitle === old) return;
    const {ok} = await apiFetch(`/api/threads/${state.threadId}`, {method:'PATCH', json:{title: newTitle}});
    if(!ok){ return; }
    $title.textContent = newTitle;
    await listThreads();
  }

  if($title){ $title.addEventListener('dblclick', promptRename); }
  if($renameTitle){ $renameTitle.addEventListener('click', promptRename); }
  if($deleteThreadBtn){
    $deleteThreadBtn.addEventListener('click', async ()=>{
      if(!state.threadId) return;
      const yes = await confirmDialog('Delete this thread and all its messages? This cannot be undone.', {okText:'Delete', cancelText:'Cancel'});
      if(!yes) return;
      const {ok} = await apiFetch(`/api/threads/${state.threadId}`, {method:'DELETE'});
      if(!ok) return;
      state.threadId = null;
      $title.textContent = 'Select or create a thread';
      localStorage.removeItem('lastThreadId');
      await listThreads();
      await refreshMessages();
    });
  }

  $exportBtn.addEventListener('click', async ()=>{
    if(!state.threadId) return;
    const {ok, data} = await apiFetch(`/api/threads/${state.threadId}/export`);
    if(!ok || !data) return;
    const blob = new Blob([JSON.stringify(data,null,2)], {type:'application/json'});
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `thread-${state.threadId}.json`;
    a.click();
  });

  $importFile.addEventListener('change', async ()=>{
    const file = $importFile.files[0]; if(!file) return;
    const text = await file.text();
    let obj; try{ obj = JSON.parse(text); }catch(e){ toast('Invalid JSON', true); return; }
    const {ok, data} = await apiFetch('/api/threads/import', {method:'POST', json: obj});
    if(!ok || !data){ return; }
    await listThreads();
    await selectThread(data.id);
  });

  // Keep UI streaming checkbox in sync with manual toggle
  if($stream){
    $stream.addEventListener('change', ()=>{
      // Local-only toggle between streaming and non-streaming send behavior
      // Reflect in settings dropdown if applicable
      state.streaming = $stream.checked ? 'sse' : state.streaming;
      if($optStreaming && $stream.checked) $optStreaming.value = 'sse';
    });
  }

  // initial
  initSettings();
  listThreads();
})();
