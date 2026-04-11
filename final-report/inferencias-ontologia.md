# Inferencia con la Ontología e Instancias — Asistente de Derecho Laboral Colombiano

## Introducción

Este documento describe los cinco casos de inferencia implementados sobre la
ontología **OntologiaContratos** (`http://example.org/contratos#`) cargada en
GraphDB. Las consultas se ejecutan desde Python usando la biblioteca
**SPARQLWrapper**, que forma parte del ecosistema **RDFLib** y sigue el
protocolo SPARQL 1.1 sobre HTTP.

### ¿Qué es la inferencia en GraphDB?

La **inferencia** (o razonamiento automático) permite que el motor de GraphDB
derive triples nuevos a partir de los axiomas de la ontología OWL/RDFS, sin
que esos triples estén escritos explícitamente en los datos. Para ello,
GraphDB debe estar configurado con un **ruleset** de OWL, por ejemplo
`OWL2-RL-Optimized` u `OWL-Horst-Optimized`.

Cuando la inferencia está habilitada, GraphDB **materializa** en tiempo de
carga los triples implícitos. Esto significa que una consulta SPARQL ordinaria
`SELECT` puede recuperar esos triples como si fuesen aserciones explícitas,
sin necesidad de añadir razonadores externos ni reescribir las consultas.

> **Activación de la inferencia en GraphDB:**  
> Al crear el repositorio, seleccionar _Ruleset_ → `OWL2-RL` (o superior) y
> dejar habilitada la opción _Enable OWL inferencing_. Una vez cargada la
> ontología y las instancias, el motor materializa todas las inferencias de
> manera automática.

---

## Configuración de la Conexión a GraphDB

Todas las consultas de inferencia se ejecutan mediante la función auxiliar
`_build_sparql()` definida en `rag/scripts/test_graphdb_connection.py`:

```python
from SPARQLWrapper import BASIC, JSON, SPARQLWrapper
from app.core.config import settings

def _build_sparql(*, update: bool = False) -> SPARQLWrapper:
    url = (
        f"{settings.GRAPHDB_URL}/repositories/{settings.GRAPHDB_REPOSITORY}/statements"
        if update
        else f"{settings.GRAPHDB_URL}/repositories/{settings.GRAPHDB_REPOSITORY}"
    )
    sparql = SPARQLWrapper(url)
    sparql.setReturnFormat(JSON)
    if settings.GRAPHDB_USERNAME and settings.GRAPHDB_PASSWORD:
        sparql.setHTTPAuth(BASIC)
        sparql.setCredentials(settings.GRAPHDB_USERNAME, settings.GRAPHDB_PASSWORD)
    return sparql

def _run_select(sparql: SPARQLWrapper, query: str) -> list[dict]:
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    response = sparql.query().convert()
    return [
        {var: row[var]["value"] for var in row}
        for row in response.get("results", {}).get("bindings", [])
    ]
```

Las variables de entorno relevantes son:

| Variable              | Descripción                          |
|-----------------------|--------------------------------------|
| `GRAPHDB_URL`         | URL base del servidor GraphDB        |
| `GRAPHDB_REPOSITORY`  | Nombre del repositorio RDF           |
| `GRAPHDB_USERNAME`    | Usuario (opcional)                   |
| `GRAPHDB_PASSWORD`    | Contraseña (opcional)                |
| `GRAPHDB_ENABLED`     | Habilita/deshabilita las pruebas     |

---

## Instancias de la Ontología

Antes de describir las inferencias, se resumen las instancias cargadas en el
repositorio desde el archivo `ontology/labor-law-ontology.ttl`:

| Individuo          | Tipo(s) declarados explícitamente          |
|--------------------|--------------------------------------------|
| `:EmpresaAlfa`     | `:Persona`, `:Contratante`, `:Empleador`   |
| `:EmpresaBeta`     | `:Persona`, `:Contratante`, `:Empleador`   |
| `:EmpresaGamma`    | `:Persona`, `:Contratante`, `:Empleador`   |
| `:EmpresaDelta`    | `:Persona`, `:Contratante`, `:Empleador`   |
| `:AnaLopez`        | `:Persona`, `:Empleado`                    |
| `:BrunoDiaz`       | `:Persona`, `:Empleado`                    |
| `:CarlaRuiz`       | `:Persona`, `:Empleado`                    |
| `:DiegoPerez`      | `:Persona`, `:Empleado`                    |
| `:SofiaMoreno`     | `:Persona`, `:Contratista`                 |
| `:TomasVega`       | `:Persona`, `:Contratista`                 |
| `:ValeriaCruz`     | `:Persona`, `:Contratista`                 |
| `:WalterNino`      | `:Persona`, `:Contratista`                 |
| `:ContratoLab001`  | `:Contrato`, `:ContratoLaboral`            |
| `:ContratoPS001`   | `:Contrato`, `:ContratoPrestacionServicios`|

Además, cada empleado tiene la propiedad `:esEmpleadoDe` hacia su empleador
(por ejemplo, `:AnaLopez :esEmpleadoDe :EmpresaAlfa`), y cada empleador tiene
`:empleaA` hacia sus empleados **solo de forma implícita** (a través de la
propiedad inversa declarada en la ontología).

---

## Caso de Inferencia 1 — `owl:equivalentClass`: clasificación de `:TrabajadorVinculado`

### Axioma de la ontología

```turtle
:TrabajadorVinculado a owl:Class ;
    owl:equivalentClass [
        a owl:Class ;
        owl:intersectionOf (
            :Empleado
            [ a owl:Restriction ;
              owl:onProperty :tieneContrato ;
              owl:someValuesFrom :ContratoLaboral
            ]
        )
    ] .
```

Este axioma declara que `:TrabajadorVinculado` es **equivalente** a la
intersección de ser `:Empleado` **y** tener al menos un `:tieneContrato` que
sea del tipo `:ContratoLaboral`.

### Por qué es posible sólo con inferencia

En los datos **no existe ninguna aserción** `?x rdf:type :TrabajadorVinculado`.
Sin el razonador, la consulta devolvería cero resultados. Con inferencia
habilitada, GraphDB aplica la regla de equivalencia OWL y clasifica
automáticamente todo individuo que satisfaga la descripción de la clase (ser
`:Empleado` con un contrato laboral) como `:TrabajadorVinculado`.

### Consulta SPARQL

```python
sparql = _build_sparql()

query = """
    PREFIX : <http://example.org/contratos#>
    SELECT ?persona
    WHERE {
        ?persona a :TrabajadorVinculado .
    }
"""

rows = _run_select(sparql, query)
for r in rows:
    print(r["persona"])
```

### Resultado esperado con las instancias cargadas

| `?persona`              |
|-------------------------|
| `:AnaLopez`             |
| `:BrunoDiaz`            |
| `:CarlaRuiz`            |
| `:DiegoPerez`           |

Los cuatro empleados poseen un `:ContratoLaboral` a través de `:tieneContrato`,
por lo que el razonador los clasifica a todos como `:TrabajadorVinculado`.

---

## Caso de Inferencia 2 — `rdfs:subClassOf`: `:Empleado` → `:Persona`

### Axioma de la ontología

```turtle
:Empleado a owl:Class ;
    rdfs:subClassOf :Persona .
```

### Por qué es posible sólo con inferencia

Ningún `:Empleado` ni `:Employador` tiene la aserción explícita
`rdf:type :Persona` en los datos, salvo la redundancia declarada por el autor
en algunos individuos. Pero los individuos `:SofiaMoreno`, `:TomasVega`,
etc. (`:Contratista`) no la tienen. Sin inferencia, buscar `?x a :Persona`
sólo retorna aquellos a quienes se les asignó ese tipo explícitamente.  
Con inferencia **RDFS**, la regla `rdfs:subClassOf` se propaga: si `C
rdfs:subClassOf D` y `x rdf:type C`, entonces `x rdf:type D`. Así, todo
`:Empleado`, `:Contratista`, `:Contratante` y `:Empleador` es inferido como
`:Persona`.

### Consulta SPARQL

```python
query = """
    PREFIX : <http://example.org/contratos#>
    SELECT ?persona ?nombre
    WHERE {
        ?persona a :Persona .
        OPTIONAL { ?persona :nombreCompleto ?nombre . }
    }
    ORDER BY ?nombre
"""

rows = _run_select(sparql, query)
for r in rows:
    print(r.get("nombre", r["persona"]))
```

### Resultado esperado con las instancias cargadas

| `?nombre`                | `?persona`          |
|--------------------------|---------------------|
| Ana López                | `:AnaLopez`         |
| Bruno Díaz               | `:BrunoDiaz`        |
| Carla Ruiz               | `:CarlaRuiz`        |
| Diego Pérez              | `:DiegoPerez`       |
| Empresa Alfa S.A.S.      | `:EmpresaAlfa`      |
| Empresa Beta S.A.S.      | `:EmpresaBeta`      |
| Empresa Delta S.A.S.     | `:EmpresaDelta`     |
| Empresa Gamma S.A.S.     | `:EmpresaGamma`     |
| Sofía Moreno             | `:SofiaMoreno`      |
| Tomás Vega               | `:TomasVega`        |
| Valeria Cruz             | `:ValeriaCruz`      |
| Walter Niño              | `:WalterNino`       |

Sin inferencia, sólo se recuperarían los individuos que tuviesen la aserción
`rdf:type :Persona` de forma explícita en los datos (un subconjunto de los
anteriores o ninguno, dependiendo de si el autor la incluyó).

---

## Caso de Inferencia 3 — `rdfs:subClassOf` en cadena: `:Empleador` → `:Contratante`

### Axioma de la ontología

```turtle
:Empleador a owl:Class ;
    rdfs:subClassOf :Contratante .

:Contratante a owl:Class ;
    rdfs:subClassOf :Persona .
```

### Por qué es posible sólo con inferencia

La cadena de subclases es `:Empleador` ⊆ `:Contratante` ⊆ `:Persona`.
Las cuatro empresas (`:EmpresaAlfa`, `:EmpresaBeta`, `:EmpresaGamma`,
`:EmpresaDelta`) están declaradas explícitamente como `:Empleador` (y también
como `:Persona` y `:Contratante`, aunque esta última podría no estar declarada
para todos los individuos dependiendo de la versión del archivo TTL).  
Sin embargo, los individuos de tipo `:Contratante` que **no** sean
`:Empleador` (por ejemplo, una entidad contratante sin empleados), recibirían
la inferencia de `:Persona` sólo por la cadena RDFS. La consulta busca todo
individuo inferido como `:Contratante`, incluyendo aquellos que sólo son
`:Empleador` y cuya pertenencia a `:Contratante` deriva de la jerarquía.

### Consulta SPARQL

```python
query = """
    PREFIX : <http://example.org/contratos#>
    SELECT ?contratante ?nombre
    WHERE {
        ?contratante a :Contratante .
        OPTIONAL { ?contratante :nombreCompleto ?nombre . }
    }
    ORDER BY ?nombre
"""

rows = _run_select(sparql, query)
for r in rows:
    print(r.get("nombre", r["contratante"]))
```

### Resultado esperado con las instancias cargadas

| `?nombre`                | `?contratante`      |
|--------------------------|---------------------|
| Empresa Alfa S.A.S.      | `:EmpresaAlfa`      |
| Empresa Beta S.A.S.      | `:EmpresaBeta`      |
| Empresa Delta S.A.S.     | `:EmpresaDelta`     |
| Empresa Gamma S.A.S.     | `:EmpresaGamma`     |

Si en el futuro se añadiera un individuo tipado únicamente como `:Empleador`
(sin declarar `:Contratante` explícitamente), el razonador lo incluiría de
igual manera gracias a la cadena de subclases.

---

## Caso de Inferencia 4 — `owl:inverseOf`: `:empleaA` ↔ `:esEmpleadoDe`

### Axioma de la ontología

```turtle
:empleaA a owl:ObjectProperty ;
    rdfs:subPropertyOf :contrataA ;
    rdfs:domain :Empleador ;
    rdfs:range :Empleado ;
    owl:inverseOf :esEmpleadoDe .

:esEmpleadoDe a owl:ObjectProperty ;
    rdfs:subPropertyOf :esContratadoPor ;
    rdfs:domain :Empleado ;
    rdfs:range :Empleador .
```

### Por qué es posible sólo con inferencia

En los datos, los empleados tienen la propiedad `:esEmpleadoDe` hacia su
empleador (por ejemplo, `AnaLopez :esEmpleadoDe :EmpresaAlfa`). Ningún
empleador tiene `:empleaA` declarado **explícitamente** en el archivo de
instancias. Con inferencia habilitada, GraphDB aplica la regla
`owl:inverseOf`: si existe `(X :esEmpleadoDe Y)`, se materializa
`(Y :empleaA X)`. La consulta busca triples `:empleaA` que existen
**únicamente como inferencias**.

### Consulta SPARQL

```python
query = """
    PREFIX : <http://example.org/contratos#>
    SELECT ?empleador ?empleado
    WHERE {
        ?empleador :empleaA ?empleado .
    }
    ORDER BY ?empleador ?empleado
"""

rows = _run_select(sparql, query)
for r in rows:
    emp_r = r["empleador"].replace("http://example.org/contratos#", ":")
    emp_e = r["empleado"].replace("http://example.org/contratos#", ":")
    print(f"{emp_r}  :empleaA  {emp_e}")
```

### Resultado esperado con las instancias cargadas

| `?empleador`      | `?empleado`    |
|-------------------|----------------|
| `:EmpresaAlfa`    | `:AnaLopez`    |
| `:EmpresaBeta`    | `:BrunoDiaz`   |
| `:EmpresaDelta`   | `:DiegoPerez`  |
| `:EmpresaGamma`   | `:CarlaRuiz`   |

Sin inferencia, esta consulta no retornaría ningún resultado, ya que el
archivo TTL no contiene ninguna aserción `?empleador :empleaA ?empleado`.

---

## Caso de Inferencia 5 — `rdfs:subPropertyOf`: `:empleaA` → `:contrataA`

### Axioma de la ontología

```turtle
:contrataA a owl:ObjectProperty ;
    rdfs:domain :Contratante ;
    rdfs:range :Persona ;
    owl:inverseOf :esContratadoPor .

:empleaA a owl:ObjectProperty ;
    rdfs:subPropertyOf :contrataA ;
    rdfs:domain :Empleador ;
    rdfs:range :Empleado .
```

### Por qué es posible sólo con inferencia

La regla RDFS de sub-propiedades establece que si `P rdfs:subPropertyOf Q` y
existe el triple `(X P Y)`, entonces también se infiere `(X Q Y)`. En los
datos existe `(EmpresaAlfa :esEmpleadoDe AnaLopez)` cuya inversa inferida es
`(EmpresaAlfa :empleaA AnaLopez)`. A su vez, como `:empleaA
rdfs:subPropertyOf :contrataA`, se infiere un segundo triple
`(EmpresaAlfa :contrataA AnaLopez)`. Ningún triple `:contrataA` está escrito
en el archivo TTL; todos son el resultado de la **cadena de inferencias**:
`owl:inverseOf` seguido de `rdfs:subPropertyOf`.

### Consulta SPARQL

```python
query = """
    PREFIX : <http://example.org/contratos#>
    SELECT ?empleador ?persona
    WHERE {
        ?empleador :contrataA ?persona .
    }
    ORDER BY ?empleador ?persona
"""

rows = _run_select(sparql, query)
for r in rows:
    empl = r["empleador"].replace("http://example.org/contratos#", ":")
    pers = r["persona"].replace("http://example.org/contratos#", ":")
    print(f"{empl}  :contrataA  {pers}")
```

### Resultado esperado con las instancias cargadas

| `?empleador`      | `?persona`      | Origen de la inferencia                      |
|-------------------|-----------------|----------------------------------------------|
| `:EmpresaAlfa`    | `:AnaLopez`     | `inverseOf(:esEmpleadoDe)` + `subPropertyOf` |
| `:EmpresaBeta`    | `:BrunoDiaz`    | `inverseOf(:esEmpleadoDe)` + `subPropertyOf` |
| `:EmpresaDelta`   | `:DiegoPerez`   | `inverseOf(:esEmpleadoDe)` + `subPropertyOf` |
| `:EmpresaGamma`   | `:CarlaRuiz`    | `inverseOf(:esEmpleadoDe)` + `subPropertyOf` |

Sin inferencia, la consulta no devuelve ningún resultado.

---

## Resumen de los Casos de Inferencia

| # | Mecanismo OWL/RDFS          | Axioma clave                                           | Triple inferido (ejemplo)                                          |
|---|-----------------------------|--------------------------------------------------------|--------------------------------------------------------------------|
| 1 | `owl:equivalentClass`       | `TrabajadorVinculado ≡ Empleado ⊓ ∃tieneContrato.ContratoLaboral` | `:AnaLopez rdf:type :TrabajadorVinculado`              |
| 2 | `rdfs:subClassOf`           | `:Empleado rdfs:subClassOf :Persona`                   | `:AnaLopez rdf:type :Persona`                                      |
| 3 | `rdfs:subClassOf` en cadena | `:Empleador rdfs:subClassOf :Contratante`              | `:EmpresaAlfa rdf:type :Contratante`                               |
| 4 | `owl:inverseOf`             | `:empleaA owl:inverseOf :esEmpleadoDe`                 | `:EmpresaAlfa :empleaA :AnaLopez`                                  |
| 5 | `rdfs:subPropertyOf`        | `:empleaA rdfs:subPropertyOf :contrataA`               | `:EmpresaAlfa :contrataA :AnaLopez`                                |

### Conclusión

Las cinco consultas son ejemplos concretos de que la inferencia habilitada en
GraphDB enriquece el grafo de conocimiento **sin modificar los datos de
origen**. El archivo `labor-law-ontology.ttl` no contiene ninguna de las
aserciones recuperadas por estas consultas; todas son producidas por el motor
de razonamiento a partir de los axiomas OWL/RDFS declarados en la ontología.
Esto permite que las consultas del sistema RAG accedan a relaciones semánticas
implícitas (jerarquías de clases, propiedades inversas, equivalencias) de
forma transparente, incrementando la calidad y completitud de las respuestas
generadas.

---

## Ejecución del Script de Pruebas

Los cinco casos de inferencia están implementados en la función
`_test_inference()` del archivo
`rag/scripts/test_graphdb_connection.py` y se ejecutan con:

```bash
# Desde el directorio rag/
make test-graphdb

# O directamente:
.venv/bin/python -m scripts.test_graphdb_connection
```

El script reporta `✔ PASS` cuando GraphDB retorna los individuos inferidos, y
`⚠ WARN` cuando no se encuentran resultados (indicando que el ruleset OWL no
está habilitado o que las instancias no están cargadas).
