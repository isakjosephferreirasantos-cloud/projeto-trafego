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

Abra `http://127.0.0.1:5000`. O usuário administrador inicial é `admserra@gmail.com`; a senha é definida no terminal antes de inicializar o banco. A variável é usada somente quando a conta ainda não existe. Não coloque credenciais no código nem as envie ao repositório.

O SQLite é criado em `instance/simulador.db`, pasta ignorada pelo Git. Para acessar o simulador, entre na conta e selecione um cruzamento.

## Simulação de tráfego

No cenário semaforizado, os fluxos Leste–Oeste e Norte–Sul alternam entre verde, amarelo e um intervalo de segurança. Os veículos reduzem a velocidade e param antes da linha quando não têm passagem; veículos que já entraram no cruzamento podem liberá-lo antes da próxima fase verde. O ciclo é acelerado para facilitar a observação.

Na rotatória, os veículos cedem passagem aos carros que já estão circulando, mantêm distância e seguem a faixa até a saída. Os indicadores apresentados são estimativas educativas e não substituem medições ou estudos de engenharia de tráfego.
