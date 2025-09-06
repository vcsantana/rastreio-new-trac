# 🌐 Guia de Solução: Acesso Externo via 5G

## 🔍 **Problema Identificado**

- ✅ **Rede Local + no-ip.org:5055** - Funciona
- ❌ **5G + no-ip.org:5055** - Não funciona

---

## 🚨 **Possíveis Causas**

### **1. Firewall do Servidor**
O firewall pode estar bloqueando conexões externas.

### **2. Configuração do Roteador**
Port forwarding pode não estar configurado corretamente.

### **3. ISP (Provedor de Internet)**
Alguns ISPs bloqueiam portas específicas.

### **4. Configuração do no-ip.org**
O DNS pode não estar propagado corretamente.

---

## 🔧 **Soluções**

### **1. Verificar Firewall do Servidor**

```bash
# Verificar se o firewall está ativo
sudo ufw status

# Se estiver ativo, liberar a porta 5055
sudo ufw allow 5055

# Verificar regras do iptables
sudo iptables -L -n | grep 5055
```

### **2. Configurar Port Forwarding no Roteador**

**Configuração necessária:**
- **Porta Externa:** 5055
- **Porta Interna:** 5055
- **IP do Servidor:** [IP interno do seu servidor]
- **Protocolo:** TCP

### **3. Testar Conectividade**

```bash
# Testar se a porta está acessível externamente
telnet qvnk.no-ip.org 5055

# Ou usar nc (netcat)
nc -zv qvnk.no-ip.org 5055
```

### **4. Verificar DNS do no-ip.org**

```bash
# Verificar se o DNS está resolvendo corretamente
nslookup qvnk.no-ip.org

# Testar com diferentes DNS
dig @8.8.8.8 qvnk.no-ip.org
```

---

## 🧪 **Testes de Diagnóstico**

### **Teste 1: Conectividade Básica**
```bash
# No servidor, testar se está escutando em todas as interfaces
ss -tlnp | grep 5055
```

### **Teste 2: Firewall**
```bash
# Testar conexão local
curl -v http://localhost:5055

# Testar conexão via IP interno
curl -v http://[IP_INTERNO]:5055
```

### **Teste 3: Port Forwarding**
```bash
# No celular (5G), testar conectividade
telnet qvnk.no-ip.org 5055
```

---

## 📱 **Configuração no App OsmAnd**

### **URLs de Teste:**
1. **Rede Local:** `http://[IP_INTERNO]:5055`
2. **Externo:** `http://qvnk.no-ip.org:5055`

### **Configurações Recomendadas:**
- **Protocol:** HTTP
- **Port:** 5055
- **Interval:** 30 segundos
- **Accuracy:** 10 metros

---

## 🛠️ **Soluções Alternativas**

### **1. Usar Porta Diferente**
Se a 5055 estiver bloqueada pelo ISP:
```yaml
# No docker-compose.dev.yml
ports:
  - "8080:5055"  # Mapear para porta 8080
```

### **2. Usar HTTPS**
```yaml
# Configurar SSL/TLS
ports:
  - "8443:5055"
```

### **3. Usar Túnel SSH**
```bash
# Criar túnel SSH
ssh -L 5055:localhost:5055 user@qvnk.no-ip.org
```

---

## 🔍 **Comandos de Diagnóstico**

### **No Servidor:**
```bash
# Verificar portas abertas
sudo netstat -tlnp | grep 5055

# Verificar logs do Docker
docker logs new-api-1 | grep -i osmand

# Testar conectividade local
curl -v http://localhost:5055/api/positions
```

### **No Celular (5G):**
```bash
# Testar DNS
nslookup qvnk.no-ip.org

# Testar conectividade
ping qvnk.no-ip.org

# Testar porta
telnet qvnk.no-ip.org 5055
```

---

## 📋 **Checklist de Verificação**

- [ ] Firewall do servidor configurado
- [ ] Port forwarding no roteador
- [ ] DNS do no-ip.org funcionando
- [ ] ISP não bloqueando porta 5055
- [ ] App OsmAnd configurado corretamente
- [ ] Servidor escutando em 0.0.0.0:5055

---

## 🆘 **Próximos Passos**

1. **Executar comandos de diagnóstico**
2. **Verificar configuração do roteador**
3. **Testar com porta alternativa**
4. **Contatar ISP se necessário**
5. **Configurar túnel SSH como alternativa**

---

## 📞 **Suporte**

Se o problema persistir:
1. Verificar logs do servidor
2. Testar com ferramentas de rede
3. Considerar usar VPN ou túnel
4. Verificar políticas do ISP
