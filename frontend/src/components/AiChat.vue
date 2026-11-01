<template>
  <div class="ai-chat-root">
    <!-- 悬浮球入口 -->
    <button v-if="!open" class="ai-fab" title="AI 智能助手" @click="open = true">
      <svg viewBox="0 0 24 24" width="26" height="26" fill="none" stroke="#4dd8ff" stroke-width="1.8">
        <path d="M12 2a7 7 0 0 1 7 7v3a7 7 0 0 1-7 7H8l-3 3v-4.5A7 7 0 0 1 5 9V9a7 7 0 0 1 7-7z" stroke-linejoin="round"/>
        <circle cx="9" cy="10.5" r="1.1" fill="#4dd8ff" stroke="none"/>
        <circle cx="15" cy="10.5" r="1.1" fill="#4dd8ff" stroke="none"/>
        <path d="M9 14c.9.8 2 1.2 3 1.2s2.1-.4 3-1.2" stroke-linecap="round"/>
      </svg>
      <span class="ai-fab-label">AI</span>
    </button>

    <!-- 聊天卡片 -->
    <transition name="ai-slide">
      <div v-if="open" class="ai-panel">
        <div class="ai-header">
          <div class="ai-header-title">
            <span class="ai-dot"></span>
            AI 智能助手
          </div>
          <div class="ai-header-actions">
            <button class="ai-icon-btn" title="清空对话" @click="clearChat">清空</button>
            <button class="ai-icon-btn" title="收起" @click="open = false">—</button>
          </div>
        </div>

        <div ref="msgList" class="ai-messages">
          <div v-if="messages.length === 0" class="ai-welcome">
            <p>你好，我是链家租房数据分析系统的 AI 助手 👋</p>
            <p>我可以基于系统的真实分析数据回答，试试：</p>
            <div class="ai-suggestions">
              <button v-for="(q, i) in suggestions" :key="i" @click="ask(q)">{{ q }}</button>
            </div>
          </div>

          <div v-for="(m, i) in messages" :key="i"
               class="ai-msg" :class="m.role === 'user' ? 'is-user' : 'is-bot'">
            <div v-if="m.role !== 'user'" class="ai-avatar">AI</div>
            <div class="ai-bubble">
              <div v-if="m.tools && m.tools.length" class="ai-tools">
                已查询：{{ m.tools.join('、') }}
              </div>
              <div class="ai-text" v-html="renderMarkdown(m.content)"></div>
            </div>
            <div v-if="m.role === 'user'" class="ai-avatar is-me">我</div>
          </div>

          <div v-if="loading" class="ai-msg is-bot">
            <div class="ai-avatar">AI</div>
            <div class="ai-bubble"><span class="ai-typing"><i></i><i></i><i></i></span></div>
          </div>
        </div>

        <div class="ai-input-row">
          <input
            v-model="input"
            class="ai-input"
            type="text"
            placeholder="例如：合肥2000元以内两室的房子"
            :disabled="loading"
            @keydown.enter="send"
          />
          <button class="ai-send" :disabled="loading || !input.trim()" @click="send">发送</button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
const API_BASE = 'http://127.0.0.1:8000';

export default {
  name: 'AiChat',
  data() {
    return {
      open: false,
      input: '',
      loading: false,
      messages: [],
      suggestions: [
        '租得最贵的前5个城市是哪些？',
        '合肥2000元以内有什么两室的房子？',
        '热门小区排行 TOP10',
        '整租和合租占比是多少？',
      ],
    };
  },
  methods: {
    clearChat() {
      this.messages = [];
    },
    renderMarkdown(text) {
      let html = (text || '')
        .replace(/&/g, '&').replace(/</g, '<').replace(/>/g, '>');
      // 简易 markdown：链接 + 加粗 + 换行（不引第三方库，保持依赖干净）
      // [文字](url) → 可点击链接
      html = html.replace(
        /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g,
        '<a href="$2" target="_blank" rel="noopener">$1</a>'
      );
      // 裸链接也转成可点击
      html = html.replace(
        /(^|[^"'>])((https?:\/\/)[^\s<]+)/g,
        '$1<a href="$2" target="_blank" rel="noopener">$2</a>'
      );
      html = html.replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>');
      return html.replace(/\n/g, '<br/>');
    },
    async ask(q) {
      if (this.loading) return;
      this.input = q;
      await this.send();
    },
    async send() {
      const text = this.input.trim();
      if (!text || this.loading) return;
      this.input = '';
      this.messages.push({ role: 'user', content: text });
      this.loading = true;
      this.scrollBottom();

      // 只带最近 6 轮上下文
      const history = this.messages
        .filter(m => m.role === 'user' || (m.role === 'assistant' && m.name !== 'error'))
        .slice(-7, -1)
        .map(m => ({ role: m.role, content: m.content }));

      try {
        const token = localStorage.getItem('token');
        const resp = await fetch(`${API_BASE}/ai/chat/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...(token ? { Authorization: `Token ${token}` } : {}),
          },
          body: JSON.stringify({ message: text, history }),
        });
        const data = await resp.json();
        if (!resp.ok && (resp.status === 401)) {
          // 与 request.js 401 行为一致：清理登录态并跳转登录页
          localStorage.removeItem('token');
          localStorage.removeItem('user_id');
          localStorage.removeItem('username');
          window.location.href = '/login';
        } else if (data.error) {
          this.messages.push({ role: 'assistant', name: 'error', content: data.error });
        } else {
          this.messages.push({ role: 'assistant', content: data.data.reply, tools: data.data.used_tools });
        }
      } catch (e) {
        this.messages.push({ role: 'assistant', name: 'error', content: 'AI 服务暂时不可用，请确认后端已启动。' });
      } finally {
        this.loading = false;
        this.scrollBottom();
      }
    },
    scrollBottom() {
      this.$nextTick(() => {
        const el = this.$refs.msgList;
        if (el) el.scrollTop = el.scrollHeight;
      });
    },
  },
};
</script>

<style scoped>
.ai-chat-root {
  position: fixed;
  right: 22px;
  bottom: 26px;
  z-index: 9999;
  font-family: 'Microsoft YaHei', sans-serif;
}

/* ============ 悬浮球 ============ */
.ai-fab {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: 1px solid rgba(77, 216, 255, 0.5);
  background: radial-gradient(circle at 30% 30%, rgba(10, 40, 70, 0.95), rgba(4, 16, 34, 0.98));
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1px;
  box-shadow: 0 0 18px rgba(77, 216, 255, 0.35);
  transition: transform 0.2s, box-shadow 0.2s;
}
.ai-fab:hover {
  transform: scale(1.08);
  box-shadow: 0 0 26px rgba(77, 216, 255, 0.6);
}
.ai-fab-label {
  font-size: 10px;
  color: #4dd8ff;
  letter-spacing: 1px;
}

/* ============ 聊天面板 ============ */
.ai-panel {
  width: 400px;
  height: 560px;
  max-width: calc(100vw - 40px);
  max-height: calc(100vh - 60px);
  margin-bottom: 0;
  border-radius: 12px;
  border: 1px solid rgba(77, 216, 255, 0.35);
  background: rgba(6, 20, 40, 0.97);
  box-shadow: 0 8px 40px rgba(0, 20, 45, 0.75), 0 0 1px rgba(77, 216, 255, 0.4);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  color: #d6eaff;
}

.ai-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid rgba(77, 216, 255, 0.2);
  background: linear-gradient(90deg, rgba(10, 40, 80, 0.6), transparent);
  flex: none;
}
.ai-header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  letter-spacing: 1px;
}
.ai-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #35e08a;
  box-shadow: 0 0 8px #35e08a;
}
.ai-header-actions { display: flex; gap: 6px; }
.ai-icon-btn {
  background: transparent;
  border: 1px solid rgba(77, 216, 255, 0.25);
  color: #8fc7ee;
  border-radius: 6px;
  font-size: 12px;
  padding: 2px 10px;
  cursor: pointer;
}
.ai-icon-btn:hover { color: #4dd8ff; border-color: rgba(77, 216, 255, 0.6); }

/* ============ 消息列表 ============ */
.ai-messages {
  flex: 1;
  overflow-y: auto;
  padding: 14px 12px;
  scroll-behavior: smooth;
}
.ai-messages::-webkit-scrollbar { width: 6px; }
.ai-messages::-webkit-scrollbar-thumb { background: rgba(77, 216, 255, 0.25); border-radius: 3px; }

.ai-welcome { font-size: 13px; color: #9fc4e0; line-height: 1.8; }
.ai-suggestions { display: flex; flex-direction: column; gap: 8px; margin-top: 6px; align-items: flex-start; }
.ai-suggestions button {
  background: rgba(20, 60, 110, 0.45);
  border: 1px solid rgba(77, 216, 255, 0.3);
  color: #bfe3ff;
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.ai-suggestions button:hover { background: rgba(40, 100, 170, 0.6); color: #fff; }

.ai-msg {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 12px;
}
.ai-msg.is-user { justify-content: flex-start; flex-direction: row-reverse; }
.ai-avatar {
  flex: none;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: linear-gradient(135deg, #1a5a9e, #0a2e5c);
  border: 1px solid rgba(77, 216, 255, 0.45);
  color: #4dd8ff;
  font-size: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ai-avatar.is-me { background: rgba(60, 90, 130, 0.6); color: #a9cef0; border-color: rgba(160, 200, 240, 0.4); }

.ai-bubble {
  max-width: 78%;
  padding: 8px 12px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.7;
  word-break: break-word;
}
.is-user .ai-bubble {
  background: rgba(40, 110, 190, 0.35);
  border: 1px solid rgba(110, 190, 255, 0.3);
  border-top-right-radius: 2px;
}
.is-bot .ai-bubble {
  background: rgba(16, 42, 76, 0.65);
  border: 1px solid rgba(77, 216, 255, 0.2);
  border-top-left-radius: 2px;
}
.is-bot .ai-bubble :deep(b) { color: #7fe3ff; }
.is-bot .ai-bubble :deep(a) { color: #4dd8ff; text-decoration: underline; word-break: break-all; }

.ai-tools {
  font-size: 11px;
  color: #7fb9e0;
  margin-bottom: 4px;
  padding-bottom: 4px;
  border-bottom: 1px dashed rgba(127, 185, 224, 0.25);
}

/* ============ 输入区 ============ */
.ai-input-row {
  flex: none;
  display: flex;
  gap: 8px;
  padding: 10px 12px;
  border-top: 1px solid rgba(77, 216, 255, 0.2);
  background: rgba(8, 26, 52, 0.8);
}
.ai-input {
  flex: 1;
  background: rgba(4, 14, 30, 0.9);
  border: 1px solid rgba(77, 216, 255, 0.25);
  border-radius: 8px;
  color: #d6eaff;
  font-size: 13px;
  padding: 8px 12px;
  outline: none;
}
.ai-input::placeholder { color: #5b83a8; }
.ai-input:focus { border-color: rgba(77, 216, 255, 0.6); }
.ai-send {
  background: linear-gradient(135deg, #1e6fc0, #14508a);
  border: none;
  color: #fff;
  border-radius: 8px;
  font-size: 13px;
  padding: 0 16px;
  cursor: pointer;
  transition: opacity 0.2s;
}
.ai-send:disabled { opacity: 0.4; cursor: not-allowed; }

/* ============ 打字动画 ============ */
.ai-typing { display: inline-flex; gap: 5px; padding: 4px 0; }
.ai-typing i {
  width: 6px; height: 6px; border-radius: 50%;
  background: #4dd8ff;
  animation: aiBlink 1.2s infinite;
}
.ai-typing i:nth-child(2) { animation-delay: 0.2s; }
.ai-typing i:nth-child(3) { animation-delay: 0.4s; }
@keyframes aiBlink { 0%, 60%, 100% { opacity: 0.25; } 30% { opacity: 1; } }

/* ============ 弹出动画 ============ */
.ai-slide-enter-active, .ai-slide-leave-active { transition: all 0.25s ease; }
.ai-slide-enter-from, .ai-slide-leave-to { opacity: 0; transform: translateY(18px) scale(0.95); }
</style>
