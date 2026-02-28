# 📋 Ficha Técnica - SPE AI Labor Law Assistant

## Acceso a la Ficha Técnica

La ficha técnica del proyecto está disponible de dos maneras:

### 1. **Desde la UI del Chat** (Recomendado)
- Haz clic en el icono **📄** (Description) en la esquina superior derecha del header
- Se abrirá un modal con la ficha técnica completa
- Desde ahí puedes:
  - **Descargar como PDF**: Botón verde "Descargar PDF"
  - **Imprimir**: Botón "Imprimir" para enviar a impresora

### 2. **Directamente desde el navegador**
- Navega a: `http://localhost:5173/technical-sheet`
- Se abre la página completa con todos los controles

---

## 📄 Contenido de la Ficha Técnica

La ficha técnica incluye:

### 1. **Descripción Ejecutiva**
- Resumen del proyecto
- Objetivos principales
- Tecnologías utilizadas

### 2. **Stack Tecnológico**
- **Backend**: FastAPI, Pydantic, Langchain, ChromaDB, OpenAI API
- **Frontend**: React 18, TypeScript, Vite, Material-UI

### 3. **Arquitectura del Sistema**
- Diagrama de componentes
- Flujo de datos en una consulta
- Componentes frontend y backend

### 4. **Herramientas Implementadas (5 Tools)**
1. **Document Retriever** - Búsqueda vectorial
2. **Source Validator** - Validación de citas
3. **Legal Concept Extractor** - Extracción de conceptos
4. **Context Builder** - Construcción de contexto
5. **Response Validator** - Validación de respuestas

### 5. **Estructuras de Datos**
- Message, Citation, Trace, WorkflowTrace
- Esquemas Pydantic del API

### 6. **Características Principales**
- Chat conversacional
- RAG (Retrieval-Augmented Generation)
- Visualización de fuentes legales
- Trazabilidad de ejecución
- Validación y confianza

### 7. **Métricas de Calidad**
| Métrica | Objetivo |
|---------|----------|
| Relevance Score | > 0.75 |
| Consistency Score | > 0.85 |
| Citation Accuracy | 100% |
| Response Time | < 3s |
| Hallucination Rate | < 5% |

### 8. **Fuentes Legales Integradas**
- DECRETO 1072 DE 2015 (Decreto único del sector trabajo)
- DECRETO 780 DE 2016 (Funciones del ministerio del trabajo)
- DECRETO 1833 DE 2016 (Seguridad y salud ocupacional)

---

## 🔍 Características de Visualización

### Botones de Control
- **Descargar PDF**: Genera un PDF profesional de toda la ficha técnica
- **Imprimir**: Abre el diálogo de impresión del navegador

### Diseño Responsivo
- Optimizado para desktop, tablet y móvil
- Colores profesionales (gradientes azul-púrpura)
- Tipografía clara y legible

### Exportación a PDF
- Mantiene el formato y estructura
- Incluye tablas formateadas
- Soporta saltos de página automáticos
- Márgenes profesionales (10mm)

---

## 📊 Implementación Técnica

### Componente Principal
**Archivo**: `/src/app/components/ui/technical-sheet.tsx`

```typescript
// Funcionalidad de descarga PDF
const handleDownloadPDF = () => {
  // Usa html2pdf.js para convertir DOM a PDF
  // Genera archivo: SPE_AI_Labor_Law_Assistant_Ficha_Tecnica.pdf
}

// Funcionalidad de impresión
const handlePrint = () => {
  // Abre ventana de impresión del navegador
}
```

### Integración en Header
**Archivo**: `/src/app/components/ui/header.tsx`

```typescript
// Botón en header para abrir modal
<IconButton onClick={() => setOpenTechnicalSheet(true)}>
  <DescriptionIcon />
</IconButton>

// Modal que contiene TechnicalSheet
<Dialog open={openTechnicalSheet}>
  <TechnicalSheet />
</Dialog>
```

---

## 🎨 Estilos

### Colores
- **Principal**: #667eea (azul)
- **Secundario**: #764ba2 (púrpura)
- **Texto**: COLORS.textOnLightPrimary
- **Fondo**: #f5f5f5

### Tipografía
- **Encabezados**: fontWeight: 700
- **Contenido**: fontSize: 0.9rem
- **Código**: fontFamily: 'monospace'

---

## 📦 Dependencias

### npm install html2pdf.js

```bash
npm install html2pdf.js
```

Proporciona:
- Conversión DOM → Canvas → PDF
- Soporte para tablas y contenido complejo
- Control de márgenes y tamaño de página

---

## 🚀 Uso

### Descarga desde UI
1. Abre el chat en `localhost:5173`
2. Haz clic en el icono de documento (📄) en el header
3. Haz clic en "Descargar PDF"
4. Se descargará: `SPE_AI_Labor_Law_Assistant_Ficha_Tecnica.pdf`

### Impresión
1. Abre la ficha técnica (modal o página)
2. Haz clic en "Imprimir"
3. Selecciona destino (impresora, PDF, etc.)
4. Configura opciones y imprime

### Acceso directo
- URL: `http://localhost:5173/technical-sheet`
- Requiere React Router configurado

---

## ✅ Checklist

- [x] Componente TechnicalSheet creado
- [x] Integración con header
- [x] Modal de visualización
- [x] Funcionalidad de descarga PDF
- [x] Funcionalidad de impresión
- [x] Estilos responsivos
- [x] Contenido completo (9 secciones)
- [x] Sin errores TypeScript
- [x] Página standalone (opcional)

---

## 🔗 Archivos Relacionados

- **Ficha técnica en MD**: `/fiche_tecnica.md`
- **Componente**: `/src/app/components/ui/technical-sheet.tsx`
- **Header**: `/src/app/components/ui/header.tsx`
- **Página standalone**: `/src/app/TechnicalSheetPage.tsx`

---

**Última actualización**: 27 de febrero de 2026  
**Versión**: 1.0.0
