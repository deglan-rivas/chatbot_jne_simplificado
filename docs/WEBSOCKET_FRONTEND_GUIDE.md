# Guía: Conexión Frontend al WebSocket

## 📍 Endpoint WebSocket

```
ws://localhost:8001/api/web/chat/ws
```

O con `user_id` en query params:
```
ws://localhost:8001/api/web/chat/ws?user_id=tu_user_id
```

---

## 🔌 Formas de Conectar

### Opción 1: Con `user_id` en la URL (Recomendado)

```javascript
const userId = "usuario_123"; // O generar UUID
const ws = new WebSocket(`ws://localhost:8001/api/web/chat/ws?user_id=${userId}`);
```

### Opción 2: Enviar `user_id` en el primer mensaje

```javascript
const ws = new WebSocket('ws://localhost:8001/api/web/chat/ws');

ws.onopen = () => {
  // Enviar user_id al conectar
  ws.send(JSON.stringify({
    type: "init",
    user_id: "usuario_123"
  }));
};
```

---

## 📤 Formato de Mensajes que Envía el Frontend

### Enviar mensaje al chatbot:
```javascript
ws.send(JSON.stringify({
  type: "message",
  message: "Hola, quiero información sobre procesos electorales"
}));
```

### Mantener conexión viva (ping):
```javascript
ws.send(JSON.stringify({
  type: "ping"
}));
```

### Cerrar conexión:
```javascript
ws.send(JSON.stringify({
  type: "close"
}));
```

---

## 📥 Formato de Mensajes que Recibe el Frontend

### Mensaje del bot:
```json
{
  "type": "message",
  "content": "Respuesta del bot...",
  "response_rich": {
    "type": "menu",
    "content": {...},
    "actions": [...]
  },
  "state": {...},
  "menu_actual": "main",
  "conversation_active": true,
  "should_finalize": false,
  "timestamp": "2025-01-21T22:25:29.361159"
}
```

### Mensaje del sistema:
```json
{
  "type": "system",
  "content": "Conexión restablecida...",
  "state": {...},
  "conversation_active": true,
  "timestamp": "..."
}
```

### Error:
```json
{
  "type": "error",
  "content": "Mensaje de error...",
  "timestamp": "..."
}
```

### Pong (respuesta a ping):
```json
{
  "type": "pong",
  "timestamp": "..."
}
```

---

## 💻 Ejemplos de Implementación

### 1. JavaScript Vanilla (Básico)

```javascript
class ChatbotWebSocket {
  constructor(userId) {
    this.userId = userId || this.generateUserId();
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  generateUserId() {
    return `web_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  connect() {
    const wsUrl = `ws://localhost:8001/api/web/chat/ws?user_id=${this.userId}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('✅ Conectado al WebSocket');
      this.reconnectAttempts = 0;
      this.onConnected();
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleMessage(data);
    };

    this.ws.onerror = (error) => {
      console.error('❌ Error en WebSocket:', error);
      this.onError(error);
    };

    this.ws.onclose = (event) => {
      console.log('🔌 Conexión cerrada:', event.code, event.reason);
      this.onDisconnected();
      
      // Reconexión automática
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        this.reconnectAttempts++;
        console.log(`🔄 Reintentando conexión (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
        setTimeout(() => this.connect(), 3000);
      }
    };
  }

  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "message",
        message: message
      }));
    } else {
      console.error('WebSocket no está conectado');
    }
  }

  handleMessage(data) {
    switch(data.type) {
      case 'message':
        // Usar response_rich si existe, sino usar content
        if (data.response_rich) {
          this.renderRichMessage(data.response_rich);
        } else {
          this.displayMessage(data.content);
        }
        break;
        
      case 'system':
        this.displaySystemMessage(data.content);
        break;
        
      case 'error':
        this.displayError(data.content);
        break;
        
      case 'pong':
        // Respuesta a ping, conexión viva
        break;
    }
  }

  renderRichMessage(rich) {
    // Implementar renderizado según tipo
    switch(rich.type) {
      case 'menu':
        this.renderMenu(rich);
        break;
      case 'buttons':
        this.renderButtons(rich);
        break;
      case 'list':
        this.renderList(rich);
        break;
      case 'card':
        this.renderCard(rich);
        break;
      case 'text':
        this.displayMessage(rich.content.text);
        break;
    }
  }

  renderMenu(rich) {
    const container = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'bot-message';
    
    // Título
    if (rich.content.title) {
      const title = document.createElement('h3');
      title.textContent = rich.content.title;
      messageDiv.appendChild(title);
    }
    
    // Texto
    if (rich.content.text) {
      const text = document.createElement('p');
      text.textContent = rich.content.text;
      messageDiv.appendChild(text);
    }
    
    // Botones
    const buttonsContainer = document.createElement('div');
    buttonsContainer.className = 'menu-buttons';
    
    rich.actions.forEach(action => {
      const button = document.createElement('button');
      button.textContent = action.label;
      button.className = `btn btn-${action.style || 'primary'}`;
      button.onclick = () => {
        this.sendMessage(action.value);
      };
      buttonsContainer.appendChild(button);
    });
    
    messageDiv.appendChild(buttonsContainer);
    container.appendChild(messageDiv);
  }

  displayMessage(text) {
    const container = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'bot-message';
    messageDiv.textContent = text;
    container.appendChild(messageDiv);
  }

  displaySystemMessage(text) {
    const container = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'system-message';
    messageDiv.textContent = text;
    container.appendChild(messageDiv);
  }

  displayError(text) {
    const container = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = 'error-message';
    messageDiv.textContent = `Error: ${text}`;
    container.appendChild(messageDiv);
  }

  // Callbacks (puedes sobrescribir)
  onConnected() {}
  onDisconnected() {}
  onError(error) {}

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}

// Uso:
const chat = new ChatbotWebSocket();
chat.connect();

// Enviar mensaje
document.getElementById('send-button').onclick = () => {
  const input = document.getElementById('message-input');
  chat.sendMessage(input.value);
  input.value = '';
};
```

---

### 2. React (Hook personalizado)

```jsx
import { useState, useEffect, useRef, useCallback } from 'react';

function useChatbotWebSocket(userId) {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState(null);
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    const wsUrl = `ws://localhost:8001/api/web/chat/ws?user_id=${userId}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      setMessages(prev => [...prev, {
        id: Date.now(),
        type: data.type,
        content: data.content,
        response_rich: data.response_rich,
        state: data.state,
        timestamp: data.timestamp
      }]);
    };

    ws.onerror = (error) => {
      setError('Error de conexión');
      setIsConnected(false);
    };

    ws.onclose = () => {
      setIsConnected(false);
      // Reconexión automática después de 3 segundos
      reconnectTimeoutRef.current = setTimeout(() => {
        connect();
      }, 3000);
    };
  }, [userId]);

  useEffect(() => {
    connect();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: "message",
        message: message
      }));
    }
  }, []);

  return { isConnected, messages, error, sendMessage };
}

// Componente de Chat
function ChatComponent() {
  const userId = useRef(`user_${Date.now()}`).current;
  const { isConnected, messages, error, sendMessage } = useChatbotWebSocket(userId);
  const [input, setInput] = useState('');

  const handleSend = () => {
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="chat-container">
      <div className="chat-status">
        {isConnected ? '🟢 Conectado' : '🔴 Desconectado'}
        {error && <span className="error">{error}</span>}
      </div>
      
      <div className="chat-messages">
        {messages.map(msg => (
          <MessageComponent key={msg.id} message={msg} onButtonClick={sendMessage} />
        ))}
      </div>
      
      <div className="chat-input">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSend()}
          placeholder="Escribe tu mensaje..."
        />
        <button onClick={handleSend} disabled={!isConnected}>
          Enviar
        </button>
      </div>
    </div>
  );
}

// Componente de Mensaje
function MessageComponent({ message, onButtonClick }) {
  if (message.type === 'system') {
    return <div className="system-message">{message.content}</div>;
  }
  
  if (message.type === 'error') {
    return <div className="error-message">{message.content}</div>;
  }

  // Usar response_rich si existe
  if (message.response_rich) {
    const rich = message.response_rich;
    
    switch(rich.type) {
      case 'menu':
        return (
          <div className="bot-message">
            {rich.content.title && <h3>{rich.content.title}</h3>}
            {rich.content.text && <p>{rich.content.text}</p>}
            <div className="menu-buttons">
              {rich.actions.map((action, idx) => (
                <button
                  key={idx}
                  className={`btn btn-${action.style || 'primary'}`}
                  onClick={() => onButtonClick(action.value)}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        );
        
      case 'buttons':
        return (
          <div className="bot-message">
            <p>{rich.content.text}</p>
            <div className="action-buttons">
              {rich.actions.map((action, idx) => (
                <button
                  key={idx}
                  className={`btn btn-${action.style || 'primary'}`}
                  onClick={() => onButtonClick(action.value)}
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        );
        
      case 'list':
        return (
          <div className="bot-message">
            {rich.content.title && <h3>{rich.content.title}</h3>}
            <ul className="list-items">
              {rich.items.map((item, idx) => (
                <li key={idx} onClick={() => onButtonClick(item.value)}>
                  <strong>{item.title}</strong>
                  {item.description && <p>{item.description}</p>}
                </li>
              ))}
            </ul>
          </div>
        );
        
      default:
        return <div className="bot-message">{message.content}</div>;
    }
  }
  
  // Fallback a texto plano
  return <div className="bot-message">{message.content}</div>;
}
```

---

### 3. Vue 3 (Composition API)

```vue
<template>
  <div class="chat-container">
    <div class="chat-status">
      {{ isConnected ? '🟢 Conectado' : '🔴 Desconectado' }}
    </div>
    
    <div class="chat-messages">
      <MessageComponent
        v-for="msg in messages"
        :key="msg.id"
        :message="msg"
        @button-click="sendMessage"
      />
    </div>
    
    <div class="chat-input">
      <input
        v-model="input"
        @keyup.enter="handleSend"
        placeholder="Escribe tu mensaje..."
      />
      <button @click="handleSend" :disabled="!isConnected">
        Enviar
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const userId = ref(`user_${Date.now()}`);
const isConnected = ref(false);
const messages = ref([]);
const input = ref('');
let ws = null;

onMounted(() => {
  connect();
});

onUnmounted(() => {
  if (ws) {
    ws.close();
  }
});

function connect() {
  const wsUrl = `ws://localhost:8001/api/web/chat/ws?user_id=${userId.value}`;
  ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    isConnected.value = true;
  };

  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    messages.value.push({
      id: Date.now(),
      ...data
    });
  };

  ws.onerror = () => {
    isConnected.value = false;
  };

  ws.onclose = () => {
    isConnected.value = false;
    setTimeout(() => connect(), 3000);
  };
}

function sendMessage(message) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: "message",
      message: message
    }));
  }
}

function handleSend() {
  if (input.value.trim()) {
    sendMessage(input.value);
    input.value = '';
  }
}
</script>
```

---

### 4. Angular (Service)

```typescript
// chatbot.service.ts
import { Injectable } from '@angular/core';
import { Observable, Subject } from 'rxjs';

@Injectable({
  providedIn: 'root'
})
export class ChatbotService {
  private ws: WebSocket | null = null;
  private messageSubject = new Subject<any>();
  public messages$ = this.messageSubject.asObservable();
  private userId = `user_${Date.now()}`;

  connect() {
    const wsUrl = `ws://localhost:8001/api/web/chat/ws?user_id=${this.userId}`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      console.log('Conectado');
    };

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.messageSubject.next(data);
    };

    this.ws.onerror = (error) => {
      console.error('Error:', error);
    };

    this.ws.onclose = () => {
      setTimeout(() => this.connect(), 3000);
    };
  }

  sendMessage(message: string) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: "message",
        message: message
      }));
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }
}
```

```typescript
// chat.component.ts
import { Component, OnInit, OnDestroy } from '@angular/core';
import { ChatbotService } from './chatbot.service';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-chat',
  template: `
    <div class="chat-container">
      <div class="messages">
        <div *ngFor="let msg of messages" [ngSwitch]="msg.type">
          <div *ngSwitchCase="'message'" class="bot-message">
            <div *ngIf="msg.response_rich">
              <!-- Renderizar response_rich -->
            </div>
            <div *ngIf="!msg.response_rich">
              {{ msg.content }}
            </div>
          </div>
        </div>
      </div>
      <input [(ngModel)]="input" (keyup.enter)="send()" />
      <button (click)="send()">Enviar</button>
    </div>
  `
})
export class ChatComponent implements OnInit, OnDestroy {
  messages: any[] = [];
  input = '';
  private subscription?: Subscription;

  constructor(private chatbotService: ChatbotService) {}

  ngOnInit() {
    this.chatbotService.connect();
    this.subscription = this.chatbotService.messages$.subscribe(msg => {
      this.messages.push(msg);
    });
  }

  send() {
    if (this.input.trim()) {
      this.chatbotService.sendMessage(this.input);
      this.input = '';
    }
  }

  ngOnDestroy() {
    this.subscription?.unsubscribe();
    this.chatbotService.disconnect();
  }
}
```

---

## 🔧 Configuración para Producción

### Cambiar URL según entorno:

```javascript
const WS_URL = process.env.NODE_ENV === 'production'
  ? 'wss://tu-dominio.com/api/web/chat/ws'
  : 'ws://localhost:8001/api/web/chat/ws';
```

**Nota:** En producción, usa `wss://` (WebSocket Secure) en lugar de `ws://`.

---

## ✅ Checklist de Implementación

- [ ] Generar o usar `user_id` persistente
- [ ] Manejar eventos: `onopen`, `onmessage`, `onerror`, `onclose`
- [ ] Implementar reconexión automática
- [ ] Procesar `response_rich` cuando exista
- [ ] Fallback a `content` si no hay `response_rich`
- [ ] Manejar errores y mensajes del sistema
- [ ] Limpiar conexión al desmontar componente
- [ ] Usar `wss://` en producción

---

## 🐛 Troubleshooting

### Error: "WebSocket connection failed"
- Verifica que el servidor esté corriendo
- Verifica la URL (debe ser `ws://` o `wss://`)
- Verifica CORS si estás en desarrollo

### Error: "user_id required"
- Asegúrate de pasar `user_id` en query params o en el primer mensaje

### La conexión se cierra frecuentemente
- Implementa ping/pong para mantener conexión viva
- Verifica timeout del servidor/proxy

### No recibo `response_rich`
- Verifica que el backend esté generando `response_rich` (solo para `platform="web"`)
- Usa `content` como fallback
