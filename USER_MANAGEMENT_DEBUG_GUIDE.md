# User Management Debug Guide

## Problemas Reportados
1. **Edição de usuários não funciona**
2. **Não consegue ver onde gerenciar permissões**

## Como Testar e Debuggar

### 1. Acesse a Página de Usuários
- URL: `http://localhost:3000/users`
- Login: `admin@traccar.com` / `admin123`

### 2. Abra o Console do Navegador
- **Chrome/Edge**: F12 → Console
- **Firefox**: F12 → Console
- **Safari**: Cmd+Option+I → Console

### 3. Teste a Edição de Usuários

#### Passo 1: Clique no Menu de Ações
1. Na tabela de usuários, clique no botão "⋮" (três pontos) de qualquer usuário
2. **Verifique no console**: Deve aparecer:
   ```
   handleMenuClick called with user: {id: X, name: "...", email: "..."}
   ```

#### Passo 2: Clique em "Edit User"
1. No menu que abriu, clique em "Edit User"
2. **Verifique no console**: Deve aparecer:
   ```
   handleEditClick called with selectedUser: {id: X, name: "...", email: "..."}
   Setting form data: {email: "...", name: "...", ...}
   ```

#### Passo 3: Verifique se o Diálogo Abriu
1. Deve abrir um diálogo "Edit User"
2. Os campos devem estar preenchidos com os dados do usuário

#### Passo 4: Teste a Atualização
1. Modifique algum campo (ex: nome)
2. Clique em "Update User"
3. **Verifique no console**: Deve aparecer:
   ```
   handleUpdateUser called with selectedUser: {id: X, ...}
   Update data: {email: "...", name: "novo nome", ...}
   updateUser called with: {userId: X, userData: {...}}
   Update response status: 200
   Updated user received: {id: X, name: "novo nome", ...}
   Update result: {id: X, name: "novo nome", ...}
   ```

### 4. Teste o Sistema de Permissões

#### Passo 1: Clique em "View Permissions"
1. No menu de ações (⋮), clique em "View Permissions"
2. **Verifique no console**: Deve aparecer:
   ```
   View Permissions clicked for user: {id: X, ...}
   handleViewPermissions called with user: {id: X, ...}
   Fetching permissions for user ID: X
   fetchUserPermissions called with userId: X
   Permissions response status: 200
   Permissions received: {device_permissions: [...], group_permissions: [...], ...}
   Setting selections: {deviceIds: [...], groupIds: [...], managedUserIds: [...]}
   ```

#### Passo 2: Verifique o Diálogo de Permissões
1. Deve abrir um diálogo "User Permissions - [Nome do Usuário]"
2. Deve ter 3 seções:
   - **Device Permissions**: Dropdown para selecionar dispositivos
   - **Group Permissions**: Dropdown para selecionar grupos
   - **Managed Users**: Dropdown para selecionar usuários gerenciados

#### Passo 3: Teste a Seleção de Permissões
1. Selecione alguns dispositivos, grupos ou usuários
2. Clique em "Save Permissions"
3. **Verifique no console**: Deve aparecer logs de salvamento

## Possíveis Problemas e Soluções

### Problema 1: Menu não abre
**Sintomas**: Clicar no ⋮ não faz nada
**Solução**: Verificar se há erros no console

### Problema 2: Diálogo de edição não abre
**Sintomas**: Clicar em "Edit User" não abre o diálogo
**Solução**: Verificar se `selectedUser` está sendo definido corretamente

### Problema 3: Campos não preenchidos
**Sintomas**: Diálogo abre mas campos estão vazios
**Solução**: Verificar se `formData` está sendo definido corretamente

### Problema 4: Atualização não funciona
**Sintomas**: Clicar em "Update User" não salva
**Solução**: Verificar logs da API e resposta do servidor

### Problema 5: Permissões não carregam
**Sintomas**: Diálogo de permissões não mostra dados
**Solução**: Verificar se há dispositivos, grupos e usuários no sistema

## Dados de Teste Disponíveis

### Dispositivos
- ID: 9, Nome: "Test Device 1", Unique ID: "TEST001"

### Grupos
- ID: 2, Nome: "Grupo Teste", Descrição: "Grupo para testes de permissões"

### Pessoas
- ID: 2, Nome: "João Silva", Tipo: "physical"

### Usuários
- ID: 1, Nome: "Admin", Email: "admin@traccar.com" (admin)
- ID: 3, Nome: "Test User", Email: "test@example.com" (user)

## Próximos Passos

1. **Execute os testes acima**
2. **Copie os logs do console**
3. **Reporte quais passos falharam**
4. **Inclua qualquer erro que aparecer**

Com essas informações, posso identificar exatamente onde está o problema e corrigi-lo.


