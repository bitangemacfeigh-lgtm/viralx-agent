# interface.py
HTML_FRONTEND = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ViralX // Tech Stack Roaster</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'JetBrains Mono', monospace; }</style>
</head>
<body class="bg-[#09090b] text-[#fafafa] min-h-screen flex flex-col justify-between selection:bg-red-500 selection:text-white">
    <header class="border-b border-[#1f1f23] px-6 py-4 flex justify-between items-center max-w-4xl mx-auto w-full">
        <div class="flex items-center space-x-2">
            <span class="h-2.5 w-2.5 rounded-full bg-red-500 animate-pulse"></span>
            <h1 class="text-sm font-bold uppercase tracking-widest text-zinc-400">ViralX // Intelligence_Node</h1>
        </div>
        <span class="text-xs text-zinc-500 border border-zinc-800 rounded-full px-3 py-1 bg-zinc-900">v1.0.0-prod</span>
    </header>

    <main class="max-w-2xl mx-auto w-full px-6 py-12 flex-grow flex flex-col justify-center">
        <div class="text-center mb-8">
            <h2 class="text-3xl font-extrabold tracking-tighter bg-gradient-to-r from-white via-zinc-400 to-zinc-600 bg-clip-text text-transparent">
                Submit Your Architecture. Face Reality.
            </h2>
        </div>

        <div class="bg-[#121214] border border-[#1f1f23] rounded-xl p-6 shadow-2xl">
            <textarea id="userInput" rows="4" 
                class="w-full bg-[#18181b] border border-[#27272a] rounded-lg p-4 text-sm text-zinc-200 placeholder-zinc-600 focus:outline-none focus:border-red-500 transition-all duration-150 resize-none"
                placeholder="e.g., Python, FastAPI, raw SQL, deployed manually via SSH..."></textarea>
            
            <div class="mt-4 flex justify-end">
                <button onclick="triggerRoast()" id="runBtn"
                    class="bg-zinc-100 hover:bg-white text-black font-bold text-xs uppercase tracking-wider px-6 py-3 rounded-lg transition-all duration-150 active:scale-95">
                    Execute Analysis
                </button>
            </div>
        </div>

        <div id="resultCard" class="hidden mt-6 bg-[#121214] border-l-2 border-red-500 rounded-r-xl p-6 shadow-xl transition-all">
            <div class="flex justify-between items-center mb-4 pb-2 border-b border-zinc-800">
                <span class="text-xs uppercase tracking-widest text-red-400 font-bold">Analysis Feed</span>
                <button onclick="copyPayload()" class="text-xs text-zinc-400 hover:text-white underline">Copy Output</button>
            </div>
            <div id="resultText" class="text-sm leading-relaxed text-zinc-300 whitespace-pre-wrap"></div>
        </div>
    </main>

    <footer class="text-center py-6 border-t border-[#1f1f23] text-xs text-zinc-600">
        Engineered for rapid growth. Built on Mistral AI.
    </footer>

    <script>
        async function triggerRoast() {
            const text = document.getElementById('userInput').value;
            const btn = document.getElementById('runBtn');
            const card = document.getElementById('resultCard');
            const display = document.getElementById('resultText');
            
            if(!text.trim()) return alert('Field cannot be empty.');
            
            btn.disabled = true;
            btn.innerText = "COMPUTING INDEX...";
            card.classList.add('hidden');
            
            try {
                const res = await fetch('/api/roast', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ user_input: text })
                });
                const data = await res.json();
                if(res.ok) {
                    display.textContent = data.roast;
                    card.classList.remove('hidden');
                } else {
                    alert('Error: ' + data.detail);
                }
            } catch {
                alert('Network drop detected.');
            } finally {
                btn.disabled = false;
                btn.innerText = "Execute Analysis";
            }
        }
        function copyPayload() {
            navigator.clipboard.writeText(document.getElementById('resultText').textContent);
            alert('Copied to clipboard. Go viral!');
        }
    </script>
</body>
</html>
"""