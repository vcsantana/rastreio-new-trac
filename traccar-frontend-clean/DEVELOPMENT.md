# 🚀 Guia de Desenvolvimento - Traccar Frontend Clean

## 📋 Visão Geral

Este documento fornece informações detalhadas para desenvolvedores que desejam contribuir ou modificar o frontend Traccar Clean.

## 🛠️ Setup de Desenvolvimento

### Pré-requisitos
- Node.js 18+ 
- npm ou yarn
- API Python Traccar rodando
- Editor de código (VS Code recomendado)

### Instalação Rápida
```bash
# 1. Navegar para o diretório
cd traccar-frontend-clean

# 2. Instalar dependências
npm install

# 3. Iniciar desenvolvimento
npm run start
```

## 🏗️ Arquitetura

### Estrutura de Pastas
```
src/
├── pages/           # Páginas da aplicação
├── components/      # Componentes reutilizáveis
├── store/          # Redux store e slices
├── utils/          # Funções utilitárias
├── App.jsx         # Componente raiz
└── main.jsx        # Entry point
```

### Fluxo de Dados
```
API Python ←→ Frontend React ←→ Redux Store ←→ Components
```

## 📱 Páginas e Funcionalidades

### 1. Dashboard (`/dashboard`)
- **Propósito**: Página principal com visão geral
- **Componentes**: Cards de estatísticas, links rápidos
- **API Calls**: `/health`, `/api/auth/me`

### 2. Map (`/map`)
- **Propósito**: Visualização de mapas e dispositivos
- **Componentes**: MapView, DeviceList
- **API Calls**: `/api/devices`

### 3. Devices (`/devices`)
- **Propósito**: Gerenciamento de dispositivos
- **Componentes**: Table, Actions, Filters
- **API Calls**: `/api/devices`

### 4. Groups (`/groups`)
- **Propósito**: Gerenciamento de grupos
- **Componentes**: Table, Member counters
- **API Calls**: `/api/groups`

### 5. Geofences (`/geofences`)
- **Propósito**: Gerenciamento de áreas geográficas
- **Componentes**: Table, Upload, Map integration
- **API Calls**: `/api/geofences`

### 6. Events (`/events`)
- **Propósito**: Visualização de eventos
- **Componentes**: Table, Filters, Event types
- **API Calls**: `/api/events`

### 7. Replay (`/replay`)
- **Propósito**: Replay de trajetos históricos
- **Componentes**: Controls, Timeline, Map
- **API Calls**: `/api/positions`

### 8. Commands (`/commands`)
- **Propósito**: Envio de comandos
- **Componentes**: Table, Send buttons
- **API Calls**: `/api/commands`

### 9. Reports (`/reports`)
- **Propósito**: Geração de relatórios
- **Componentes**: Forms, Filters, Export
- **API Calls**: `/api/reports`

### 10. Users (`/users`)
- **Propósito**: Gerenciamento de usuários
- **Componentes**: Table, Roles, Permissions
- **API Calls**: `/api/users`

### 11. Settings (`/settings`)
- **Propósito**: Configurações do sistema
- **Componentes**: Forms, Server info
- **API Calls**: `/health`

## 🔧 Padrões de Desenvolvimento

### Componentes
```jsx
// Estrutura padrão de página
import React, { useState, useEffect } from 'react';
import { Container, Typography, ... } from '@mui/material';
import { useSelector } from 'react-redux';

const PageName = () => {
  const user = useSelector((state) => state.auth.user);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch('/api/endpoint', {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
          const result = await response.json();
          setData(result);
        } else {
          setError('Failed to fetch data');
        }
      } catch (err) {
        setError('Network error');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return <CircularProgress />;
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4">Page Title</Typography>
      {error && <Alert severity="error">{error}</Alert>}
      {/* Page content */}
    </Container>
  );
};

export default PageName;
```

### Estado Global (Redux)
```javascript
// store/authSlice.js
import { createSlice } from '@reduxjs/toolkit';

const initialState = {
  user: null,
  token: null,
  isAuthenticated: false,
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setUser: (state, action) => {
      state.user = action.payload;
      state.isAuthenticated = true;
    },
    clearUser: (state) => {
      state.user = null;
      state.token = null;
      state.isAuthenticated = false;
    },
  },
});

export const { setUser, clearUser } = authSlice.actions;
export default authSlice.reducer;
```

### Requisições API
```javascript
// Padrão para requisições
const fetchData = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/endpoint', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    });

    if (response.ok) {
      return await response.json();
    } else {
      throw new Error('Request failed');
    }
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};
```

## 🎨 Styling e Theming

### Material-UI Theme
```javascript
// Tema personalizado
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#1976d2' },
    secondary: { main: '#dc004e' },
  },
});
```

### Responsive Design
```jsx
// Breakpoints Material-UI
xs: 0px    // Extra small devices
sm: 600px  // Small devices
md: 900px  // Medium devices
lg: 1200px // Large devices
xl: 1536px // Extra large devices
```

## 🔐 Autenticação

### Fluxo de Login
1. Usuário insere credenciais
2. POST para `/api/auth/login`
3. Recebe token JWT
4. Armazena no localStorage
5. Redireciona para dashboard

### Verificação de Token
```javascript
// Verificação automática
useEffect(() => {
  const token = localStorage.getItem('token');
  if (token) {
    // Verificar token com API
    fetch('/api/auth/me', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    .then(response => {
      if (response.ok) {
        return response.json();
      }
      throw new Error('Invalid token');
    })
    .then(userData => {
      dispatch(setUser(userData));
    })
    .catch(() => {
      localStorage.removeItem('token');
      dispatch(clearUser());
    });
  }
}, []);
```

## 🚀 Build e Deploy

### Build de Produção
```bash
npm run build
```

### Estrutura de Build
```
dist/
├── index.html
├── assets/
│   ├── index-[hash].js
│   ├── index-[hash].css
│   └── [other assets]
```

### Configuração de Produção
```javascript
// vite.config.js para produção
export default defineConfig({
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'terser',
  },
  server: {
    proxy: {
      '/api': 'https://api.traccar.com',
    },
  },
});
```

## 🧪 Testing

### Estrutura de Testes (Futuro)
```
src/
├── __tests__/
│   ├── pages/
│   ├── components/
│   └── utils/
├── test-utils/
└── setupTests.js
```

### Comandos de Teste
```bash
# Instalar dependências de teste
npm install --save-dev @testing-library/react @testing-library/jest-dom

# Executar testes
npm test

# Coverage
npm run test:coverage
```

## 🔍 Debugging

### Ferramentas de Debug
- **React DevTools**: Extensão do navegador
- **Redux DevTools**: Extensão do navegador
- **Console**: Logs e erros
- **Network**: Requisições API

### Logs Úteis
```javascript
// Debug de requisições
console.log('API Request:', { url, method, headers });
console.log('API Response:', response);

// Debug de estado
console.log('Redux State:', store.getState());
console.log('Component State:', state);
```

## 📦 Dependências

### Principais
- **react**: ^19.1.1
- **@mui/material**: ^7.3.1
- **@reduxjs/toolkit**: ^2.8.2
- **react-router-dom**: ^7.8.1

### Desenvolvimento
- **vite**: ^7.1.3
- **@vitejs/plugin-react**: ^5.0.1
- **eslint**: ^9.33.0

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. API não conecta
```bash
# Verificar se API está rodando
curl http://localhost:8000/health

# Verificar proxy no vite.config.js
```

#### 2. Login falha
```javascript
// Verificar credenciais
console.log('Login attempt:', { email, password });

// Verificar resposta da API
console.log('Login response:', response);
```

#### 3. Páginas não carregam
```javascript
// Verificar roteamento
console.log('Current route:', window.location.pathname);

// Verificar autenticação
console.log('User authenticated:', user);
```

#### 4. Build falha
```bash
# Limpar cache
rm -rf node_modules package-lock.json
npm install

# Verificar dependências
npm audit
```

## 📚 Recursos Adicionais

### Documentação
- [React 19 Docs](https://react.dev/)
- [Material-UI Docs](https://mui.com/)
- [Redux Toolkit Docs](https://redux-toolkit.js.org/)
- [Vite Docs](https://vitejs.dev/)

### Ferramentas
- [VS Code Extensions](https://code.visualstudio.com/)
- [React DevTools](https://react.dev/learn/react-developer-tools)
- [Redux DevTools](https://github.com/reduxjs/redux-devtools)

---

**🎯 Desenvolvimento eficiente e organizado para o Traccar Frontend Clean!**

