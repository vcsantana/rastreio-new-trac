# 🧪 Teste do Sistema de Usuários - Frontend

## ✅ Dados de Teste Criados

### **Dispositivos Disponíveis:**
- **ID 9**: "Test Device 1" (TEST001)
- **ID 10**: "Dispositivo Veículo 1" (VEIC001) 
- **ID 11**: "Dispositivo Veículo 2" (VEIC002)

### **Grupos Disponíveis:**
- **ID 2**: "Grupo Teste" (Grupo para testes de permissões)
- **ID 3**: "Frota Veículos" (Grupo para veículos da frota)
- **ID 4**: "Funcionários" (Grupo para funcionários da empresa)

### **Pessoas Disponíveis:**
- **ID 2**: "João Silva" (Pessoa Física)
- **ID 3**: "Maria Silva" (Pessoa Física)
- **ID 4**: "Empresa ABC Ltda" (Pessoa Jurídica)

### **Usuários Disponíveis:**
- **ID 1**: "Admin User" (admin@traccar.com) - Admin
- **ID 2**: "Kalebe Santana" (kalebe@gmail.com) - User (COM PERMISSÕES)
- **ID 3**: "Test User Modificado" (test@example.com) - User
- **ID 4**: "Administrator" (admin@traccar.org) - Admin

## 🎯 Teste 1: Edição de Usuário

### **Passo 1: Abrir Console**
1. Acesse: `http://localhost:3000/users`
2. Pressione **F12** → Aba **Console**

### **Passo 2: Testar Edição**
1. Clique no **⋮** (três pontos) do usuário **"Test User Modificado"**
2. Clique em **"Edit User"**
3. **Verifique no console** se aparecem os logs:
   ```
   handleMenuClick called with user: {id: 3, name: "Test User Modificado", ...}
   handleEditClick called with selectedUser: {id: 3, ...}
   Setting form data: {email: "test@example.com", name: "Test User Modificado", ...}
   ```

### **Passo 3: Modificar e Salvar**
1. No diálogo que abriu, mude o nome para: **"Test User Final"**
2. Clique em **"Update User"**
3. **Verifique no console** se aparecem os logs:
   ```
   handleUpdateUser called with selectedUser: {id: 3, ...}
   Update data: {email: "test@example.com", name: "Test User Final", ...}
   updateUser called with: {userId: 3, userData: {...}}
   Update response status: 200
   Updated user received: {id: 3, name: "Test User Final", ...}
   ```

## 🎯 Teste 2: Sistema de Permissões

### **Passo 1: Testar Permissões do Kalebe**
1. Clique no **⋮** do usuário **"Kalebe Santana"**
2. Clique em **"View Permissions"**
3. **Verifique no console** se aparecem os logs:
   ```
   View Permissions clicked for user: {id: 2, ...}
   handleViewPermissions called with user: {id: 2, ...}
   Fetching permissions for user ID: 2
   fetchUserPermissions called with userId: 2
   Permissions response status: 200
   Permissions received: {device_permissions: [...], group_permissions: [...], ...}
   ```

### **Passo 2: Verificar Diálogo de Permissões**
1. Deve abrir um diálogo **"User Permissions - Kalebe Santana"**
2. **Device Permissions**: Deve mostrar 3 dispositivos selecionados
3. **Group Permissions**: Deve mostrar 3 grupos selecionados  
4. **Managed Users**: Deve mostrar "Test User Modificado" selecionado

### **Passo 3: Testar Modificação de Permissões**
1. **Desmarque** um dispositivo (ex: "Test Device 1")
2. **Adicione** um novo grupo (ex: "Funcionários")
3. Clique em **"Save Permissions"**
4. **Verifique no console** se aparecem logs de salvamento

## 🎯 Teste 3: Usuário Sem Permissões

### **Passo 1: Testar Usuário Limpo**
1. Clique no **⋮** do usuário **"Test User Modificado"**
2. Clique em **"View Permissions"**
3. **Verifique**: Deve mostrar permissões vazias (0 dispositivos, 0 grupos, 0 usuários gerenciados)

### **Passo 2: Adicionar Permissões**
1. **Selecione** alguns dispositivos e grupos
2. Clique em **"Save Permissions"**
3. **Verifique**: Deve salvar com sucesso

## 🚨 Problemas Possíveis

### **Problema 1: Menu não abre**
- **Sintoma**: Clicar no ⋮ não faz nada
- **Solução**: Verificar se há erros no console

### **Problema 2: Diálogo não abre**
- **Sintoma**: Clicar em "Edit User" ou "View Permissions" não abre diálogo
- **Solução**: Verificar logs no console

### **Problema 3: Campos vazios**
- **Sintoma**: Diálogo abre mas campos estão vazios
- **Solução**: Verificar se `formData` está sendo definido

### **Problema 4: Erro ao salvar**
- **Sintoma**: Clicar em "Update User" ou "Save Permissions" dá erro
- **Solução**: Verificar logs da API no console

## 📋 Checklist de Teste

- [ ] **Menu de ações abre** (⋮)
- [ ] **Edição de usuário funciona** (Edit User)
- [ ] **Campos são preenchidos** corretamente
- [ ] **Atualização salva** com sucesso
- [ ] **Permissões carregam** (View Permissions)
- [ ] **Diálogo de permissões abre** com dados
- [ ] **Seleção múltipla funciona** (dispositivos, grupos, usuários)
- [ ] **Salvamento de permissões funciona**

## 🔍 O que Reportar

Se algo não funcionar, copie e cole:
1. **Logs do console** (F12 → Console)
2. **Qual teste falhou** (Teste 1, 2 ou 3)
3. **Qual passo específico** não funcionou
4. **Qualquer erro** que aparecer

Com essas informações, posso corrigir o problema imediatamente!


