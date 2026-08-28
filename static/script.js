const form = document.querySelector('#chatForm');
const input = document.querySelector('#messageInput');
const sendButton = document.querySelector('#sendButton');
const messages = document.querySelector('#chatMessages');
const typing = document.querySelector('#typing');
const statusMessage = document.querySelector('#statusMessage');
const moodEmoji = document.querySelector('#moodEmoji');
const moodText = document.querySelector('#moodText');
const moodBadge = document.querySelector('#moodBadge');
const pipCharacter = document.querySelector('#pipCharacter');
const pipCaption = document.querySelector('#pipCaption');

const history = [];
const MAX_HISTORY = 16;
const moods = {
  happy: ['😊', 'Happy', 'Pip is happy with you ✨'],
  supportive: ['💗', 'Supportive', 'Pip is here for you 💗'],
  calm: ['🌿', 'Calm', "Let's take it easy 🌿"],
  curious: ['🤔', 'Curious', 'Tell me more 🤔'],
  playful: ['😜', 'Playful', "Let's have some fun 😜"],
  surprised: ['😮', 'Surprised', 'Wow! 😮'],
  serious: ['🧠', 'Serious', "I'm listening carefully."],
  friendly: ['✨', 'Friendly', "Let's chat ✨"],
};
const moodNames = Object.keys(moods);

function timeNow() {
  return new Intl.DateTimeFormat([], { hour: '2-digit', minute: '2-digit' }).format(new Date());
}

function addMessage(role, content) {
  const row = document.createElement('div');
  row.className = `message ${role === 'user' ? 'user-message' : 'friend-message'}`;

  if (role === 'assistant') {
    const avatar = document.createElement('div');
    avatar.className = 'mini-avatar';
    avatar.setAttribute('aria-hidden', 'true');
    avatar.textContent = 'P';
    row.appendChild(avatar);
  }

  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  const name = document.createElement('span');
  name.className = 'message-name';
  name.textContent = role === 'user' ? 'YOU' : 'A2 FRIEND';
  const text = document.createElement('p');
  text.textContent = content;
  const time = document.createElement('time');
  time.textContent = timeNow();
  bubble.append(name, text, time);
  row.appendChild(bubble);
  messages.appendChild(row);
  messages.scrollTo({ top: messages.scrollHeight, behavior: 'smooth' });
}

function updateMood(mood) {
  const normalized = Object.hasOwn(moods, mood) ? mood : 'friendly';
  const [emoji, label, caption] = moods[normalized];
  moodEmoji.textContent = emoji;
  moodText.textContent = label;
  pipCaption.textContent = caption;
  pipCharacter.classList.remove(...moodNames);
  pipCharacter.classList.add(normalized);
  moodBadge.dataset.mood = normalized;
  moodBadge.classList.remove('mood-pop');
  requestAnimationFrame(() => moodBadge.classList.add('mood-pop'));
}

function setLoading(isLoading) {
  input.disabled = isLoading;
  sendButton.disabled = isLoading;
  typing.hidden = !isLoading;
  if (isLoading) messages.scrollTop = messages.scrollHeight;
}

function resizeInput() {
  input.style.height = 'auto';
  input.style.height = `${Math.min(input.scrollHeight, 110)}px`;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message || sendButton.disabled) return;

  statusMessage.textContent = '';
  addMessage('user', message);
  input.value = '';
  resizeInput();
  setLoading(true);

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history: history.slice(-MAX_HISTORY) }),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || 'A2 Friend cannot answer right now. Please try again.');

    history.push({ role: 'user', content: message }, { role: 'assistant', content: data.answer });
    if (history.length > MAX_HISTORY) history.splice(0, history.length - MAX_HISTORY);
    addMessage('assistant', data.answer);
    updateMood(data.mood);
  } catch (error) {
    statusMessage.textContent = error.message;
  } finally {
    setLoading(false);
    input.focus();
  }
});

input.addEventListener('input', resizeInput);
input.addEventListener('keydown', (event) => {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});
