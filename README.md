# editar_videos

Repositório com a skill [video-use](https://github.com/browser-use/video-use) instalada para edição de vídeos via Claude Code.

## Skill instalada

`.claude/skills/video-use/` — vendorizada a partir de `browser-use/video-use` (upstream). Traz:

- `SKILL.md` — regras de produção e fluxo de edição diário
- `install.md` — guia de instalação original
- `helpers/` — scripts de transcrição, empacotamento, timeline view, render e color grade
- `skills/manim-video/` — sub-skill para animações com Manim

Um hook `SessionStart` (`.claude/hooks/session-start.sh`) garante, em cada sessão remota do Claude Code, que `ffmpeg` e as dependências Python da skill (`uv sync`) estejam instaladas.

## Uso

1. Coloque as gravações brutas em uma pasta (fora de `.claude/`).
2. Abra uma sessão do Claude Code apontando para essa pasta, ou peça no chat para editar os vídeos.
3. Configure sua chave da ElevenLabs (necessária para transcrição):
   ```bash
   cp .claude/skills/video-use/.env.example .claude/skills/video-use/.env
   # edite .env e defina ELEVENLABS_API_KEY=...
   ```
   Chave disponível em https://elevenlabs.io/app/settings/api-keys — em sessões na web, defina como variável de ambiente do ambiente do Claude Code em vez de commitar o `.env`.
4. Peça para editar: "edita essas gravações num vídeo de lançamento" — a saída final vai para `<pasta>/edit/final.mp4`.

Veja `.claude/skills/video-use/SKILL.md` para as regras completas de produção.
