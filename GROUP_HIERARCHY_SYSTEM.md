# Sistema de Hierarquia de Grupos

## Visão Geral

O sistema de grupos do Traccar foi expandido para suportar hierarquia hierárquica, permitindo que grupos herdem permissões de grupos pai, criando uma cascata de permissões. Este sistema permite uma organização mais flexível e escalável de permissões de usuários e dispositivos.

## Características Principais

### 1. Hierarquia de Grupos
- **Grupos Raiz**: Grupos sem pai (parent_id = null)
- **Grupos Filhos**: Grupos que herdam de um grupo pai
- **Níveis**: Cada grupo tem um nível hierárquico (0 = raiz, 1 = primeiro nível, etc.)

### 2. Herança de Permissões
- Usuários com permissão em um grupo automaticamente têm acesso a todos os grupos filhos
- A herança é recursiva (grupos filhos de grupos filhos também são acessíveis)
- Administradores têm acesso a todos os grupos independentemente da hierarquia

### 3. Validações de Segurança
- Prevenção de referências circulares
- Validação de permissões para criação de grupos filhos
- Verificação de existência de grupos pai

## Estrutura do Banco de Dados

### Tabela `groups`
```sql
ALTER TABLE groups ADD COLUMN parent_id INTEGER REFERENCES groups(id);
```

### Campos Adicionais
- `parent_id`: ID do grupo pai (nullable)
- `level`: Nível hierárquico calculado automaticamente
- `children_count`: Número de grupos filhos
- `parent_name`: Nome do grupo pai (para exibição)

## API Endpoints

### GET /api/groups/
Retorna todos os grupos que o usuário tem permissão para acessar, incluindo grupos herdados.

**Resposta:**
```json
[
  {
    "id": 8,
    "name": "SUPORTE",
    "description": "GRUPO ADM DE TODOS DEVICE",
    "parent_id": null,
    "parent_name": null,
    "level": 0,
    "children_count": 1,
    "device_count": 0,
    "person_name": null,
    "disabled": false,
    "created_at": "2025-09-06T19:20:59.038177Z"
  },
  {
    "id": 11,
    "name": "SUPORTE TÉCNICO",
    "description": "Subgrupo do SUPORTE",
    "parent_id": 8,
    "parent_name": "SUPORTE",
    "level": 1,
    "children_count": 0,
    "device_count": 0,
    "person_name": null,
    "disabled": false,
    "created_at": "2025-09-06T19:54:29.061495Z"
  }
]
```

### POST /api/groups/
Cria um novo grupo com validação de hierarquia.

**Parâmetros:**
```json
{
  "name": "Nome do Grupo",
  "description": "Descrição opcional",
  "parent_id": 8,  // ID do grupo pai (opcional)
  "person_id": 1,  // ID da pessoa responsável (opcional)
  "disabled": false
}
```

**Validações:**
- Nome do grupo deve ser único
- Grupo pai deve existir
- Usuário deve ter permissão para criar grupos sob o grupo pai especificado
- Prevenção de referências circulares

## Lógica de Permissões

### Algoritmo de Herança
1. **Usuários Admin**: Têm acesso a todos os grupos
2. **Usuários Regulares**: 
   - Acesso direto aos grupos com permissão explícita
   - Acesso automático a todos os grupos filhos (recursivo)

### Função `get_user_accessible_groups()`
```python
async def get_user_accessible_groups(db: AsyncSession, user_id: int, is_admin: bool) -> Set[int]:
    """
    Retorna todos os IDs de grupos que um usuário pode acessar, incluindo grupos herdados.
    """
    if is_admin:
        # Admin pode acessar todos os grupos
        return {row[0] for row in result.all()}
    
    # Obter grupos diretamente atribuídos
    direct_groups = {row[0] for row in result.all()}
    
    # Encontrar todos os grupos filhos recursivamente
    accessible_groups = set(direct_groups)
    current_level = direct_groups
    
    while current_level:
        children = find_children(current_level)
        new_groups = children - accessible_groups
        if not new_groups:
            break
        accessible_groups.update(new_groups)
        current_level = new_groups
    
    return accessible_groups
```

## Interface do Usuário

### Visualização Hierárquica
- **Indentação Visual**: Grupos filhos são indentados com símbolos `└─`
- **Coluna Parent**: Mostra o nome do grupo pai
- **Coluna Children**: Mostra o número de grupos filhos
- **Ordenação**: Por nível hierárquico e depois por nome

### Formulário de Criação/Edição
- **Campo Parent Group**: Dropdown com todos os grupos disponíveis
- **Indentação no Dropdown**: Mostra a hierarquia na seleção
- **Prevenção de Auto-referência**: Impede que um grupo seja seu próprio pai

## Exemplos de Uso

### Cenário 1: Organização por Região
```
SUPORTE (Nível 0)
├── SUPORTE TÉCNICO (Nível 1)
│   ├── SUPORTE SP (Nível 2)
│   └── SUPORTE RJ (Nível 2)
└── SUPORTE COMERCIAL (Nível 1)
    ├── SUPORTE VENDAS (Nível 2)
    └── SUPORTE MARKETING (Nível 2)
```

### Cenário 2: Organização por Cliente
```
CLIENTES (Nível 0)
├── CLIENTE A (Nível 1)
│   ├── CLIENTE A - DEVICES (Nível 2)
│   └── CLIENTE A - USERS (Nível 2)
└── CLIENTE B (Nível 1)
    └── CLIENTE B - PRODUÇÃO (Nível 2)
```

## Regras de Negócio

### 1. Criação de Grupos
- Usuários podem criar grupos apenas sob grupos que têm permissão
- Administradores podem criar grupos em qualquer nível
- Nome do grupo deve ser único globalmente

### 2. Edição de Grupos
- Usuários podem editar apenas grupos que têm permissão
- Mudança de grupo pai requer permissão no novo grupo pai
- Prevenção de referências circulares

### 3. Exclusão de Grupos
- Grupos com filhos não podem ser excluídos
- Grupos com dispositivos associados requerem confirmação
- Exclusão em cascata pode ser implementada se necessário

### 4. Permissões de Usuário
- Permissões são herdadas automaticamente
- Usuários veem apenas grupos que têm permissão (incluindo herdados)
- Administradores veem todos os grupos

## Benefícios

### 1. Escalabilidade
- Organização hierárquica permite crescimento sem complexidade
- Permissões automáticas reduzem configuração manual

### 2. Flexibilidade
- Estrutura adaptável a diferentes organizações
- Suporte a múltiplos níveis de hierarquia

### 3. Segurança
- Validações rigorosas previnem configurações incorretas
- Herança de permissões mantém consistência

### 4. Usabilidade
- Interface visual clara da hierarquia
- Formulários intuitivos com validação em tempo real

## Considerações Técnicas

### Performance
- Queries otimizadas para hierarquia
- Cache de permissões pode ser implementado
- Índices no banco para consultas eficientes

### Manutenção
- Logs de alterações hierárquicas
- Backup de estrutura antes de mudanças
- Validação de integridade periódica

## Próximos Passos

1. **Implementar cache de permissões** para melhorar performance
2. **Adicionar logs de auditoria** para mudanças hierárquicas
3. **Implementar validação de integridade** automática
4. **Adicionar suporte a herança de dispositivos** se necessário
5. **Implementar migração de dados** para estruturas existentes

## Conclusão

O sistema de hierarquia de grupos fornece uma base sólida para organização escalável de permissões, mantendo a simplicidade de uso enquanto oferece flexibilidade para estruturas organizacionais complexas. A implementação garante segurança e consistência através de validações rigorosas e herança automática de permissões.
