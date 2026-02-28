import type { Citation, WorkflowTrace } from "../app/types";

// ─── MOCK BACKEND ────────────────────────────────────────────────────────────
const MOCK_ANSWERS: Record<number, { text: string; citations: Citation[]; }> = {
  0: {
    text: `Según el Código Sustantivo del Trabajo colombiano, la liquidación de prestaciones sociales al término de un contrato laboral comprende los siguientes conceptos:

• **Prima de servicios:** equivalente a 15 días de salario por cada semestre trabajado o proporcional al tiempo laborado.
• **Cesantías:** un mes de salario por cada año de servicios o proporcional. Se liquidan con base en el último salario devengado.
• **Intereses a las cesantías:** 12% anual sobre el saldo de las cesantías, pagaderos en enero de cada año o al momento de la liquidación.
• **Vacaciones:** 15 días hábiles de descanso por cada año trabajado, o su equivalente en dinero si no se disfrutaron.

Para el cálculo, se toma como base el salario promedio del último año cuando este ha variado más del 10%. El empleador tiene un plazo máximo de 15 días hábiles contados desde la terminación del contrato para realizar el pago, so pena de incurrir en la sanción moratoria del artículo 65 del CST.`,
    citations: [
      {
        source: "CÓDIGO SUSTANTIVO DEL TRABAJO, Artículo 65",
        page: 45,
        chunk_id: "chunk_cst_65",
        snippet: "El pago de las prestaciones sociales debe realizarse dentro de quince (15) días hábiles contados desde la terminación del contrato"
      },
      {
        source: "DECRETO 1072 DE 2015, Artículo 2.2.8.8.1",
        page: 125,
        chunk_id: "chunk_1072_88_1",
        snippet: "La prima de servicios equivale a quince (15) días de salario por cada semestre trabajado"
      }
    ]
  },
  1: {
    text: `El contrato a término fijo en Colombia está regulado por el artículo 46 del Código Sustantivo del Trabajo. Sus características fundamentales son:

• **Duración:** mínimo 1 día, máximo 3 años. Puede renovarse indefinidamente, pero si se renueva más de tres veces por períodos iguales o inferiores a un año, el trabajador puede exigir que sea indefinido.
• **Preaviso de no renovación:** el empleador debe avisar con al menos 30 días de anticipación su intención de no renovar el contrato. De no hacerlo, el contrato se entiende renovado automáticamente.
• **Prestaciones sociales:** el trabajador tiene derecho a todas las prestaciones de ley (cesantías, prima, vacaciones, salud, pensión, ARL) de forma proporcional.
• **Terminación anticipada:** si el empleador termina el contrato antes del vencimiento sin justa causa, debe pagar los salarios correspondientes al tiempo que faltaba para cumplir el plazo pactado.

Este tipo de contrato es ideal para trabajos de temporada, proyectos específicos o para el período de prueba inicial en algunas empresas.`,
    citations: [
      {
        source: "CÓDIGO SUSTANTIVO DEL TRABAJO, Artículo 46",
        page: 28,
        chunk_id: "chunk_cst_46",
        snippet: "El contrato a término fijo debe constar por escrito y su duración no puede ser menor de un día ni mayor de tres años"
      },
      {
        source: "CÓDIGO SUSTANTIVO DEL TRABAJO, Artículo 47",
        page: 29,
        chunk_id: "chunk_cst_47",
        snippet: "El trabajador que labore en un contrato a término fijo por más de tres períodos iguales o inferiores a un año, puede exigir que el contrato sea a término indefinido"
      }
    ]
  },
  2: {
    text: `El despido con justa causa en Colombia está regulado por el artículo 62 del Código Sustantivo del Trabajo. Las causales más relevantes son:

**Por parte del empleador (causales para terminar el contrato):**
• Haber suministrado datos falsos al momento de la contratación.
• Actos de violencia, injuria, malos tratos o grave indisciplina contra el empleador, sus representantes, compañeros o familiares.
• Daño material grave causado intencionalmente o por negligencia al patrimonio del empleador.
• Incumplimiento grave de las obligaciones o prohibiciones especiales del contrato.
• Detención preventiva del trabajador por más de 30 días, o condena privativa de la libertad.
• Acoso laboral debidamente comprobado.

**Consideraciones importantes:**
• El despido con justa causa no genera obligación de pagar indemnización por despido.
• No obstante, el empleador **siempre** debe pagar las prestaciones sociales causadas (cesantías, primas, vacaciones).
• Es fundamental seguir el procedimiento disciplinario interno antes de ejecutar el despido, garantizando el derecho de defensa del trabajador (principio del debido proceso laboral).`,
    citations: [
      {
        source: "CÓDIGO SUSTANTIVO DEL TRABAJO, Artículo 62",
        page: 42,
        chunk_id: "chunk_cst_62",
        snippet: "Son causas para disolver el contrato de trabajo sin responsabilidad para el empleador: actos de violencia, injuria, malos tratos, grave indisciplina"
      },
      {
        source: "DECRETO 1072 DE 2015, Artículo 2.2.4.2.2",
        page: 89,
        chunk_id: "chunk_1072_4_2_2",
        snippet: "El acoso laboral como conducta persistente y demostrable, dirigida a infundir miedo e inseguridad o a lograr su desestabilización psicológica"
      }
    ]
  },
};

const mockWorkflowTrace = (): WorkflowTrace => {
  const conversationId = `conv_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
  const startTime = Date.now();
  
  return {
    conversation_id: conversationId,
    total_steps: 4,
    tools_used: ["classify_intent", "semantic_search", "generate_grounded_answer", "validate_answer"],
    tool_traces: [
      {
        tool_name: "classify_intent",
        status: "success",
        timestamp: new Date(startTime).toISOString(),
        duration_ms: 145,
        input: { query: "¿Qué son las prestaciones sociales?" },
        output: { intent: "domainSearch", confidence: 0.98 }
      },
      {
        tool_name: "semantic_search",
        status: "success",
        timestamp: new Date(startTime + 145).toISOString(),
        duration_ms: 312,
        input: { query: "prestaciones sociales", k: 4 },
        output: { documents_count: 4, top_score: 0.92 }
      },
      {
        tool_name: "generate_grounded_answer",
        status: "success",
        timestamp: new Date(startTime + 457).toISOString(),
        duration_ms: 1245,
        input: { context: "4 documentos", query: "¿Qué son las prestaciones sociales?" },
        output: { tokens_generated: 245, citations_used: 3 }
      },
      {
        tool_name: "validate_answer",
        status: "success",
        timestamp: new Date(startTime + 1702).toISOString(),
        duration_ms: 98,
        input: { answer: "...", context: "..." },
        output: { is_valid: true, hallucination_detected: false }
      }
    ],
    validation_passed: true,
    validation_details: {
      is_valid: true,
      coherence_score: 0.87,
      grounding_score: 0.91,
      hallucination_detected: false,
      completeness_score: 0.85,
      reason: "La respuesta está bien fundamentada en fuentes legales colombianas"
    },
    execution_time_ms: 1800,
    intent: "domainSearch"
  };
};

export const mockResponse = async () => {
  const delay = 1200 + Math.random() * 600;
  await new Promise((resolve) => setTimeout(resolve, delay));

  const keys = Object.keys(MOCK_ANSWERS).map(Number);
  const idx = keys[Math.floor(Math.random() * keys.length)];
  const { text, citations } = MOCK_ANSWERS[idx];

  const intros = [
    "Gracias por su consulta. A continuación le presento la información relevante:\n\n",
    "Con gusto le orientaré sobre este tema de derecho laboral colombiano:\n\n",
    "En el marco del ordenamiento jurídico laboral colombiano, encontramos lo siguiente:\n\n",
  ];
  const intro = intros[Math.floor(Math.random() * intros.length)];
  
  return {
    answer: intro + text,
    citations: citations,
    workflow_trace: mockWorkflowTrace()
  };
}
