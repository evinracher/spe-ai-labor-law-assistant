// ─── MOCK BACKEND ────────────────────────────────────────────────────────────
const MOCK_ANSWERS: Record<number, string> = {
  0: `Según el Código Sustantivo del Trabajo colombiano, la liquidación de prestaciones sociales al término de un contrato laboral comprende los siguientes conceptos:

• **Prima de servicios:** equivalente a 15 días de salario por cada semestre trabajado o proporcional al tiempo laborado.
• **Cesantías:** un mes de salario por cada año de servicios o proporcional. Se liquidan con base en el último salario devengado.
• **Intereses a las cesantías:** 12% anual sobre el saldo de las cesantías, pagaderos en enero de cada año o al momento de la liquidación.
• **Vacaciones:** 15 días hábiles de descanso por cada año trabajado, o su equivalente en dinero si no se disfrutaron.

Para el cálculo, se toma como base el salario promedio del último año cuando este ha variado más del 10%. El empleador tiene un plazo máximo de 15 días hábiles contados desde la terminación del contrato para realizar el pago, so pena de incurrir en la sanción moratoria del artículo 65 del CST.`,
  1: `El contrato a término fijo en Colombia está regulado por el artículo 46 del Código Sustantivo del Trabajo. Sus características fundamentales son:

• **Duración:** mínimo 1 día, máximo 3 años. Puede renovarse indefinidamente, pero si se renueva más de tres veces por períodos iguales o inferiores a un año, el trabajador puede exigir que sea indefinido.
• **Preaviso de no renovación:** el empleador debe avisar con al menos 30 días de anticipación su intención de no renovar el contrato. De no hacerlo, el contrato se entiende renovado automáticamente.
• **Prestaciones sociales:** el trabajador tiene derecho a todas las prestaciones de ley (cesantías, prima, vacaciones, salud, pensión, ARL) de forma proporcional.
• **Terminación anticipada:** si el empleador termina el contrato antes del vencimiento sin justa causa, debe pagar los salarios correspondientes al tiempo que faltaba para cumplir el plazo pactado.

Este tipo de contrato es ideal para trabajos de temporada, proyectos específicos o para el período de prueba inicial en algunas empresas.`,
  2: `El despido con justa causa en Colombia está regulado por el artículo 62 del Código Sustantivo del Trabajo. Las causales más relevantes son:

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
};

export const mockResponse = async () => {
  const delay = 1200 + Math.random() * 600;
  await new Promise((resolve) => setTimeout(resolve, delay));

  const keys = Object.keys(MOCK_ANSWERS).map(Number);
  const idx = keys[Math.floor(Math.random() * keys.length)];
  const base = MOCK_ANSWERS[idx];

  const intros = [
    "Gracias por su consulta. A continuación le presento la información relevante:\n\n",
    "Con gusto le orientaré sobre este tema de derecho laboral colombiano:\n\n",
    "En el marco del ordenamiento jurídico laboral colombiano, encontramos lo siguiente:\n\n",
  ];
  const intro = intros[Math.floor(Math.random() * intros.length)];
  return intro + base;
}