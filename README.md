# Simulador de Fluxo Urbano

Aplicação Flask para gerenciar cruzamentos e comparar, em uma visualização 3D educativa, o fluxo em cruzamentos semaforizados e rotatórias.

## Requisitos

- Python 3.11 ou superior
- Navegador com suporte a WebGL para a visualização 3D

## Instalação no Windows (PowerShell)

No terminal, a partir da pasta `simulador_urbano`:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
$env:SIMULATOR_ADMIN_PASSWORD = Read-Host "Defina a senha inicial do administrador"
python seed.py
python app.py
```

Abra `http://127.0.0.1:5000` para ver o site público, com o mapa interativo e o simulador de tráfego. A opção **Área de gestão** leva ao login do painel Flask, disponível também em `/painel` após a autenticação. O usuário administrador inicial é `admserra@gmail.com`; a senha é definida no terminal antes de inicializar o banco. A variável é usada somente quando a conta ainda não existe. Não coloque credenciais no código nem as envie ao repositório.

O SQLite é criado em `instance/simulador.db`, pasta ignorada pelo Git. Para acessar o simulador, entre na conta e selecione um cruzamento.

## Publicação no Render

O arquivo `render.yaml` configura o site e o painel como um único serviço Flask no plano gratuito. Ao criar o Blueprint no Render, defina `SIMULATOR_ADMIN_PASSWORD` com uma senha longa e exclusiva; não reutilize senhas de teste nem envie credenciais ao repositório.

O plano gratuito usa armazenamento efêmero e pode suspender o serviço quando estiver ocioso. Como o banco SQLite fica nesse armazenamento, contas e publicações podem ser perdidas após reinicializações ou novas implantações. Para manter os dados em produção, use um banco gerenciado ou disco persistente em um plano pago.

## Simulação de tráfego

No cenário semaforizado, os fluxos Leste–Oeste e Norte–Sul alternam entre verde, amarelo e um intervalo de segurança. Os veículos aceleram e freiam gradualmente, mantêm distância e param antes da linha quando não têm passagem. No amarelo, a decisão de parar considera a velocidade e a distância de frenagem; quem já entrou no cruzamento pode liberá-lo antes da próxima fase verde. O ciclo é acelerado para facilitar a observação.

Na rotatória, os veículos cedem passagem aos carros que já estão circulando, mantêm distância e seguem a faixa até a saída. Os indicadores apresentados são estimativas educativas e não substituem medições ou estudos de engenharia de tráfego.
