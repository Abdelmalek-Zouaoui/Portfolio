(() => {
  const dataEl = document.getElementById('portfolio-data');
  const terminal = document.getElementById('hero-terminal');
  const output = document.getElementById('term-output');
  const inputLine = document.getElementById('term-input-line');
  const input = document.getElementById('term-input');
  if (!dataEl || !terminal || !output || !input) return;

  let DATA = {};
  try {
    DATA = JSON.parse(dataEl.textContent);
  } catch {
    DATA = {};
  }

  const history = [];
  let historyIndex = -1;

  function scrollToBottom() {
    terminal.scrollTop = terminal.scrollHeight;
  }

  function appendLine(text, className) {
    const line = document.createElement('div');
    line.className = 'term-line term-output-line' + (className ? ' ' + className : '');
    line.textContent = text;
    output.appendChild(line);
    return line;
  }

  function appendLinkLine(prefix, label, href) {
    const line = document.createElement('div');
    line.className = 'term-line term-output-line term-dim';
    const prefixSpan = document.createElement('span');
    prefixSpan.textContent = prefix;
    const link = document.createElement('a');
    link.href = href;
    link.textContent = label;
    link.target = '_blank';
    link.rel = 'noopener';
    link.style.color = '#64b5f6';
    line.appendChild(prefixSpan);
    line.appendChild(link);
    output.appendChild(line);
    return line;
  }

  function echo(cmd) {
    const line = document.createElement('div');
    line.className = 'term-line term-output-line';
    const prompt = document.createElement('span');
    prompt.className = 'term-prompt';
    prompt.textContent = '❯ ';
    const text = document.createElement('span');
    text.className = 'term-output-echo';
    text.textContent = cmd;
    line.appendChild(prompt);
    line.appendChild(text);
    output.appendChild(line);
  }

  const COMMANDS = {
    help() {
      appendLine('Available commands:');
      appendLine('  whoami       — who I am');
      appendLine('  about        — short bio');
      appendLine('  experience   — work history');
      appendLine('  education    — academic background');
      appendLine('  skills       — technical skills');
      appendLine('  projects     — list projects (try: open <n>)');
      appendLine('  contact      — how to reach me');
      appendLine('  resume       — open my résumé');
      appendLine('  clear        — clear the terminal');
    },

    whoami() {
      const name = DATA.name || 'anonymous';
      const eyebrow = DATA.eyebrow ? ` — ${DATA.eyebrow}` : '';
      appendLine(`${name}${eyebrow}`);
    },

    about() {
      const text = (DATA.about || '').trim();
      if (!text) {
        appendLine('No bio added yet.', 'term-dim');
        return;
      }
      const excerpt = text.length > 280 ? text.slice(0, 280).trim() + '…' : text;
      excerpt.split('\n').forEach((para) => {
        if (para.trim()) appendLine(para.trim());
      });
    },

    experience() {
      const items = DATA.experience || [];
      if (!items.length) {
        appendLine('No experience entries yet.', 'term-dim');
        return;
      }
      items.forEach((e) => {
        const period = e.period ? ` (${e.period})` : '';
        appendLine(`• ${e.role} @ ${e.org}${period}`);
      });
    },

    education() {
      const items = DATA.education || [];
      if (!items.length) {
        appendLine('No education entries yet.', 'term-dim');
        return;
      }
      items.forEach((e) => {
        const period = e.period ? ` (${e.period})` : '';
        appendLine(`• ${e.degree} @ ${e.institution}${period}`);
      });
    },

    skills() {
      const categories = Object.keys(DATA.skills || {});
      if (!categories.length) {
        appendLine('No skills added yet.', 'term-dim');
        return;
      }
      categories.forEach((cat) => {
        appendLine(`${cat}: ${DATA.skills[cat].join(', ')}`);
      });
    },

    projects() {
      const items = DATA.projects || [];
      if (!items.length) {
        appendLine('No projects added yet.', 'term-dim');
        return;
      }
      items.forEach((p, i) => appendLine(`${i + 1}. ${p.title}`));
      appendLine("type 'open <n>' to view one, e.g. open 1", 'term-dim');
    },

    open(arg) {
      const items = DATA.projects || [];
      const n = parseInt(arg, 10);
      if (!n || !items[n - 1]) {
        appendLine(`open: no project #${arg || '?'} — try 'projects' to list them`, 'term-output-error');
        return;
      }
      const project = items[n - 1];
      appendLine(`→ opening "${project.title}"…`, 'term-dim');
      setTimeout(() => {
        window.location.href = `/projects/${project.id}`;
      }, 500);
    },

    contact() {
      let any = false;
      if (DATA.email) {
        appendLinkLine('email:    ', DATA.email, `mailto:${DATA.email}`);
        any = true;
      }
      if (DATA.github) {
        appendLinkLine('github:   ', DATA.github.replace(/^https?:\/\//, ''), DATA.github);
        any = true;
      }
      if (DATA.linkedin) {
        appendLinkLine('linkedin: ', DATA.linkedin.replace(/^https?:\/\//, ''), DATA.linkedin);
        any = true;
      }
      if (!any) appendLine('No contact info added yet.', 'term-dim');
    },

    resume() {
      if (!DATA.resume) {
        appendLine('No résumé uploaded yet.', 'term-dim');
        return;
      }
      appendLine('→ opening résumé…', 'term-dim');
      window.open(DATA.resume, '_blank', 'noopener');
    },

    clear() {
      output.innerHTML = '';
    },
  };

  function run(raw) {
    const trimmed = raw.trim();
    if (!trimmed) return;

    echo(trimmed);
    history.push(trimmed);
    historyIndex = history.length;

    const [cmdRaw, ...rest] = trimmed.split(/\s+/);
    const cmd = cmdRaw.toLowerCase();

    if (cmd === 'sudo') {
      appendLine('Permission denied: you are not root here 😄', 'term-output-error');
    } else if (cmd in COMMANDS) {
      COMMANDS[cmd](rest.join(' '));
    } else {
      appendLine(`command not found: ${cmd} — type 'help' for a list of commands`, 'term-output-error');
    }
    scrollToBottom();
  }

  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
      run(input.value);
      input.value = '';
    } else if (e.key === 'ArrowUp') {
      if (historyIndex > 0) {
        historyIndex -= 1;
        input.value = history[historyIndex];
      }
      e.preventDefault();
    } else if (e.key === 'ArrowDown') {
      if (historyIndex < history.length - 1) {
        historyIndex += 1;
        input.value = history[historyIndex];
      } else {
        historyIndex = history.length;
        input.value = '';
      }
      e.preventDefault();
    }
  });

  terminal.addEventListener('click', () => input.focus());

  const revealDelay = 4700;
  setTimeout(() => {
    input.disabled = false;
  }, revealDelay);
})();
