@echo off
:: Verifica se está rodando como Administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Execute este arquivo como Administrador.
    echo Clique com o botao direito e escolha "Executar como administrador".
    pause
    exit /b 1
)

echo [FIREWALL] Criando regra para porta 5000 (SmartBathroom Flask)...

netsh advfirewall firewall delete rule name="SmartBathroom Flask 5000" >nul 2>&1

netsh advfirewall firewall add rule ^
    name="SmartBathroom Flask 5000" ^
    dir=in ^
    action=allow ^
    protocol=TCP ^
    localport=5000 ^
    profile=any

if %errorlevel% equ 0 (
    echo [OK] Porta 5000 liberada com sucesso!
    echo      Raspberry Pi (10.1.25.110) agora consegue acessar o Flask.
) else (
    echo [ERRO] Falha ao criar regra de firewall.
)

pause
