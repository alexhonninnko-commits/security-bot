<!DOCTYPE html>
<html lang="cs">
<head>
    <meta charset="UTF-8">
    <title>JavaScript Kódový Editor & Spouštěč</title>
    <style>
        body { background-color: #2b2b2b; color: white; font-family: Arial, sans-serif; padding: 20px; }
        textarea { width: 100%; height: 150px; background-color: #1e1e1e; color: #ffffff; font-family: Consolas, monospace; border: none; padding: 10px; resize: vertical; }
        button { background-color: #27ae60; color: white; font-weight: bold; padding: 10px 20px; border: none; cursor: pointer; margin-top: 10px; font-size: 11px; }
        button:hover { background-color: #219653; }
        pre { background-color: #1e1e1e; color: #2ecc71; padding: 10px; height: 100px; overflow-y: auto; font-family: Consolas, monospace; }
        .label { color: #aaaaaa; font-size: 10px; margin-top: 10px; display: block; }
    </style>
</head>
<body>

    <h2 style="text-align: center;">JavaScript Kódový Editor & Spouštěč</h2>

    <span class="label">Zadej kód k provedení:</span>
    <textarea id="codeInput">// Sem napiš svůj JS kód
for (let i = 0; i < 5; i++) {
    console.log(`Radek cislo: ${i}`);
}</textarea>

    <br>
    <button onclick="runCode()">Spustit kód</button>

    <span class="label">Výstup programu:</span>
    <pre id="outputBox">Kód ještě nebyl spuštěn...</pre>

    <script>
        function runCode() {
            const code = document.getElementById('codeInput').value;
            const outputBox = document.getElementById('outputBox');
            outputBox.textContent = "";

            // Dočasné zachycení výstupu z console.log
            let logs = [];
            const originalLog = console.log;
            console.log = (...args) => {
                logs.push(args.map(arg => typeof arg === 'object' ? JSON.stringify(arg) : arg).join(' '));
            };

            try {
                // Bezpečnější spuštění kódu v JavaScriptu
                const executeCode = new Function(code);
                executeCode();

                if (logs.length > 0) {
                    outputBox.textContent = logs.join('\n');
                } else {
                    outputBox.textContent = "Kód proběhl úspěšně bez výstupu.\n";
                }
            } catch (error) {
                outputBox.textContent = "Chyba:\n" + error.message;
            } finally {
                // Obnovení původního console.log
                console.log = originalLog;
            }
        }
    </script>

</body>
</html>
