# S3G4 LAB - Instrumentación de Laboratorio Portátil e Inalámbrica

Este proyecto está siendo desarrollado para el curso de **Proyecto Final de Carrera** de **Ingeniería Electrónica** en la **Universidad de Ingeniería y Tecnología (UTEC)**.

## Integrantes
*   **Urbizagastegui Fernández, Keneth Joseph**
*   **Chacón Fernández, William Roberto**

## Asesor
*   **Lozano Bravo, Miguel Angel**

---

## Descripción del Proyecto

**S3G4 LAB** es un prototipo de instrumentación de laboratorio autónomo y portátil que consolida en un solo dispositivo electrónico de mano los instrumentos clásicos de experimentación. El sistema está diseñado para ayudar a la realización de experimentos prácticos en cursos fundamentales de laboratorio como *Circuitos Eléctricos*, *Circuitos Analógicos*, y *Circuitos Eléctricos y Electrónicos* para estudiantes de primeros ciclos de las especialidades de **Ingeniería Electrónica** e **Ingeniería Mecatrónica**.

El dispositivo integra los siguientes instrumentos:
1.  **Osciloscopio Digital**: Visualización multicanal de señales en tiempo real con escalas de tiempo y voltaje configurables.
2.  **Generador de Funciones**: Generación de formas de onda (Senoidal, Triangular, PWM, Diente de Sierra, etc.) con amplitud y frecuencia controlables.
3.  **Multímetro Digital (En desarrollo)**: Medición de tensión DC con auto-rango mediante la integración en el coprocesador.

---

## Características de Conectividad

*   **Servidor Web Inalámbrico (Autónomo)**: El módulo principal (ESP32-S3) funciona como un punto de acceso o cliente de red (AP/STA) y aloja un servidor HTTP y WebSocket. Permite conectar laptops, tablets o celulares y abrir el cliente de control interactivo sin necesidad de redes de internet externas ni instalación de aplicaciones.
*   **Conexión a PC mediante Aplicación de Escritorio**: Capacidad de interactuar y transmitir telemetría en tiempo real a una computadora mediante una interfaz física serial (USB CDC).

---

## Arquitectura de Hardware y Software

El sistema utiliza una arquitectura de doble procesador para garantizar un alto rendimiento en tiempo real y una interfaz gráfica fluida:
*   **ESP32-S3**: Encargado de la interfaz de usuario en la pantalla TFT color mediante la biblioteca **LVGL (v9)**, procesamiento táctil, control del switch del transceptor Wi-Fi y streaming de datos vía WebSocket.
*   **STM32G473**: Coprocesador a cargo de la adquisición y digitalización de señales analógicas (ADC), control del convertidor digital-analógico (DAC) para el generador de ondas, y transmisión de alta velocidad hacia el ESP32 mediante interrupciones y DMA por bus SPI.

---

## Estructura del Repositorio

El repositorio está organizado en las siguientes carpetas de producción:
*   **[`firmware/`](./firmware)**: Códigos fuente de producción:
    *   `esp32_firmware/`: Proyecto de firmware ESP-IDF para el microcontrolador principal ESP32-S3.
    *   `stm32_firmware/`: Proyecto de firmware STM32 CubeIDE para el coprocesador STM32G473.
*   **[`hardware/`](./hardware)**: Diseño circuital del osciloscopio:
    *   Lista de materiales de ensamble (BOM).
    *   Esquema eléctrico completo en PDF.
    *   Imágenes descriptivas exportadas del esquemático por módulos (Alimentación, MCU, Adquisición, Display).
*   **[`software/`](./software)**: Aplicaciones de interfaz:
    *   `web_client/`: Aplicación web interactiva del osciloscopio en HTML5, React, Vite y TypeScript.

---

## Referencias

Este proyecto se basa y complementa su desarrollo utilizando recursos y flujos de los siguientes trabajos de código abierto:

*   [1] J. G. Peiró, "*black_scope: An open-source STM32 and ESP32 oscilloscope project*," GitHub repository. [En línea]. Disponible en: https://github.com/jgpeiro/black_scope
*   [2] P. Sury, "*EMBO: Embedded Oscilloscope desktop interface*," GitHub repository. [En línea]. Disponible en: https://github.com/psury/embo
*   [3] Digilent Inc., "*WaveForms Live and OpenScope MZ: Multi-function open-source instrument*," GitHub repository. [En línea]. Disponible en: https://github.com/Digilent/waveforms-live
