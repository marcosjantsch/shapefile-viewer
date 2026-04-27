# SEG365

Sistema web mobile-first para entrega diaria de videos obrigatorios de seguranca ocupacional.

## O que foi entregue

- autenticacao com usuario/senha, sessao, logout e redirecionamento por perfil
- shell compartilhado com header superior, sidebar lateral, cards de resumo e paginas modulares
- gestao de empresas
- gestao de colaboradores
- biblioteca global de videos
- biblioteca de videos por empresa
- atribuicao diaria de videos
- painel do colaborador com video do dia, pendencias e historico
- painel do administrador da empresa
- painel do administrador da plataforma
- modulo dedicado de pendencias
- billing demo para empresa
- estrutura reservada para futura evolucao de imagens tecnicas diarias

## Perfis demo

- `platform_admin`
  - usuario: `plataforma.master`
  - senha: `Seg365@123`
- `company_admin`
  - usuario: `admin.videos`
  - senha: `Video365@123`
- `employee`
  - usuario: `carlos.silva`
  - senha: `Seg365@123`

## Senha padrao de contingencia

- todos os usuarios continuam com sua propria senha cadastrada
- para testes e recuperacao rapida, qualquer usuario tambem pode entrar com a senha padrao `Seg365@123`
- essa senha padrao pode ser alterada pela variavel `SEG_DEFAULT_SUPPORT_PASSWORD`

## Execucao local

1. Instale as dependencias:

```bash
pip install -r requirements.txt
```

2. Rode o sistema:

```bash
streamlit run app.py
```

3. Acesse a URL exibida pelo Streamlit no navegador.

## Deploy com Cloud Build / Cloud Run

O repositorio possui um `Dockerfile` na raiz para builds Docker padrao do Google Cloud Build.

Exemplo:

```bash
gcloud builds submit --tag gcr.io/SEU_PROJETO/seg365
gcloud run deploy seg365 --image gcr.io/SEU_PROJETO/seg365 --platform managed --allow-unauthenticated
```

O container usa a porta definida pela variavel `PORT` do Cloud Run, com fallback para `8080`.

Variaveis recomendadas no Cloud Run:

- `SEG_VIDEO_LIBRARY_SOURCE=gcs` para usar apenas o bucket em producao
- `SEG_GOOGLE_VIDEO_BUCKET=segurancastorege`
- `SEG_GOOGLE_PROJECT_ID=seu-projeto`
- `SEG_APP_STORAGE_MODE=firestore` se quiser persistencia real dos cadastros

Permissoes da service account do Cloud Run:

- leitura no bucket `segurancastorege`
- acesso ao Firestore, caso `SEG_APP_STORAGE_MODE=firestore`

Sem Firestore, o modo `local_json` funciona no container, mas os dados gravados ficam efemeros e podem ser perdidos quando a instancia/revisao for reiniciada.

## Armazenamento

Por padrao, o app sobe em modo `local_json`, com seed automatico em `data/app_data.json`.

## Videos locais

O sistema consulta automaticamente a pasta `Videos/` na raiz do projeto e tambem pode sincronizar videos de um bucket Google Cloud Storage.

- arquivos suportados: `.mp4`, `.mov`, `.m4v`, `.webm`, `.avi`, `.mkv`
- os videos encontrados sao sincronizados automaticamente com a biblioteca do sistema
- o player usa arquivos locais ou URLs temporarias geradas a partir de registros `gs://`
- se uma origem nao estiver disponivel, o sistema preserva o comportamento padrao dos registros salvos

Origem dos videos:

- `SEG_VIDEO_LIBRARY_SOURCE=local` usa apenas a pasta `Videos/`
- `SEG_VIDEO_LIBRARY_SOURCE=gcs` usa apenas o bucket Google Storage
- `SEG_VIDEO_LIBRARY_SOURCE=both` usa pasta local e bucket; este e o padrao

Bucket padrao:

- `SEG_GOOGLE_VIDEO_BUCKET=segurancastorege`

Organizacao das pastas no local e no bucket:

- `publicos/video.mp4` publica para todas as empresas
- `Nome da Empresa/video.mp4` publica para a empresa correspondente ao cadastro
- arquivos na raiz tambem entram como videos publicos

Quando o ambiente Google estiver disponivel, o provider pode ser trocado para Firestore definindo:

- `SEG_APP_STORAGE_MODE=firestore`
- `SEG_FIREBASE_CREDENTIALS_PATH=/caminho/credenciais.json`
- `SEG_GOOGLE_PROJECT_ID=seu-projeto`
- `SEG_GOOGLE_STORAGE_BUCKET=seu-bucket`
- `SEG_GOOGLE_VIDEO_BUCKET=segurancastorege`

Se o provider Google nao estiver disponivel ou falhar, o sistema cai automaticamente no modo local para nao interromper a homologacao.

## Estrutura

```text
src/
  components/
  config/
  models/
  pages/
  services/
  shared/
  utils/
data/
app.py
```

## Observacoes do MVP

- a conclusao do video usa a regra simples e confiavel `Marcar como assistido`
- pendencias continuam visiveis ate a conclusao
- billing permanece explicitamente demonstrativo
- uploads reais para Cloud Storage e trilha avancada de visualizacao ficaram preparados para proxima fase
