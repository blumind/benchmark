---
layout: default
title: BluMind Benchmark
description: El benchmark público de razonamiento de IA aplicado a la operación de plantas de tratamiento de agua.
permalink: /es/
lang: es
---

# BluMind Benchmark

**El benchmark público de razonamiento de IA aplicado a la operación de plantas de tratamiento de agua.**

BluMind evalúa modelos de IA sobre tareas reales de diagnóstico y razonamiento extraídas de la operación de plantas de tratamiento de agua. Cada respuesta es puntuada por el **Comité Técnico de BluMind** — profesionales senior e investigadores del sector del agua — contra un *gold standard* privado.

El benchmark es **público, reproducible y puntuado por humanos**. El leaderboard se actualiza a medida que se evalúan nuevos modelos y a medida que el Comité Técnico publica nuevos casos.

---

## Leaderboard · v1.0

v1.0 cubre las **5 familias principales de fallo** (FOUL, SCAL, OXID, MECH, NOWE) en plantas de desalación por ósmosis inversa — **31 casos**, **12 modelos evaluados**, puntuados por el Comité Técnico de BluMind.

| #  | Sujeto | Proveedor | Modo | Media (/12) | **Q ↑** | Estado |
|---:|--------|-----------|:----:|------------:|--------:|:------:|
| 1 | **claude-opus-4-7** | Anthropic | reasoning | 11,03 | **0,91** | Elegible |
| 2 | **gpt-5-5** | OpenAI | reasoning | 10,97 | **0,91** | Elegible |
| 3 | gpt-5 | OpenAI | classic | 10,87 | 0,89 | Elegible |
| 4 | claude-haiku-4-5 | Anthropic | classic | 10,48 | 0,84 | Descalificado |
| 5 | claude-opus-4-6 | Anthropic | classic | 10,58 | 0,83 | Descalificado |

*Top 5 por puntuación de calidad compuesta Q. Los modelos **descalificados** activaron la *safety gate* en al menos un caso.*

[Ver el leaderboard completo, métricas operativas y detalle de la *safety gate* en GitHub →](https://github.com/blumind/benchmark/blob/main/results/leaderboard.md)

---

## Qué hace diferente a BluMind

**Puntuación humana independiente.** Cada respuesta es puntuada por **dos miembros** del Comité Técnico de BluMind, seleccionados entre profesionales senior e investigadores del sector del agua. El comité es la autoridad institucional detrás de cada puntuación.

**Safety gate.** Una sola recomendación de fallo crítico — cualquier acción que dañaría la planta o comprometería la seguridad del operador — descalifica al modelo del leaderboard independientemente del resto de sus puntuaciones. La acción que activa la *safety gate* se cita literalmente y se hace pública.

**Reproducible.** Casos, rúbrica, prompts, scripts de evaluación y métricas agregadas son públicos. Las respuestas *gold* privadas y la correspondencia entre revisores se mantienen privadas — exactamente lo que cabe esperar de un benchmark fiable.

[Lee la metodología completa en GitHub →](https://github.com/blumind/benchmark/blob/main/docs/methodology.md)

---

## Enviar un modelo

Durante la **fase fundacional** (hasta el 31 de diciembre de 2026), las solicitudes válidas se evalúan **sin coste**. El remitente proporciona los metadatos, las credenciales de acceso técnico cifradas con la clave PGP de BluMind y confirma la elegibilidad respecto al alcance publicado.

Una solicitud se valida normalmente en **2 días laborables** y se evalúa en **10 días laborables** desde la validación.

[Lee la guía de envío en GitHub →](https://github.com/blumind/benchmark/blob/main/docs/submission_guide.md)

---

## El comité

El **Comité Técnico de BluMind** es el cuerpo de profesionales senior e investigadores responsable de la integridad del benchmark. Es la autoridad institucional detrás de cada puntuación, clasificación y decisión de apelación.

Entre sus miembros públicos figuran **Álvaro Díaz del Río Redondo** — CEO de BluMind, anteriormente Head of Innovation en Tedagua y Cobra Infraestructuras Hidráulicas — y **Rafael Jiménez Garrido** — Country Manager en Whitewater Group, profesor del Máster de Desalación y Reutilización de Aguas (Universidad de Alicante) y colaborador en ALADYR.

Tres figuras internacionales senior adicionales del sector del agua forman parte del comité; sus nombres están pendientes de divulgación pública.

[Conoce al comité en GitHub →](https://github.com/blumind/benchmark/blob/main/COMMITTEE.md)

---

## Contacto

- Envíos: [submissions@blumind.es](mailto:submissions@blumind.es) · [Clave pública PGP](https://github.com/blumind/benchmark/blob/main/system/keys/blumind-submissions.asc)
- Comité Técnico: [committee@blumind.es](mailto:committee@blumind.es)
- Consultas generales: [info@blumind.es](mailto:info@blumind.es)
- Repositorio: [github.com/blumind/benchmark](https://github.com/blumind/benchmark)

---

<p style="font-size: 0.85em; color: #122c4b;">BluMind Benchmark es operado por BluMind. El benchmark se publica bajo los términos de licencia indicados en <a href="https://github.com/blumind/benchmark/blob/main/LICENSE">LICENSE</a>.</p>
