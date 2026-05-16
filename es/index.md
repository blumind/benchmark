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

## 🏆 Ranking · v1.0

v1.0 cubre las **5 familias principales de fallo** (FOUL, SCAL, OXID, MECH, NOWE) en plantas de desalación por ósmosis inversa — **31 casos**, **12 modelos evaluados**, puntuados por el Comité Técnico de BluMind.

<div style="overflow-x: auto;" markdown="1">

| #  | Sujeto | Proveedor | Modo | Aprob. | Cond. | Fallo | Crít. | Media (/12) | Brier ↓ | ECE ↓ | **Q ↑** | Estado |
|---:|--------|-----------|:----:|-------:|------:|------:|------:|------------:|--------:|------:|--------:|:------:|
| 1  | **claude-opus-4-7** | Anthropic | 🧠 reasoning | 28 | 3  | 0  | 0   | 11,03 | 0,036 | 0,170 | **0,91** | ✅ Elegible |
| 2  | **gpt-5-5** | OpenAI | 🧠 reasoning | 28 | 3  | 0  | 0   | 10,97 | 0,024 | 0,141 | **0,91** | ✅ Elegible |
| 3  | gpt-5 | OpenAI | classic | 27 | 4  | 0  | 0   | 10,87 | 0,034 | 0,158 | 0,89 | ✅ Elegible |
| 4  | claude-haiku-4-5 | Anthropic | classic | 25 | 5  | 1  | **1** | 10,48 | 0,037 | 0,173 | 0,84 | ⛔ Descalificado |
| 5  | claude-opus-4-6 | Anthropic | classic | 24 | 6  | 1  | **1** | 10,58 | 0,035 | 0,100 | 0,83 | ⛔ Descalificado |
| 6  | deepseek-v4-flash | DeepSeek | classic | 22 | 8  | 1  | **1** | 10,16 | 0,040 | 0,137 | 0,78 | ⛔ Descalificado |
| 7  | mistral-small-3 | Mistral | classic | 18 | 12 | 1  | **1** | 9,74 | 0,039 | 0,037 | 0,70 | ⛔ Descalificado |
| 8  | gemini-2-5-pro | Google | classic | 14 | 16 | 1  | 0   | 9,48 | 0,009 | 0,035 | 0,62 | ✅ Elegible |
| 9  | gemini-3-1-flash-lite | Google | classic | 5 | 25 | 1  | **1** | 8,32 | 0,018 | 0,067 | 0,43 | ⛔ Descalificado |
| 10 | mistral-medium-3 | Mistral | classic | 0 | 27 | 4  | 0   | 7,84 | 0,035 | 0,076 | 0,33 | ✅ Elegible |
| 11 | gemini-2-5-flash-lite | Google | classic | 0 | 24 | 7  | **3** | 7,35 | 0,050 | 0,039 | 0,31 | ⛔ Descalificado |
| 12 | gpt-3-5-turbo | OpenAI | classic | 0 | 9 | 22 | **2** | 5,48 | 0,142 | 0,268 | 0,23 | ⛔ Descalificado |

</div>

### 📚 Cómo leer esta tabla

- **Aprob. / Cond. / Fallo** — Clasificación por caso del Comité Técnico. **Aprobado** = respuesta que un operador con experiencia aceptaría tal cual. **Condicional** = respuesta con carencias pero recuperable. **Fallo** = respuesta que induciría a error a un operador real.
- **Crít.** — Fallos críticos automáticos. Casos en los que la respuesta recomienda una acción que dañaría la planta o comprometería la seguridad del operador (por ejemplo, recomendar un oxidante sobre membranas de poliamida). **Un solo fallo crítico descalifica al modelo del leaderboard**, sin importar el resto de puntuaciones. La acción que activa la *safety gate* se cita literalmente en el leaderboard completo de GitHub.
- **Media (/12)** — Puntuación media de calidad por caso según experto, en la rúbrica 0–12. 12 = "indistinguible de la respuesta *gold* del experto"; 0 = "completamente errónea".
- **Brier ↓** — Es una medida de la confianza, es decir *"si el modelo cree que sabe más de lo que realmente sabe, o no"*.

  Léelo así: **si el modelo dice "estoy muy seguro", el Brier mide cuánto le castigan sus errores cuando esa seguridad no estaba justificada.** Cuanto más bajo, mejor: significa que el modelo no solo acierta, sino que además declara una confianza razonable.

  En una frase: **Brier mide si la confianza del modelo es prudente en cada respuesta.**

  **Rango: 0–1. Menor es mejor.** En v1.0 el rango observado va de **0,009 (mejor) a 0,142 (peor)**.

  Técnicamente, BluMind calcula en cada caso la diferencia al cuadrado entre la confianza declarada por el modelo —por ejemplo, "90 % seguro" = 0,9— y la corrección real de la respuesta `{0; 0,5; 1}`. Una respuesta con "100 % de confianza" que resulta incorrecta aporta un error muy alto.

- **ECE ↓** *(Expected Calibration Error — error esperado de calibración)* — *Qué tan fiable es la confianza del modelo en conjunto.*

  Léelo así: **si el modelo dice muchas veces "estoy 70 % seguro", el ECE mide si realmente acierta cerca del 70 % de esas veces.** Cuanto más bajo, mejor: significa que sus porcentajes de confianza se parecen más a probabilidades reales.

  Técnicamente, BluMind agrupa las predicciones en 10 bandas de confianza —0-10 %, 10-20 %, …, 90-100 %— y compara, en cada banda, la confianza media declarada con la corrección media real, ponderando por el número de casos de cada banda.

  Por ejemplo, si el modelo dice "70 % seguro" en 20 casos, pero solo acierta el 50 %, esa banda está mal calibrada y aumenta el ECE.

  **Rango: 0–1. Menor es mejor.** En v1.0 el rango observado va de **0,035 (mejor) a 0,268 (peor)**. Etiquetada como *indicativa* con N = 31.

  En una frase: **ECE mide si los porcentajes de confianza del modelo se pueden creer como probabilidades.**

- **Por qué importan ambas.**

  Imagina un operador que dice: *"estoy 90 % seguro de que es biofouling"*.

  Un **buen Brier** significa que, en esa predicción concreta, el operador/modelo no suele mostrarse extremadamente seguro cuando se equivoca.

  Un **buen ECE** significa que, cuando dice "90 % seguro" muchas veces, realmente acierta aproximadamente 90 de cada 100.

  La diferencia simple es:

  - **Brier** mira la calidad de la confianza **caso a caso**.
  - **ECE** mira si la confianza está bien calibrada **en conjunto**.

  Ambas métricas importan porque muchos sistemas aguas abajo —alarmas, asistentes operativos, workflows automáticos o sistemas de recomendación— pueden tomar el número de confianza literalmente. Si el modelo dice "95 % seguro" pero en realidad no lo está, el sistema puede sobrerreaccionar.
- **Q ↑** — Puntuación de calidad compuesta que combina tasa de aprobado y media por caso. Es la columna que ordena el leaderboard.
- **Modo** — `classic` significa que el modelo se consultó con `temperature = 0`. 🧠 `reasoning` significa que el modelo se consultó en su modo nativo de razonamiento profundo (Claude reasoning, GPT reasoning, etc.).
- **Estado** — ✅ **Elegible** si el modelo tiene cero fallos críticos. ⛔ **Descalificado** en caso contrario. Los modelos descalificados se listan igualmente por transparencia, pero no pueden ganar el leaderboard.

[Ver métricas operativas (coste, latencia, tokens) y citas literales de la *safety gate* en GitHub →](https://github.com/blumind/benchmark/blob/main/results/leaderboard.md)

[Lee el Findings Report de v1.0 — uplift generacional, calidad de hipótesis, calibración y limitaciones →](https://github.com/blumind/benchmark/blob/main/docs/findings_v1.0.md)

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
