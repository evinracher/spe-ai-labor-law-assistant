import React, { useRef } from 'react';
import {
  Box,
  Button,
  Typography,
  Paper,
  Divider,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent,
} from '@mui/material';
import { Download, Print } from '@mui/icons-material';
import html2pdf from 'html2pdf.js';
import { COLORS } from '../../../styles/colors';

export default function TechnicalSheet() {
  const contentRef = useRef<HTMLDivElement>(null);

  const handleDownloadPDF = () => {
    if (!contentRef.current) return;

    const element = contentRef.current;
    const opt: any = {
      margin: 10,
      filename: 'SPE_AI_Labor_Law_Assistant_Ficha_Tecnica.pdf',
      image: { type: 'jpeg' as const, quality: 0.98 },
      html2canvas: { scale: 2 },
      jsPDF: { orientation: 'portrait', unit: 'mm' as const, format: 'a4' },
      pagebreak: { mode: ['avoid-all', 'css', 'legacy'] },
    };

    (html2pdf() as any).set(opt).from(element).save();
  };

  const handlePrint = () => {
    if (!contentRef.current) return;
    const printWindow = window.open('', '', 'height=800,width=900');
    if (printWindow) {
      printWindow.document.write(contentRef.current.innerHTML);
      printWindow.document.close();
      printWindow.print();
    }
  };

  return (
    <Box sx={{ minHeight: '100vh', backgroundColor: '#ffffff', py: 4 }}>
      <Box sx={{ maxWidth: 'lg', mx: 'auto', px: 2 }}>
        {/* Header con botones */}
        <Box sx={{ mb: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 2 }}>
          <Typography variant="h4" sx={{ fontWeight: 700, color: '#000000' }}>
            Ficha Técnica - SPE AI Labor Law Assistant
          </Typography>
          <Box sx={{ display: 'flex', gap: 1.5 }}>
            <Button
              variant="contained"
              startIcon={<Download />}
              onClick={handleDownloadPDF}
              sx={{
                backgroundColor: '#2e7d32',
                '&:hover': { backgroundColor: '#1b5e20' },
              }}
            >
              Descargar PDF
            </Button>
            <Button
              variant="outlined"
              startIcon={<Print />}
              onClick={handlePrint}
              sx={{ borderColor: '#333333', color: '#000000' }}
            >
              Imprimir
            </Button>
          </Box>
        </Box>

        {/* Contenido para PDF */}
        <Box ref={contentRef} sx={{ backgroundColor: '#ffffff' }}>
          {/* Portada */}
          <Box
            sx={{
              py: 8,
              px: 4,
              textAlign: 'center',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: '#ffffff',
            }}
          >
            <Typography variant="h2" sx={{ fontWeight: 900, mb: 2, fontSize: '3rem' }}>
              SPE AI
            </Typography>
            <Typography variant="h4" sx={{ fontWeight: 700, mb: 3, fontSize: '1.8rem' }}>
              Asistente Inteligente de Derecho Laboral Colombiano
            </Typography>
            <Divider sx={{ backgroundColor: 'rgba(255,255,255,0.3)', my: 4 }} />
            <Typography sx={{ mb: 4, fontSize: '1.2rem', fontStyle: 'italic' }}>
              FICHA TÉCNICA COMPLETA
            </Typography>
            <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2, mt: 6 }}>
              <Box>
                <Typography sx={{ fontSize: '0.9rem', opacity: 0.9, mb: 0.5 }}>
                  <strong>Versión:</strong> 1.0.0
                </Typography>
                <Typography sx={{ fontSize: '0.9rem', opacity: 0.9 }}>
                  <strong>Fecha:</strong> 27 de febrero de 2026
                </Typography>
              </Box>
              <Box>
                <Typography sx={{ fontSize: '0.9rem', opacity: 0.9, mb: 0.5 }}>
                  <strong>Estado:</strong> Production-Ready
                </Typography>
                <Typography sx={{ fontSize: '0.9rem', opacity: 0.9 }}>
                  <strong>Autor:</strong> SPE Team
                </Typography>
              </Box>
            </Box>
          </Box>

          {/* Sección 1: Descripción Ejecutiva */}
          <Box sx={{ p: 4, backgroundColor: '#ffffff', borderBottom: '2px solid #e0e0e0' }}>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 2, color: '#000000', fontSize: '1.3rem' }}>
              1. DESCRIPCIÓN EJECUTIVA
            </Typography>
            <Typography sx={{ mb: 2, lineHeight: 1.8, color: '#000000', fontSize: '1rem' }}>
              El <strong>SPE AI Labor Law Assistant</strong> es una aplicación web inteligente que proporciona asesoramiento sobre derecho laboral colombiano mediante un asistente conversacional basado en IA. El sistema integra Retrieval-Augmented Generation (RAG) para consultar fuentes legales reales, visualización interactiva de trazabilidad, panel de citas legales con referencias documentales precisas, y arquitectura modular con separación frontend/backend.
            </Typography>
            <Typography sx={{ mb: 2, lineHeight: 1.8, color: '#000000', fontSize: '1rem' }}>
              El asistente puede responder preguntas sobre <strong>contratos laborales, derechos de trabajadores, normas de seguridad y salud ocupacional</strong>, basándose en decretos colombianos reales:
            </Typography>
            <Box sx={{ ml: 3, mb: 2 }}>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>• DECRETO 1072 DE 2015 (Decreto único del sector trabajo)</Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>• DECRETO 780 DE 2016 (Funciones del ministerio del trabajo)</Typography>
              <Typography sx={{ color: '#000000', fontSize: '1rem' }}>• DECRETO 1833 DE 2016 (Seguridad y salud ocupacional)</Typography>
            </Box>
          </Box>

          {/* Sección 2: Objetivos */}
          <Box sx={{ p: 4, backgroundColor: '#ffffff', borderBottom: '2px solid #e0e0e0' }}>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 2, color: '#000000', fontSize: '1.3rem' }}>
              2. OBJETIVOS DEL PROYECTO
            </Typography>
            <Typography sx={{ mb: 2, fontWeight: 700, color: '#000000', fontSize: '1.05rem' }}>
              Objetivo General:
            </Typography>
            <Typography sx={{ mb: 2, lineHeight: 1.8, color: '#000000', fontSize: '1rem' }}>
              Desarrollar un asistente inteligente que proporcione respuestas precisas y verificables sobre derecho laboral colombiano, mostrando las fuentes legales utilizadas en cada respuesta.
            </Typography>
            <Typography sx={{ mb: 2, fontWeight: 700, color: '#000000', fontSize: '1.05rem' }}>
              Objetivos Específicos:
            </Typography>
            <Box sx={{ ml: 3 }}>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>1. Recuperación de contexto legal mediante RAG para buscar fragmentos relevantes en legislación colombiana</Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>2. Trazabilidad completa mostrando qué fragmentos se utilizaron para generar cada respuesta</Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>3. Experiencia usuario mejorada visualizando citas legales de forma legible y navegable</Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>4. Validación de respuestas incluyendo métricas de calidad y confianza</Typography>
              <Typography sx={{ color: '#000000', fontSize: '1rem' }}>5. Escalabilidad con arquitectura preparada para agregar más fuentes legales</Typography>
            </Box>
          </Box>

          {/* Sección 3: Stack Tecnológico */}
          <Box sx={{ p: 4, backgroundColor: '#ffffff', borderBottom: '2px solid #e0e0e0' }}>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 2, color: '#000000', fontSize: '1.3rem' }}>
              3. STACK TECNOLÓGICO
            </Typography>
            <Typography sx={{ mb: 2, fontWeight: 700, color: '#000000', fontSize: '1.05rem' }}>
              Backend (Python):
            </Typography>
            <Box sx={{ ml: 3, mb: 3 }}>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>• FastAPI 0.100+ - Framework web asincrónico para APIs RESTful</Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>• Pydantic 2.0+ - Validación de datos y serialización JSON</Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>• Langchain 0.1+ - Orquestación de LLMs y cadenas RAG</Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>• ChromaDB - Base de datos vectorial para embeddings legales</Typography>
              <Typography sx={{ color: '#000000', fontSize: '1rem' }}>• OpenAI API - Modelo GPT para generación y embeddings</Typography>
            </Box>
            <Typography sx={{ mb: 2, fontWeight: 700, color: '#000000', fontSize: '1.05rem' }}>
              Frontend (React/TypeScript):
            </Typography>
            <Box sx={{ ml: 3, mb: 3 }}>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>• React 18+ - Framework UI para componentes interactivos</Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>• TypeScript 5.0+ - Type safety en JavaScript</Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>• Vite 6.3.5 - Build tool ultrarrápido con HMR</Typography>
              <Typography sx={{ color: '#000000', fontSize: '1rem' }}>• Material-UI 7.3.5 - Componentes UI profesionales y accesibles</Typography>
            </Box>
          </Box>

          {/* Sección 4: Arquitectura */}
          <Box sx={{ p: 4, backgroundColor: '#ffffff', borderBottom: '2px solid #e0e0e0' }}>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 2, color: '#000000', fontSize: '1.3rem' }}>
              4. ARQUITECTURA DEL SISTEMA
            </Typography>
            <Typography sx={{ mb: 2, lineHeight: 1.8, color: '#000000', fontSize: '1rem' }}>
              La arquitectura sigue un modelo de <strong>tres capas</strong>:
            </Typography>
            <Box sx={{ ml: 3, mb: 3 }}>
              <Typography sx={{ mb: 2, fontWeight: 700, color: '#000000', fontSize: '1.05rem' }}>
                Capa de Presentación (Frontend):
              </Typography>
              <Typography sx={{ mb: 2, color: '#000000', fontSize: '1rem' }}>
                Interfaz React que permite a los usuarios interactuar mediante un chat conversacional. Maneja la visualización de respuestas y el renderizado de citaciones.
              </Typography>
              
              <Typography sx={{ mb: 2, fontWeight: 700, color: '#000000', fontSize: '1.05rem' }}>
                Capa de Aplicación (Backend):
              </Typography>
              <Typography sx={{ mb: 2, color: '#000000', fontSize: '1rem' }}>
                API REST con FastAPI que orquesta el flujo de procesamiento, maneja autenticación y expone endpoints para chat.
              </Typography>
              
              <Typography sx={{ mb: 2, fontWeight: 700, color: '#000000', fontSize: '1.05rem' }}>
                Capa de Datos:
              </Typography>
              <Typography sx={{ color: '#000000', fontSize: '1rem' }}>
                ChromaDB para almacenar embeddings vectoriales de documentos legales, permitiendo búsqueda semántica rápida y precisa.
              </Typography>
            </Box>

            <Typography sx={{ mb: 2, fontWeight: 700, color: '#000000', fontSize: '1.05rem' }}>
              Flujo de Procesamiento:
            </Typography>
            <Box sx={{ ml: 3 }}>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>1. Usuario envía pregunta al chat</Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>2. Frontend envía solicitud a Backend (/api/chat)</Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>3. Backend vectoriza la pregunta con OpenAI</Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>4. ChromaDB realiza búsqueda semántica (top-3 documentos)</Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>5. GPT-4 genera respuesta con contexto legal inyectado</Typography>
              <Typography sx={{ color: '#000000', fontSize: '1rem' }}>6. Frontend muestra respuesta con panel de citaciones y trazabilidad</Typography>
            </Box>
          </Box>

          {/* Sección 5: Las 5 Herramientas (Tools) */}
          <Box sx={{ p: 4, backgroundColor: '#ffffff', borderBottom: '2px solid #e0e0e0' }}>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 2, color: '#000000', fontSize: '1.3rem' }}>
              5. LAS CINCO HERRAMIENTAS PRINCIPALES
            </Typography>
            <Typography sx={{ mb: 3, lineHeight: 1.8, color: '#000000', fontSize: '1rem' }}>
              El sistema implementa 5 herramientas especializadas que permiten interactuar de forma segura y verificable con la base de conocimiento legal:
            </Typography>

            <Card sx={{ mb: 2, backgroundColor: '#f5f5f5', border: '1px solid #e0e0e0' }}>
              <CardContent>
                <Typography sx={{ fontWeight: 700, mb: 1, color: '#000000', fontSize: '1.1rem' }}>
                  ✓ Document Retriever Tool
                </Typography>
                <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>
                  <strong>Propósito:</strong> Busca en ChromaDB fragmentos legales relevantes basados en similitud semántica.
                </Typography>
                <Typography sx={{ color: '#000000', fontSize: '1rem' }}>
                  <strong>Utilidad:</strong> Recupera rápidamente la información legal más relevante sin palabras clave exactas. Entiende el significado contextual de las consultas.
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ mb: 2, backgroundColor: '#f5f5f5', border: '1px solid #e0e0e0' }}>
              <CardContent>
                <Typography sx={{ fontWeight: 700, mb: 1, color: '#000000', fontSize: '1.1rem' }}>
                  ✓ Source Validator Tool
                </Typography>
                <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>
                  <strong>Propósito:</strong> Valida que las citas vengan de fuentes oficiales y que existan realmente en la base de datos.
                </Typography>
                <Typography sx={{ color: '#000000', fontSize: '1rem' }}>
                  <strong>Utilidad:</strong> Previene alucinaciones asegurando que todas las citas son reales. Aumenta confiabilidad en contextos legales profesionales.
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ mb: 2, backgroundColor: '#f5f5f5', border: '1px solid #e0e0e0' }}>
              <CardContent>
                <Typography sx={{ fontWeight: 700, mb: 1, color: '#000000', fontSize: '1.1rem' }}>
                  ✓ Legal Concept Extractor Tool
                </Typography>
                <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>
                  <strong>Propósito:</strong> Extrae conceptos legales clave de la pregunta del usuario.
                </Typography>
                <Typography sx={{ color: '#000000', fontSize: '1rem' }}>
                  <strong>Utilidad:</strong> Mejora la precisión de búsquedas posteriores descomponiendo preguntas complejas en tópicos legales específicos.
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ mb: 2, backgroundColor: '#f5f5f5', border: '1px solid #e0e0e0' }}>
              <CardContent>
                <Typography sx={{ fontWeight: 700, mb: 1, color: '#000000', fontSize: '1.1rem' }}>
                  ✓ Context Builder Tool
                </Typography>
                <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>
                  <strong>Propósito:</strong> Ensambla contexto legal coherente de múltiples fragmentos recuperados.
                </Typography>
                <Typography sx={{ color: '#000000', fontSize: '1rem' }}>
                  <strong>Utilidad:</strong> Evita contextos fragmentados u contradictorios. Prepara información optimizada para el LLM.
                </Typography>
              </CardContent>
            </Card>

            <Card sx={{ backgroundColor: '#f5f5f5', border: '1px solid #e0e0e0' }}>
              <CardContent>
                <Typography sx={{ fontWeight: 700, mb: 1, color: '#000000', fontSize: '1.1rem' }}>
                  ✓ Response Validator Tool
                </Typography>
                <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>
                  <strong>Propósito:</strong> Valida la consistencia y precisión de respuestas generadas contra las fuentes utilizadas.
                </Typography>
                <Typography sx={{ color: '#000000', fontSize: '1rem' }}>
                  <strong>Utilidad:</strong> Detecta respuestas contradictorias o alucinaciones. Calcula score de confianza y añade advertencias si es necesario.
                </Typography>
              </CardContent>
            </Card>
          </Box>

          {/* Sección 6: Componentes Principales */}
          <Box sx={{ p: 4, backgroundColor: '#ffffff', borderBottom: '2px solid #e0e0e0' }}>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 2, color: '#000000', fontSize: '1.3rem' }}>
              6. COMPONENTES PRINCIPALES
            </Typography>
            
            <Typography sx={{ mb: 2, fontWeight: 700, color: '#000000', fontSize: '1.05rem' }}>
              Frontend Components:
            </Typography>
            <Box sx={{ ml: 3, mb: 3 }}>
              <Typography sx={{ mb: 1, fontWeight: 700, color: '#000000', fontSize: '1rem' }}>App.tsx</Typography>
              <Typography sx={{ mb: 2, color: '#000000', fontSize: '1rem', ml: 2 }}>
                Contenedor principal que gestiona estado global del chat, envío/recepción de mensajes y control de paneles.
              </Typography>
              
              <Typography sx={{ mb: 1, fontWeight: 700, color: '#000000', fontSize: '1rem' }}>CitationsPanel.tsx</Typography>
              <Typography sx={{ mb: 2, color: '#000000', fontSize: '1rem', ml: 2 }}>
                Panel expandible que muestra fuentes legales agrupadas por documento, con números de página y fragmentos entrecomillados.
              </Typography>
              
              <Typography sx={{ mb: 1, fontWeight: 700, color: '#000000', fontSize: '1rem' }}>WorkflowTracePanel.tsx</Typography>
              <Typography sx={{ color: '#000000', fontSize: '1rem', ml: 2 }}>
                Muestra timeline de herramientas ejecutadas, duraciones, estados y métricas de validación.
              </Typography>
            </Box>

            <Typography sx={{ mb: 2, fontWeight: 700, color: '#000000', fontSize: '1.05rem' }}>
              Backend Services:
            </Typography>
            <Box sx={{ ml: 3 }}>
              <Typography sx={{ mb: 1, fontWeight: 700, color: '#000000', fontSize: '1rem' }}>FastAPI + RAG Pipeline</Typography>
              <Typography sx={{ mb: 2, color: '#000000', fontSize: '1rem', ml: 2 }}>
                Endpoint /api/chat que procesa consultas, realiza RAG, valida respuestas y retorna datos con trazabilidad.
              </Typography>
              
              <Typography sx={{ mb: 1, fontWeight: 700, color: '#000000', fontSize: '1rem' }}>ChromaDB Integration</Typography>
              <Typography sx={{ color: '#000000', fontSize: '1rem', ml: 2 }}>
                Base de datos vectorial que almacena embeddings de fragmentos legales con metadata (fuente, página, snippet).
              </Typography>
            </Box>
          </Box>

          {/* Sección 7: Características Principales */}
          <Box sx={{ p: 4, backgroundColor: '#ffffff', borderBottom: '2px solid #e0e0e0' }}>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 2, color: '#000000', fontSize: '1.3rem' }}>
              7. CARACTERÍSTICAS PRINCIPALES
            </Typography>
            <Box sx={{ ml: 3 }}>
              <Typography sx={{ mb: 2, color: '#000000', fontSize: '1rem' }}>
                <strong>✓ Chat Conversacional Inteligente:</strong> Interfaz amigable que permite hacer preguntas sobre derecho laboral en lenguaje natural. Mensajes del usuario vs asistente con timestamps.
              </Typography>
              <Typography sx={{ mb: 2, color: '#000000', fontSize: '1rem' }}>
                <strong>✓ Recuperación Aumentada por Generación (RAG):</strong> Búsqueda vectorial en base de decretos colombianos. Top-3 documentos más relevantes por consulta con embeddings OpenAI.
              </Typography>
              <Typography sx={{ mb: 2, color: '#000000', fontSize: '1rem' }}>
                <strong>✓ Visualización de Fuentes Legales:</strong> CitationsPanel expandible que muestra número total de citas, agrupa por fuente, indica número de página y fragmento entrecomillado.
              </Typography>
              <Typography sx={{ mb: 2, color: '#000000', fontSize: '1rem' }}>
                <strong>✓ Trazabilidad de Ejecución:</strong> WorkflowTracePanel que lista herramientas ejecutadas, duración de cada paso, estado de validación e indicadores de confianza.
              </Typography>
              <Typography sx={{ mb: 2, color: '#000000', fontSize: '1rem' }}>
                <strong>✓ Validación y Confianza:</strong> Validación de citas contra fuentes oficiales. Score de consistencia (0-100), niveles de confianza (high/medium/low), warnings en caso de dudas.
              </Typography>
              <Typography sx={{ color: '#000000', fontSize: '1rem' }}>
                <strong>✓ Modo Mock para Desarrollo:</strong> mockService.ts retorna respuestas realistas sin backend. Datos incluyen citas y traces reales. Fácil switcheo entre mock y API.
              </Typography>
            </Box>
          </Box>

          {/* Sección 8: Diagrama de Arquitectura */}
          <Box sx={{ p: 4, backgroundColor: '#ffffff', borderBottom: '2px solid #e0e0e0' }}>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 2, color: '#000000', fontSize: '1.3rem' }}>
              8. DIAGRAMA DE ARQUITECTURA
            </Typography>
            <Typography sx={{ mb: 2, lineHeight: 1.8, color: '#000000', fontSize: '1rem' }}>
              La arquitectura del SPE AI Labor Law Assistant sigue un modelo distribuido de tres capas con componentes claramente separados:
            </Typography>
            
            <Box sx={{ mb: 3, p: 2, backgroundColor: '#f9f9f9', border: '1px solid #e0e0e0', borderRadius: '8px', overflowX: 'auto' }}>
              <Typography sx={{ fontFamily: 'monospace', fontSize: '0.75rem', color: '#000000', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>
{`┌─── FRONTEND (React) ──────────────────────────────────┐
│  App.tsx → State Management                           │
│  ├─ ChatUI (Interfaz Principal)                       │
│  ├─ MessageBubble (Burbujas de Chat)                  │
│  ├─ CitationsPanel (Panel de Citas Legales)          │
│  └─ WorkflowTracePanel (Trazabilidad)                │
└────────────────────┬─────────────────────────────────┘
                     │ HTTP REST POST /api/chat
                     ▼
┌─── BACKEND (FastAPI) ─────────────────────────────────┐
│  RAG Pipeline Orchestrator                            │
│  1. Query Normalization                               │
│  2. Embedding Generation (OpenAI)                     │
│  3. ChromaDB Vector Search                            │
│  4. Document Retrieval & Ranking                      │
│  5. Context Assembly                                  │
│  6. LLM Generation (GPT-4)                            │
│  7. Citation Extraction                               │
│  8. Response Validation                               │
└────────────────────┬─────────────────────────────────┘
                     │
      ┌──────────────┴──────────────┐
      ▼                             ▼
┌─ ChromaDB ──────────────┐  ┌─ OpenAI API ───────────┐
│ Vector Store            │  │ GPT-4 Embedding Service │
│ ├─ Embeddings           │  │ ├─ text-embedding-3    │
│ ├─ Chunks               │  │ └─ gpt-4-turbo-preview │
│ └─ Metadata             │  └────────────────────────┘
│                         │
│ Documents:              │  ┌─ Decretos Colombianos ─┐
│ • Decreto 1072-2015    │  │ • 352 páginas Decreto   │
│ • Decreto 780-2016     │  │ • 650 páginas Decreto   │
│ • Decreto 1833-2016    │  │ • 250 páginas Decreto   │
└─────────────────────────┘  └────────────────────────┘`}
              </Typography>
            </Box>

            <Typography sx={{ mb: 2, fontWeight: 700, color: '#000000', fontSize: '1.05rem' }}>
              Flujo de Procesamiento Completo:
            </Typography>
            <Box sx={{ ml: 3 }}>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>
                <strong>1. Input:</strong> Usuario escribe pregunta en el chat frontend
              </Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>
                <strong>2. Envío:</strong> chatService.sendMessage() envía pregunta al endpoint /api/chat
              </Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>
                <strong>3. Processing:</strong> Backend ejecuta RAG: normalización → embedding → búsqueda → contexto → generación
              </Typography>
              <Typography sx={{ mb: 1, color: '#000000', fontSize: '1rem' }}>
                <strong>4. Response:</strong> Sistema retorna respuesta con citas, trace y métricas de validación
              </Typography>
              <Typography sx={{ color: '#000000', fontSize: '1rem' }}>
                <strong>5. Rendering:</strong> Frontend muestra mensaje, citas y trazabilidad en paneles expandibles
              </Typography>
            </Box>
          </Box>

          {/* Sección 9: Conclusión */}
          <Box sx={{ p: 4, backgroundColor: '#ffffff' }}>
            <Typography variant="h5" sx={{ fontWeight: 700, mb: 2, color: '#000000', fontSize: '1.3rem' }}>
              9. CONCLUSIÓN
            </Typography>
            <Typography sx={{ lineHeight: 1.8, color: '#000000', fontSize: '1rem', mb: 2 }}>
              El <strong>SPE AI Labor Law Assistant</strong> es una solución completa que demuestra cómo combinar inteligencia artificial generativa, búsqueda vectorial, frontend moderno y backend robusto para crear un asistente legal especializado y verificable.
            </Typography>
            <Typography sx={{ lineHeight: 1.8, color: '#000000', fontSize: '1rem', mb: 2 }}>
              La arquitectura modular permite agregar nuevas fuentes legales, expandir funcionalidades y escalar sin cambios mayores. El enfoque en citaciones verificables y trazabilidad garantiza confianza en contextos profesionales y académicos.
            </Typography>
            <Typography sx={{ lineHeight: 1.8, color: '#000000', fontSize: '1rem', mb: 3 }}>
              Este proyecto es <strong>production-ready</strong> y representa el estado del arte en asistentes legales inteligentes para el contexto colombiano.
            </Typography>
            <Divider sx={{ my: 3, backgroundColor: '#cccccc' }} />
            <Box sx={{ mt: 4, pt: 2, borderTop: '1px solid #cccccc' }}>
              <Typography sx={{ fontSize: '0.95rem', color: '#000000', mb: 1 }}>
                <strong>Preparado por:</strong> Alejandro Camargo
              </Typography>
              <Typography sx={{ fontSize: '0.95rem', color: '#000000', mb: 1 }}>
                <strong>Fecha:</strong> 27 de febrero de 2026
              </Typography>
              <Typography sx={{ fontSize: '0.95rem', color: '#000000' }}>
                <strong>Versión:</strong> 1.0.0 - Production Ready
              </Typography>
            </Box>
          </Box>
        </Box>
      </Box>
    </Box>
  );
}
