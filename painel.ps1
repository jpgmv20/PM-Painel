function Mostrar-Menu {
    Clear-Host
    Write-Host "=========================="
    Write-Host " Painel de Controle Pessoal"
    Write-Host "=========================="
    Write-Host "[1] Git"
    Write-Host "[2] Programas"
    Write-Host "[3] Sair"
    Write-Host ""

    $opcao = Read-Host "Escolha uma opcao"
    switch ($opcao) {
        "1" { Git-Menu }
        "2" { Programas-Menu }
        "3" { Write-Host "Saindo..."; break }
        default { Write-Host "Opcao invalida."; Pause }
    }
}

# Menu do Git
function Git-Menu {
    while ($true) {
        Clear-Host
        $nome = git config --global user.name
        if (-not $nome) { $nome = "(nao configurado)" }
        $email = git config --global user.email
        if (-not $email) { $email = "(nao configurado)" }

        Write-Host "==========================="
        Write-Host " Painel de Controle do Git"
        Write-Host "==========================="
        Write-Host ""
        Write-Host "Usuario Git atual: $nome"
        Write-Host "Email Git atual: $email"
        Write-Host ""
        Write-Host "[1] Download Git"
        Write-Host "[2] Login"
        Write-Host "[3] Logout"
        Write-Host "[4] Ver repositorios"
        Write-Host "[5] Clonar repositorio"
        Write-Host "[6] Enviar projeto local para o GitHub"
        Write-Host "[7] Voltar"
        Write-Host ""

        $opcaog = Read-Host "Escolha uma opcao"

        switch ($opcaog) {
            "1" { Instalar-Git }
            "2" { Logar-Git }
            "3" { Logout-Git }
            "4" { Mostrar-Repositorios }
            "5" { Clonar-Repositorio }
            "6" { Enviar-Projeto }
            "7" { Mostrar-Menu }
            default { Write-Host "Opcao invalida. Tente novamente."; Pause }
        }
    }
}

function Instalar-Git {
    Write-Host "Baixando e instalando Git..."
    $url = "https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-64-bit.exe"
    $destino = "$env:TEMP\git-installer.exe"
    Invoke-WebRequest -Uri $url -OutFile $destino
    Start-Process $destino -ArgumentList "/VERYSILENT" -Wait
    Write-Host "Git instalado com sucesso!"
    Pause
}

function Logar-Git {
    $nome = Read-Host "Digite seu nome de usuario do GitHub"
    $email = Read-Host "Digite seu e-mail para o Git"
    $token = Read-Host "Cole seu token de acesso pessoal (PAT)"
    git config --global user.name "$nome"
    git config --global user.email "$email"
    git config --global github.token "$token"
    Write-Host "`nLogin configurado com sucesso!"
    Pause
}

function Logout-Git {
    git config --global --unset user.name
    git config --global --unset user.email
    git config --global --unset github.token
    cmdkey /delete:git:https://github.com | Out-Null
    Write-Host "Logout concluido!"
    Pause
}

function Mostrar-Repositorios {
    $usuario = git config --global user.name
    $token = git config --global github.token
    if (-not $usuario -or -not $token) {
        Write-Host "Usuario ou token nao configurado. Faca login primeiro."
        Pause
        return
    }
    $headers = @{ Authorization = "Bearer $token"; "User-Agent" = "$usuario" }

    function Contar-Conteudo($url) {
        $arquivos = 0; $pastas = 0
        try {
            $itens = Invoke-RestMethod -Uri $url -Headers $headers -UseBasicParsing
            foreach ($item in $itens) {
                if ($item.type -eq "file") { $arquivos++ }
                elseif ($item.type -eq "dir") {
                    $pastas++
                    $sub = Contar-Conteudo $item.url
                    $arquivos += $sub.arquivos
                    $pastas += $sub.pastas
                }
            }
        } catch {}
        return @{ arquivos = $arquivos; pastas = $pastas }
    }

    $url = "https://api.github.com/user/repos?per_page=100"
    try {
        $repos = Invoke-RestMethod -Uri $url -Headers $headers -UseBasicParsing
        if (-not $repos) {
            Write-Host "Nenhum repositorio encontrado."
        } else {
            foreach ($repo in $repos) {
                $visibilidade = if ($repo.private) { "[Privado]" } else { "[Publico]" }
                $nomeRepo = $repo.name
                $urlConteudo = "https://api.github.com/repos/$usuario/$nomeRepo/contents"
                $res = Contar-Conteudo $urlConteudo
                Write-Host "`n $nomeRepo $visibilidade - Arquivos: $($res.arquivos), Pastas: $($res.pastas)"
            }
        }
    } catch {
        Write-Host "Erro ao acessar repositorios."
    }
    Pause
}

function Clonar-Repositorio {
    $usuario = git config --global user.name
    $token = git config --global github.token
    if (-not $usuario -or -not $token) {
        Write-Host "Faca login primeiro."
        Pause
        return
    }
    $headers = @{ Authorization = "Bearer $token"; "User-Agent" = "$usuario" }
    $url = "https://api.github.com/user/repos?per_page=100"
    $repos = Invoke-RestMethod -Uri $url -Headers $headers -UseBasicParsing

    if ($repos.Count -ne 0) {
        Write-Host "`nEscolha um repositório para clonar:"
        for ($i = 0; $i -lt $repos.Count; $i++) {
            Write-Host "[$i] $($repos[$i].name)"
        }
        $escolha = Read-Host "Numero"
        $repo = $repos[$escolha].clone_url
        $dest = Read-Host "Caminho da pasta"
        git clone $repo $dest
        Write-Host "Repositorio clonado com sucesso!"
    } else {
        Write-Host "Nenhum repositorio encontrado."
    }
    Pause
}

function Enviar-Projeto {
    $usuario = git config --global user.name
    $token = git config --global github.token
    if (-not $usuario -or -not $token) {
        Write-Host "Faca login primeiro."
        Pause
        return
    }
    $headers = @{ Authorization = "Bearer $token"; "User-Agent" = "$usuario" }
    $url = "https://api.github.com/user/repos?per_page=100"
    $repos = Invoke-RestMethod -Uri $url -Headers $headers -UseBasicParsing

    if ($repos.Count -ne 0) {
        Write-Host "`nEscolha o repositorio:"
        for ($i = 0; $i -lt $repos.Count; $i++) {
            Write-Host "[$i] $($repos[$i].name)"
        }
        $escolha = Read-Host "Numero"
        $repo = $repos[$escolha]
        $urlRemoto = $repo.clone_url -replace "https://", "https://$token@"
        $caminho = Read-Host "Caminho da pasta local"
        Push-Location $caminho
        if (-not (Test-Path ".git")) {
            git init
            git remote add origin $urlRemoto
        } else {
            git remote set-url origin $urlRemoto
        }
        git add .
        $mensagem = Read-Host "Mensagem do commit"
        git commit -m "$mensagem"
        $branch = Read-Host "Nome do branch para envio (ex: main ou master)"
        git branch -M $branch
        git push -u origin $branch
        Pop-Location
        Write-Host "Projeto enviado!"
    } else {
        Write-Host "Nenhum repositorio encontrado."
    }
    Pause
}

# Menu de Programas
function Programas-Menu {
    while ($true) {
        Clear-Host
        Write-Host "=============================="
        Write-Host " Painel de Programas"
        Write-Host "=============================="
        Write-Host "[1] Instalar Git"
        Write-Host "[2] Instalar Node.js"
        Write-Host "[3] Instalar Python"
        Write-Host "[4] Instalar VS Code"
        Write-Host "[5] Instalar tudo"
        Write-Host "[6] Desinstalar programas"
        Write-Host "[7] Voltar"
        Write-Host ""
        $opcao = Read-Host "Escolha uma opcao"
        switch ($opcao) {
            "1" { Instalar-Git }
            "2" { Instalar-Node }
            "3" { Instalar-Python }
            "4" { Instalar-VSCode }
            "5" { Instalar-Tudo }
            "6" { Desinstalar-Menu }
            "7" { Mostrar-Menu }
            default { Write-Host "Opcao invalida."; Pause }
        }
    }
}

function Instalar-Node {
    if (Get-Command node -ErrorAction SilentlyContinue) {
        Write-Host "Node.js ja instalado."
    } else {
        Write-Host "Instalando Node.js..."
        $url = "https://nodejs.org/dist/v20.11.1/node-v20.11.1-x64.msi"
        $dest = "$env:TEMP\node.msi"
        Invoke-WebRequest $url -OutFile $dest
        Start-Process msiexec.exe -ArgumentList "/i $dest /quiet /norestart" -Wait
        Write-Host "Node.js instalado!"
    }
    Pause
}

function Instalar-Python {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        Write-Host "Python ja instalado."
    } else {
        Write-Host "Instalando Python..."
        $url = "https://www.python.org/ftp/python/3.12.3/python-3.12.3-amd64.exe"
        $dest = "$env:TEMP\python-installer.exe"
        Invoke-WebRequest $url -OutFile $dest
        Start-Process $dest -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
        Write-Host "Python instalado!"
    }
    Pause
}

function Instalar-VSCode {
    $vscodePath = "$env:ProgramFiles\Microsoft VS Code\Code.exe"
    if (Test-Path $vscodePath) {
        Write-Host "VS Code ja instalado."
    } else {
        Write-Host "Instalando VS Code..."
        $url = "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user"
        $dest = "$env:TEMP\vscode-installer.exe"
        Invoke-WebRequest $url -OutFile $dest
        Start-Process $dest -ArgumentList "/silent /mergetasks=!runcode" -Wait
        Write-Host "VS Code instalado!"
    }
    Pause
}

function Instalar-Tudo {
    Instalar-Git
    Instalar-Node
    Instalar-Python
    Instalar-VSCode
}

# Menu de Desinstalacao
function Desinstalar-Menu {
    while ($true) {
        Clear-Host
        Write-Host "=============================="
        Write-Host " Painel de Desinstalacao"
        Write-Host "=============================="
        Write-Host "[1] Desinstalar Git"
        Write-Host "[2] Desinstalar Node.js"
        Write-Host "[3] Desinstalar Python"
        Write-Host "[4] Desinstalar VS Code"
        Write-Host "[5] Desinstalar tudo"
        Write-Host "[6] Voltar"
        Write-Host ""
        $opcao = Read-Host "Escolha uma opcao"
        switch ($opcao) {
            "1" { Desinstalar-Git }
            "2" { Desinstalar-Node }
            "3" { Desinstalar-Python }
            "4" { Desinstalar-VSCode }
            "5" { Desinstalar-Tudo }
            "6" { Programas-Menu }
            default { Write-Host "Opcao invalida."; Pause }
        }
    }
}

function Desinstalar-Git {
    Write-Host "Desinstalando Git..."
    winget uninstall --id Git.Git -e --silent
    Pause
}
function Desinstalar-Node {
    Write-Host "Desinstalando Node.js..."
    winget uninstall "Node.js" --silent
    Pause
}
function Desinstalar-Python {
    Write-Host "Desinstalando Python..."
    winget uninstall "Python" --silent
    Pause
}
function Desinstalar-VSCode {
    Write-Host "Desinstalando VS Code..."
    winget uninstall "Microsoft Visual Studio Code" --silent
    Pause
}
function Desinstalar-Tudo {
    Desinstalar-Git
    Desinstalar-Node
    Desinstalar-Python
    Desinstalar-VSCode
}

# Loop principal
do {
    Mostrar-Menu
    
} while ($true)
