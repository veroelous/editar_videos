def ph(t0, top, bot, t_end, step=0.11):
    """Frase de legenda: linha de ligação (branca) + linha forte (azul-céu); palavras entram uma a uma."""
    ws, t = [], t0
    for w in top.split(): ws.append((t, t + 0.3, w, False)); t += step
    for w in bot.split(): ws.append((t, t + 0.3, w, True)); t += step
    return (ws, t_end)
