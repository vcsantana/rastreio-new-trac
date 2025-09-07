# Traccar Frontend Clean

## 🎯 Visão Geral

Frontend moderno e limpo para o sistema Traccar GPS Tracking, construído com React 19, TypeScript, Material-UI v7 e conectado à API Python FastAPI. Este frontend oferece uma interface responsiva e intuitiva para gerenciamento completo de dispositivos GPS, mapas, eventos e relatórios.

## 🚀 Características Principais

- ✅ **React 19** com TypeScript
- ✅ **Material-UI v7** para interface moderna
- ✅ **Redux Toolkit** para gerenciamento de estado
- ✅ **React Router v7** para navegação
- ✅ **Design Responsivo** (mobile-first)
- ✅ **Autenticação JWT** integrada
- ✅ **Conexão com API Python** FastAPI
- ✅ **11 Páginas Completas** de funcionalidades
- ✅ **Interface Intuitiva** com menu lateral

## 📁 Estrutura do Projeto

```
traccar-frontend-clean/
├── public/                 # Arquivos estáticos
│   └── favicon.ico
├── src/
│   ├── components/         # Componentes reutilizáveis
│   ├── pages/             # Páginas da aplicação
│   │   ├── LoginPage.jsx
│   │   ├── DashboardPage.jsx
│   │   ├── DevicesPage.jsx
│   │   ├── MapPage.jsx
│   │   ├── EventsPage.jsx
│   │   ├── ReportsPage.jsx
│   │   ├── UsersPage.jsx
│   │   ├── SettingsPage.jsx
│   │   ├── GeofencesPage.jsx
│   │   ├── ReplayPage.jsx
│   │   ├── CommandsPage.jsx
│   │   └── GroupsPage.jsx
│   ├── store/             # Redux store
│   │   ├── index.js
│   │   └── authSlice.js
│   ├── utils/             # Utilitários
│   ├── App.jsx            # Componente principal
│   └── main.jsx           # Ponto de entrada
├── package.json           # Dependências
├── vite.config.js         # Configuração Vite
└── index.html             # HTML principal
```

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Versão | Propósito |
|------------|--------|-----------|
| **React** | 19.1.1 | Framework UI |
| **TypeScript** | 5.7+ | Tipagem estática |
| **Material-UI** | 7.3.1 | Componentes UI |
| **Redux Toolkit** | 2.8.2 | Gerenciamento de estado |
| **React Router** | 7.8.1 | Roteamento |
| **Vite** | 7.1.3 | Build tool |
| **ESLint** | 9.33.0 | Linting |

## 📋 Páginas Implementadas

### 🏠 Dashboard
- **URL**: `/dashboard`
- **Funcionalidades**:
  - Informações do usuário logado
  - Status do servidor em tempo real
  - Links rápidos para outras páginas
  - Estatísticas do sistema

### 🗺️ Map
- **URL**: `/map`
- **Funcionalidades**:
  - Visualização de mapas interativos
  - Lista de dispositivos
  - Preparado para MapLibre GL, Google Maps, OpenStreetMap
  - Interface responsiva

### 📱 Devices
- **URL**: `/devices`
- **Funcionalidades**:
  - Lista completa de dispositivos
  - Status em tempo real
  - Ações de gerenciamento
  - Filtros e busca

### 👥 Groups
- **URL**: `/groups`
- **Funcionalidades**:
  - Gerenciamento de grupos
  - Associação de dispositivos e usuários
  - Contadores de membros
  - Ações CRUD

### 🚧 Geofences
- **URL**: `/geofences`
- **Funcionalidades**:
  - Lista de geofences
  - Upload de arquivos GPX
  - Gerenciamento de áreas
  - Visualização no mapa

### 📊 Events
- **URL**: `/events`
- **Funcionalidades**:
  - Lista de eventos em tempo real
  - Filtros por dispositivo e tipo
  - Chips coloridos por tipo de evento
  - Histórico completo

### ▶️ Replay
- **URL**: `/replay`
- **Funcionalidades**:
  - Replay de trajetos históricos
  - Controles de reprodução (play/pause/forward/rewind)
  - Download de dados KML
  - Visualização de posições detalhadas

### ⚡ Commands
- **URL**: `/commands`
- **Funcionalidades**:
  - Lista de comandos salvos
  - Envio de comandos para dispositivos
  - Gerenciamento de tipos de comando
  - Histórico de comandos

### 📈 Reports
- **URL**: `/reports`
- **Funcionalidades**:
  - Gerador de relatórios
  - Filtros por data e dispositivo
  - Relatórios rápidos (diário, semanal, mensal)
  - Exportação de dados

### 👤 Users
- **URL**: `/users`
- **Funcionalidades**:
  - Gerenciamento de usuários
  - Roles e permissões
  - Status de usuários
  - Ações de edição e exclusão

### ⚙️ Settings
- **URL**: `/settings`
- **Funcionalidades**:
  - Preferências do usuário
  - Informações do servidor
  - Links para documentação da API
  - Configurações de notificações

## 🔧 Configuração e Instalação

### Pré-requisitos
- Node.js 18+
- npm ou yarn
- API Python Traccar rodando em `http://localhost:8000`

### Instalação

1. **Clone ou navegue para o diretório**:
```bash
cd traccar-frontend-clean
```

2. **Instale as dependências**:
```bash
npm install
```

3. **Configure a API**:
   - Certifique-se de que a API Python está rodando em `http://localhost:8000`
   - O proxy está configurado no `vite.config.js`

4. **Inicie o servidor de desenvolvimento**:
```bash
npm run start
```

5. **Acesse a aplicação**:
   - Frontend: http://localhost:3002 (ou porta disponível)
   - API: http://localhost:8000
   - Documentação da API: http://localhost:8000/docs

## 🚀 Scripts Disponíveis

```bash
# Desenvolvimento
npm run start          # Inicia servidor de desenvolvimento
npm run dev            # Alias para start

# Produção
npm run build          # Build para produção
```

## 🔗 Conexão com API

### Configuração do Proxy
O frontend está configurado para se conectar com a API Python através de proxy:

```javascript
// vite.config.js
export default defineConfig({
  server: {
    port: 3002,
    proxy: {
      '/api': 'http://localhost:8000',
      '/health': 'http://localhost:8000',
    },
  },
});
```

### Endpoints Utilizados
- `/api/auth/login` - Autenticação
- `/api/auth/me` - Informações do usuário
- `/api/devices` - Dispositivos
- `/api/events` - Eventos
- `/api/geofences` - Geofences
- `/api/commands` - Comandos
- `/api/groups` - Grupos
- `/api/users` - Usuários
- `/api/positions` - Posições
- `/health` - Status do servidor

## 🎨 Interface e Design

### Tema
- **Material-UI v7** com tema personalizado
- **Cores primárias**: Azul (#1976d2)
- **Cores secundárias**: Rosa (#dc004e)
- **Modo**: Claro (preparado para escuro)

### Responsividade
- **Mobile-first** design
- **Breakpoints**: xs, sm, md, lg, xl
- **Menu lateral** responsivo
- **Componentes adaptativos**

### Navegação
- **Menu lateral** com drawer
- **Menu hambúrguer** em dispositivos móveis
- **Roteamento** com React Router
- **Breadcrumbs** em páginas específicas

## 🔐 Autenticação

### Sistema JWT
- **Login** com email e senha
- **Token JWT** armazenado no localStorage
- **Verificação automática** de token
- **Redirecionamento** para login se não autenticado

### Fluxo de Autenticação
1. Usuário faz login
2. Token JWT é armazenado
3. Requisições incluem token no header
4. Verificação automática de validade
5. Logout limpa token e redireciona

## 📱 Funcionalidades Mobile

- ✅ **Design responsivo** completo
- ✅ **Menu lateral** adaptativo
- ✅ **Touch-friendly** interface
- ✅ **Otimizado** para dispositivos móveis
- ✅ **PWA ready** (estrutura preparada)

## 🔧 Desenvolvimento

### Estrutura de Componentes
```jsx
// Exemplo de página
import React, { useState, useEffect } from 'react';
import { Container, Typography, ... } from '@mui/material';
import { useSelector } from 'react-redux';

const ExamplePage = () => {
  const user = useSelector((state) => state.auth.user);
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch data from API
  }, []);

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4">Page Title</Typography>
      {/* Page content */}
    </Container>
  );
};

export default ExamplePage;
```

### Padrões Utilizados
- **Functional Components** com hooks
- **Material-UI** para componentes
- **Redux** para estado global
- **Async/await** para requisições
- **Error boundaries** para tratamento de erros

## 🚀 Deploy

### Build para Produção
```bash
npm run build
```

### Arquivos de Build
- **Dist**: `dist/` (arquivos otimizados)
- **Assets**: CSS, JS, imagens otimizadas
- **Index**: `index.html` principal

### Configuração de Produção
- Atualizar URLs da API no `vite.config.js`
- Configurar proxy para produção
- Definir variáveis de ambiente

## 📊 Status do Projeto

### ✅ Implementado
- [x] Estrutura base do projeto
- [x] Sistema de autenticação
- [x] 11 páginas completas
- [x] Navegação e roteamento
- [x] Conexão com API Python
- [x] Design responsivo
- [x] Tratamento de erros
- [x] Loading states

### 🔄 Em Desenvolvimento
- [ ] Integração com mapas (MapLibre GL)
- [ ] WebSocket para tempo real
- [ ] PWA manifest
- [ ] Testes automatizados
- [ ] Internacionalização

### 📋 Próximos Passos
- [ ] Integração completa com mapas
- [ ] Sistema de notificações
- [ ] Relatórios avançados
- [ ] Exportação de dados
- [ ] Temas escuro/claro

## 🤝 Contribuição

### Como Contribuir
1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

### Padrões de Código
- **ESLint** configurado
- **Prettier** para formatação
- **Conventional Commits**
- **Componentes funcionais**
- **Hooks** do React

## 📞 Suporte

### Documentação
- **API**: http://localhost:8000/docs
- **Redoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Problemas Comuns
1. **API não conecta**: Verificar se está rodando na porta 8000
2. **Login falha**: Verificar credenciais na API
3. **Páginas não carregam**: Verificar console do navegador
4. **Build falha**: Verificar dependências

## 📄 Licença

Este projeto mantém compatibilidade com a licença original do Traccar (Apache 2.0).

---

**🎉 Frontend Traccar Clean - Moderno, Responsivo e Completo!**

**Desenvolvido com ❤️ usando React 19, Material-UI e FastAPI**
