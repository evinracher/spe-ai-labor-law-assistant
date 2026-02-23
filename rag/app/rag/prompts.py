from langchain_core.messages import SystemMessage
from langchain_core.prompts import ChatPromptTemplate

CLASSIFIER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """
     You are a classifier. Your tasks is to classifier the user intention
     choose:
     - 'domainSearch' if the user is asking about Colombian Labor Laws
     - 'summarize' if the user is asking to summarize a document from the Colombian Labor Law domain (e.g.: a law article, a law)
     - 'compare' if the user is asking to compare two or more documents from the Colombian Labor Law domain
     - 'generalSearch' if the user is asking a general question
     Answer only with the JSOM scheme asked.
    """,
        ),
        ("user", "question: {question}"),
    ]
)

GENERAL_SYSTEM_PROMPT = SystemMessage(
    content="""
     Answer the user question in Spanish. At the end of the answer, only if user asked a question, add a note that says:

     **Nota:** Soy un asistente especializado en **derecho laboral colombiano**. Esta respuesta se proporciona a nivel general y puede no reflejar información actualizada o especializada sobre este tema. Se recomienda consultar una fuente experta o profesional en el área correspondiente.
"""
)
