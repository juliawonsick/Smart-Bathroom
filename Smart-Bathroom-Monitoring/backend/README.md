# SmartBathroom 🚽

Sistema web de monitoramento de banheiros para campus universitário.

---

## 📁 Estrutura do projeto

```
smartbathroom/
├── app.py                  # Aplicação Flask principal (rotas, lógica, banco)
├── run.py                  # Script de inicialização com ngrok
├── arduino_raspberry.py    # Código de integração com Raspberry Pi / Arduino
├── requirements.txt        # Dependências Python
├── smartbathroom.db        # Banco SQLite (criado automaticamente)
└── templates/
    ├── login.html          # Tela de login (aluno + limpeza)
    ├── cadastro.html       # Cadastro de aluno
    ├── aluno.html          # Dashboard do aluno
    └── limpeza.html        # Dashboard da equipe de limpeza
```

---

## ⚙️ Instalação (VSCode / terminal)

### 1. Crie um ambiente virtual (recomendado)

```bash
cd smartbathroom
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. (Opcional) Configure o token do ngrok

Crie uma conta gratuita em https://ngrok.com, copie seu authtoken e:

```bash
# Windows
set NGROK_AUTHTOKEN=seu_token_aqui

# Linux/Mac
export NGROK_AUTHTOKEN=seu_token_aqui
```

> Sem o token, o ngrok funciona com limitações (1 sessão simultânea, URL muda a cada reinício).

### 4. Inicie o servidor

```bash
python run.py
```

O terminal mostrará:
- URL pública ngrok (para outros dispositivos e celular)
- URL local (http://localhost:5000)

---

## 👤 Contas de acesso

### Equipe de Limpeza (pré-cadastrada)
| Campo    | Valor          |
|----------|----------------|
| Usuário  | limpeza.atitus |
| Senha    | limpeza2026    |

### Aluno
Acesse `/cadastro` e preencha:
- Nome completo
- RA (7 dígitos numéricos)
- Email: gerado automaticamente como `RA@atitus.edu.br`
- Senha (mínimo 8 caracteres)

**Nenhum campo aceita emojis.**

---

## 🌐 Rotas da aplicação

| Rota                      | Método | Descrição                              |
|---------------------------|--------|----------------------------------------|
| `/`                       | GET    | Redireciona conforme sessão            |
| `/login`                  | GET/POST | Login de aluno ou limpeza            |
| `/cadastro`               | GET/POST | Cadastro de aluno                    |
| `/logout`                 | GET    | Encerra sessão                         |
| `/aluno`                  | GET    | Dashboard do aluno                     |
| `/limpeza`                | GET    | Dashboard da equipe de limpeza         |
| `/api/aluno/status`       | GET    | Status dos itens (polling aluno)       |
| `/api/aluno/report`       | POST   | Reportar falta de item                 |
| `/api/limpeza/status`     | GET    | Status + histórico (polling limpeza)   |
| `/api/limpeza/resolve`    | POST   | Resolver alerta individual             |
| `/api/limpeza/mark_cleaning` | POST | Marcar banheiro como realizado (resolve tudo) |
| `/api/arduino/report`     | POST   | Sensor reporta falta (Arduino/Raspberry) |
| `/api/arduino/status`     | GET    | Consulta status para Arduino/Raspberry |

---

## 🤖 Integração Arduino / Raspberry Pi 4

Edite o arquivo `arduino_raspberry.py`:

1. Defina `SERVER_URL` com a URL do servidor (ngrok ou IP local da rede)
2. Descomente as linhas do `RPi.GPIO` e configure os pinos corretos
3. Execute no Raspberry Pi:

```bash
python arduino_raspberry.py
```

### Exemplo de chamada da API via HTTP (Arduino com ESP8266/ESP32)

```cpp
// POST para reportar falta
HTTPClient http;
http.begin("http://SEU_IP:5000/api/arduino/report");
http.addHeader("Content-Type", "application/json");
int code = http.POST("{\"item\":\"Papel Higiênico\",\"bathroom\":\"Banheiro Bloco A\"}");
```

---

## 🔄 Atualização em tempo real

- Dashboard do **aluno** atualiza automaticamente a cada **8 segundos**
- Dashboard da **limpeza** atualiza automaticamente a cada **6 segundos**
- Quando a limpeza resolve um alerta, o status do aluno é atualizado no próximo ciclo

---

## 🗄️ Banco de dados SQLite

O arquivo `smartbathroom.db` é criado automaticamente. Tabelas:

- **users** — alunos e equipe de limpeza
- **alerts** — histórico de alertas (status: `aberto` / `resolvido`)
