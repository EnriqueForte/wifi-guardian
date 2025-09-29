# Interpretación del informe y respuesta ante hallazgos

Este documento explica cómo leer los informes generados por WiFi Guardian y qué acciones prácticas tomar.

---

## 1) Estructura del informe
- **Resumen (JSON)**: interfaz, red, nº total de dispositivos, *added/removed* respecto al baseline.
- **Anomalías**: lista de eventos relevantes a revisar (ARP cambios sospechosos, deauth, etc.).
- **Dispositivos detectados**: tabla con **IP**, **MAC**, **hostname** y **nota**.

Los informes se guardan como `reports/report-YYYYMMDD-HHMMSS.html` y `.md`.

---

## 2) Casos típicos y lectura rápida

### A) No hay anomalías y pocos cambios
- Situación normal; la red está estable.

### B) “Nuevos dispositivos”
- Puede ser un móvil/TV/IoT recién conectado o un intruso.
- **Acciones**:
  1. Verifica si reconoces el **hostname**.
  2. Mira el **fabricante** por OUI (prefijo MAC). *(Mejora futura)*
  3. Si no lo reconoces, **cambia la contraseña Wi‑Fi** y revisa clientes en tu router.

### C) “Dispositivos ausentes”
- Alguien que ya no está (normal si apagaste un equipo). Vigila si desaparecen equipos críticos.

### D) “ARP cambio sospechoso: IP -> MAC1 ahora MAC2”
- Indicio de **ARP spoofing** (posible Man‑in‑the‑Middle).
- **Acciones** (prioridad de fácil a robusto):
  1. Desconecta y reconecta tu equipo al Wi‑Fi.
  2. Reinicia router y **actualiza firmware**.
  3. Desactiva **WPS**; usa **WPA2** fuerte o **WPA3**.
  4. Activa **aislamiento de clientes** / segmenta invitados.
  5. Cambia contraseñas (Wi‑Fi y administración del router).
  6. Usa **VPN** en equipos sensibles o **cable** Ethernet.

### E) “Deauth frames totales: N” (Linux + monitor)
- **N alto** → posible ataque para expulsar clientes y capturar handshakes o sabotear.
- **Acciones**:
  1. Cambia **canal/banda** (2.4/5/6 GHz) y oculta SSID (obscurece, no asegura).
  2. Cambia **contraseña Wi‑Fi** y usa **WPA3** si es viable.
  3. Reduce potencia o reubica AP; valora **mesh** o varios AP.
  4. Monitoriza tendencias (picos horarios, repeticiones).

> ⚠️ Una **anomalía** no implica “hackeo” garantizado: confirma con el contexto (horario, quién estaba en casa, etc.).

---

## 3) Checklist de respuesta rápida (incidentes domésticos)

- [ ] ¿Reconozco todos los **hostnames** del informe?
- [ ] ¿Hay **MACs** desconocidas? (ver en el router lista de clientes)
- [ ] ¿Se repiten **ARP cambios** en el mismo IP a horas raras?
- [ ] ¿Aparecen **deauth** frecuentes durante días?
- [ ] ¿El **firmware** del router está actualizado?
- [ ] ¿Tengo **WPS desactivado**?
- [ ] ¿La **clave Wi‑Fi** es robusta (WPA2/3, 14+ chars, aleatoria)?
- [ ] ¿Uso **red de invitados** para IoT/visitas?
- [ ] ¿He cambiado la **password del panel** del router?

---

## 4) Buenas prácticas permanentes

- Usa **WPA2‑PSK fuerte** (o **WPA3** si compatible).
- Desactiva **WPS**.
- **Red de invitados** separada para IoT y visitas.
- **Actualizaciones** periódicas del router y dispositivos.
- Segmenta (VLAN) si tu equipo lo permite.
- Considera **DNS filtrado** (p.ej., NextDNS/AdGuard) para bloquear dominios maliciosos.

---

## 5) Limitaciones y falsos positivos

- **ARP spoof** se basa en observar cambios IP→MAC; failovers o cambios legítimos pueden parecer sospechosos.
- **Deauth** requiere hardware compatible y un entorno con tráfico 802.11; ausencia de eventos no implica seguridad total.
- No sustituye a soluciones corporativas (IDS/IPS/SIEM), es una capa de **visibilidad doméstica** y aprendizaje.

---

## 6) Próximos pasos recomendados (Roadmap)

- Detección de **Rogue AP / Evil Twin**: BSSID no visto, SSID duplicado con distinta OUI o RSSI atípico.
- Enriquecimiento por **OUI** (fabricante) y etiquetado de tipo de dispositivo.
- Exportación **PDF** de informes; envío de alertas a **Telegram/Discord**.
- GUI ligera y empaquetado (Windows .exe, Linux AppImage).

---

¿Dudas al interpretar un informe concreto? Guarda el HTML/MD y compárteme un extracto para orientarte.
