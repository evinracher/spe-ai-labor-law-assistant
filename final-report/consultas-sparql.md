# Documentación de Consultas SPARQL — Asistente de Derecho Laboral

## Introducción

Este documento describe las consultas SPARQL implementadas en el archivo
`rag/scripts/test_graphdb_connection.py`, que se conecta a una instancia de
**GraphDB** mediante la biblioteca **SPARQLWrapper** de Python.  
El script valida la conectividad con el repositorio RDF y demuestra el uso de
los principales tipos de consultas SPARQL requeridos para el proyecto.

---

## Configuración de la Conexión a GraphDB

La conexión a GraphDB se establece mediante la función auxiliar `_build_sparql()`,
que configura un objeto `SPARQLWrapper` apuntando al endpoint del repositorio
definido en las variables de entorno (`.env`):

```python
def _build_sparql(*, update: bool = False) -> SPARQLWrapper:
    if update:
        url = f"{settings.GRAPHDB_URL}/repositories/{settings.GRAPHDB_REPOSITORY}/statements"
    else:
        url = f"{settings.GRAPHDB_URL}/repositories/{settings.GRAPHDB_REPOSITORY}"

    sparql = SPARQLWrapper(url)
    sparql.setReturnFormat(JSON)
    if settings.GRAPHDB_USERNAME and settings.GRAPHDB_PASSWORD:
        sparql.setHTTPAuth(BASIC)
        sparql.setCredentials(settings.GRAPHDB_USERNAME, settings.GRAPHDB_PASSWORD)
    return sparql
```

- Las consultas **SELECT** usan el endpoint base: `.../repositories/{repo}`.
- Las operaciones **UPDATE** usan el endpoint de escritura: `.../repositories/{repo}/statements`.
- La autenticación HTTP Basic es opcional y se activa cuando las credenciales están configuradas.

Las variables de entorno relevantes son:

| Variable              | Descripción                          |
|-----------------------|--------------------------------------|
| `GRAPHDB_URL`         | URL base del servidor GraphDB        |
| `GRAPHDB_REPOSITORY`  | Nombre del repositorio RDF           |
| `GRAPHDB_USERNAME`    | Usuario (opcional)                   |
| `GRAPHDB_PASSWORD`    | Contraseña (opcional)                |
| `GRAPHDB_ENABLED`     | Habilita/deshabilita las pruebas     |

---

## Consultas SPARQL Implementadas

### 1. SELECT — Consulta Básica

**Prueba 1:** Listar todas las clases OWL definidas en el repositorio.

```sparql
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?clase ?etiqueta
WHERE {
    ?clase a owl:Class .
    OPTIONAL { ?clase rdfs:label ?etiqueta . }
}
```

**Descripción:**  
Esta consulta recupera todos los individuos de tipo `owl:Class` presentes en el
grafo junto con sus etiquetas (`rdfs:label`), usando `OPTIONAL` para que las
clases sin etiqueta también sean incluidas en los resultados.  
Valida que la ontología de contratos laborales esté correctamente cargada en
GraphDB (clases como `:Empleado`, `:ContratoLaboral`, `:Salario`, etc.).

---

### 2. SELECT + FILTER — Filtrado por Valor Numérico

**Prueba 2:** Recuperar empleados cuyo salario base sea igual o superior a
3.000.000 COP.

```sparql
PREFIX :    <http://example.org/contratos#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?nombre ?salarioBase
WHERE {
    ?emp  a             :Empleado ;
          :nombreCompleto ?nombre ;
          :tieneSalario   ?sal .
    ?sal  :salarioBase    ?salarioBase .
    FILTER (?salarioBase >= 3000000)
}
```

**Descripción:**  
La cláusula `FILTER` restringe los resultados a los empleados cuya propiedad
`:salarioBase` (enlazada a través del nodo `:Salario`) supera el umbral
numérico indicado.  
Demuestra el uso de operadores de comparación (`>=`) sobre literales
`xsd:decimal` / `xsd:integer` en SPARQL.

---

### 3. SELECT + ORDER BY — Ordenamiento de Resultados

**Prueba 3:** Listar contratos laborales ordenados por fecha de inicio de forma
descendente.

```sparql
PREFIX :    <http://example.org/contratos#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?contrato ?fechaInicio ?duracion
WHERE {
    ?contrato a             :ContratoLaboral ;
              :fechaInicio  ?fechaInicio .
    OPTIONAL { ?contrato :duracionMeses ?duracion . }
}
ORDER BY DESC(?fechaInicio)
```

**Descripción:**  
La cláusula `ORDER BY DESC(...)` ordena los contratos laborales del más reciente
al más antiguo según su propiedad `:fechaInicio`.  
El uso de `OPTIONAL` permite incluir contratos que no tengan registrada su
duración en meses sin excluirlos del resultado.

---

### 4. SELECT + LIMIT — Paginación de Resultados

**Prueba 4:** Recuperar los primeros 5 individuos de cualquier tipo presentes
en el grafo.

```sparql
SELECT DISTINCT ?sujeto ?tipo
WHERE {
    ?sujeto a ?tipo .
}
LIMIT 5
```

**Descripción:**  
La cláusula `LIMIT` restringe el número máximo de filas devueltas por la
consulta. `DISTINCT` elimina duplicados cuando un individuo tiene múltiples
tipos asignados.  
Esta consulta permite verificar rápidamente que el grafo contiene instancias
cargadas, sin importar su clase.

---

### 5. UPDATE — INSERT DATA (Inserción de Triples)

**Prueba 5:** Insertar un empleado de prueba en el grafo.

```sparql
PREFIX :    <http://example.org/contratos#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

INSERT DATA {
    :EmpleadoTest a              :Empleado ;
                  :nombreCompleto "Empleado De Prueba"^^xsd:string ;
                  :identificacion "TEST-001"^^xsd:string .
}
```

**Descripción:**  
`INSERT DATA` es una operación de actualización SPARQL que añade un conjunto
estático de triples al grafo por defecto del repositorio.  
La operación se ejecuta contra el endpoint `/statements` de GraphDB usando
el método HTTP `POST` con `POSTDIRECTLY`, tal como lo requiere el protocolo
SPARQL 1.1 Update.

Tras la inserción, se ejecuta una consulta SELECT de verificación para
confirmar que los triples fueron persistidos correctamente:

```sparql
PREFIX : <http://example.org/contratos#>

SELECT ?nombre ?id
WHERE {
    :EmpleadoTest :nombreCompleto ?nombre ;
                  :identificacion ?id .
}
```

---

### 6. UPDATE — DELETE DATA (Eliminación de Triples)

**Prueba 6:** Eliminar el empleado de prueba insertado previamente.

```sparql
PREFIX :    <http://example.org/contratos#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

DELETE DATA {
    :EmpleadoTest a              :Empleado ;
                  :nombreCompleto "Empleado De Prueba"^^xsd:string ;
                  :identificacion "TEST-001"^^xsd:string .
}
```

**Descripción:**  
`DELETE DATA` elimina un conjunto estático y conocido de triples del grafo.
Al igual que `INSERT DATA`, se deben especificar los valores exactos de cada
triple a eliminar.  
Tras la eliminación, se ejecuta una consulta SELECT de verificación para
confirmar que los triples ya no existen en el grafo:

```sparql
PREFIX : <http://example.org/contratos#>

SELECT ?nombre
WHERE {
    :EmpleadoTest :nombreCompleto ?nombre .
}
```

---

## Resumen de Requisitos

| Requisito                | Consulta implementada                          | Prueba   |
|--------------------------|------------------------------------------------|----------|
| `SELECT`                 | Listar clases OWL                              | Prueba 1 |
| `SELECT` + `FILTER`      | Empleados con salario ≥ 3.000.000              | Prueba 2 |
| `SELECT` + `ORDER BY`    | Contratos ordenados por fecha (descendente)    | Prueba 3 |
| `SELECT` + `LIMIT`       | Primeras 5 instancias del grafo                | Prueba 4 |
| `UPDATE` — `INSERT DATA` | Insertar empleado de prueba                    | Prueba 5 |
| `UPDATE` — `DELETE DATA` | Eliminar empleado de prueba                    | Prueba 6 |
| Conexión a GraphDB       | SPARQLWrapper sobre endpoint SPARQL de GraphDB | Todas    |

> **Nota sobre SPARQLWrapper y RDFLib:** SPARQLWrapper es la biblioteca estándar
> de Python para ejecutar consultas SPARQL contra endpoints remotos compatibles
> con el protocolo SPARQL 1.1. Se integra con el ecosistema RDFLib y sigue el
> mismo modelo de conexión remota que se usaría con `rdflib-endpoint`. En este
> proyecto se usa directamente sobre el endpoint HTTP del servidor GraphDB, sin
> gestión local del grafo.

---

## Ejecución del Script

```bash
# Desde el directorio rag/
make test-graphdb
# o equivalentemente:
.venv/bin/python -m scripts.test_graphdb_connection
```

Las variables de entorno necesarias deben estar definidas en `rag/.env`:

```env
GRAPHDB_URL=http://localhost:7200
GRAPHDB_REPOSITORY=labor-law
GRAPHDB_ENABLED=true
# GRAPHDB_USERNAME=admin     # opcional
# GRAPHDB_PASSWORD=secret    # opcional
```
