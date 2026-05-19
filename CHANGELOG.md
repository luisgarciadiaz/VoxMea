# 📋 Changelog — VoxMea

Todos los cambios notables en este proyecto serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

---

## [0.1.0] — 2026-05-19

### Añadido
- 🎉 **Inicialización del proyecto** — Estructura base de VoxMea.
- 📁 Estructura de directorios:
  - `sources/` — Carpeta de ingesta para textos sin procesar.
    - `obsidian/` — Notas exportadas de Obsidian.
    - `emails/` — Correos exportados.
    - `articles/` — Artículos y posts.
  - `curated/` — Textos filtrados y clasificados.
    - Subcarpetas por tipo: `narrativo/`, `argumentativo/`, `informal/`, `tecnico/`.
  - `dataset/` — Dataset final para el LLM.
  - `scripts/` — Scripts de procesamiento Python.
  - `prompts/` — Prompts de sistema y plantillas.
  - `tests/` — Textos de control y resultados.
  - `docs/` — Documentación y logs.
- 📄 Documentación inicial:
  - `README.md` — Visión general del proyecto, fases y quickstart.
  - `agents.md` — Definición de 4 agentes: Curator, Analyst, Builder, Tester.
  - `architecture.md` — Arquitectura técnica, flujos de datos y decisiones de diseño.
  - `CHANGELOG.md` — Este archivo.
- 🔧 Archivo `.gitkeep` en directorios vacíos para preservar estructura en Git.

---

## Roadmap

### [0.2.0] — Fase 1: Extracción y Curación
- [ ] Script `curate.py` para filtrado automático de textos.
- [ ] Patrones regex para redacción de datos sensibles.
- [ ] Selección de texto de control.

### [0.3.0] — Fase 2: Formateo y Estructuración
- [ ] Script `build_dataset.py` para consolidación.
- [ ] Generación de `estilo_contexto.md`.
- [ ] (Opcional) Generación de `dataset.jsonl`.

### [0.4.0] — Fase 3: Integración y Pruebas
- [ ] Integración con Ollama / LM Studio.
- [ ] Configuración de RAG (Smart Connections).
- [ ] Suite de pruebas de generación.

### [1.0.0] — Release
- [ ] Pipeline completo y validado.
- [ ] Documentación final.
- [ ] Perfil de estilo refinado y aprobado.
