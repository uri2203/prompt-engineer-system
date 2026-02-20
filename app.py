<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Acceso Restringido | Sistema Modular</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-[#0f172a] h-screen flex items-center justify-center">
    <div class="bg-[#1e293b] p-8 rounded-2xl shadow-2xl border border-slate-700 w-96 text-center">
        <h2 class="text-blue-400 font-bold text-xl mb-6">ADMIN LOGIN</h2>
        <form action="/login" method="POST" class="space-y-4">
            <input type="text" name="username" placeholder="Usuario" class="w-full p-3 rounded-lg bg-[#0f172a] border border-slate-700 text-white outline-none focus:border-blue-500">
            <input type="password" name="password" placeholder="Contraseña" class="w-full p-3 rounded-lg bg-[#0f172a] border border-slate-700 text-white outline-none focus:border-blue-500">
            <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg transition-all shadow-lg shadow-blue-500/20">ENTRAR</button>
        </form>
    </div>
</body>
</html>
