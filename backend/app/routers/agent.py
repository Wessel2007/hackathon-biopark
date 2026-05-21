import json
from typing import List

from fastapi import APIRouter, Depends
from openai import OpenAI
from pydantic import BaseModel

from app.config import settings
from app.routers.deps import get_current_user
from app.supabase_client import SupabaseClient, get_supabase

router = APIRouter(prefix="/agent", tags=["agent"])

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "buscar_protocolos",
            "description": "Busca protocolos cadastrados com filtros opcionais. Use para responder perguntas sobre projetos, status, órgãos ou responsáveis.",
            "parameters": {
                "type": "object",
                "properties": {
                    "projeto": {"type": "string", "description": "Filtrar por nome do projeto (busca parcial)"},
                    "status": {
                        "type": "string",
                        "enum": ["EM ANDAMENTO", "PENDENTE", "APROVADO", "CANCELADO", "REPROVADO"],
                        "description": "Filtrar por status do protocolo",
                    },
                    "ativo": {"type": "boolean", "description": "true = apenas ativos, false = apenas inativos"},
                    "limit": {"type": "integer", "description": "Máximo de resultados (padrão 20, máximo 100)"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "resumo_dashboard",
            "description": "Retorna estatísticas gerais: total de protocolos, quantos ativos, distribuição por status. Use para perguntas de visão geral.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]

SYSTEM_PROMPT = (
    "Você é um assistente especializado na plataforma Biopark de gestão de protocolos públicos. "
    "Ajude o usuário a entender o status dos protocolos, encontrar informações e tomar decisões. "
    "Responda sempre em português brasileiro de forma clara, direta e objetiva. "
    "Quando precisar de dados reais, use as ferramentas disponíveis antes de responder. "
    "Nunca invente dados — se não encontrar, diga que não há registros."
)


def _buscar_protocolos(sb: SupabaseClient, projeto=None, status=None, ativo=None, limit=20):
    limit = min(int(limit), 100)
    q = sb.table("protocols").select(
        "id,projeto,protocolo,atividade,status,situacao,orgao_site_consultado,atribuido_a,data_abertura,data_finalizacao,ativo"
    )
    if projeto:
        q = q.ilike("projeto", f"%{projeto}%")
    if status:
        q = q.eq("status", status)
    if ativo is not None:
        q = q.eq("ativo", ativo)
    return q.limit(limit).order("projeto").execute().data


def _resumo_dashboard(sb: SupabaseClient):
    protocols = sb.table("protocols").select("status,ativo").execute().data
    total = len(protocols)
    ativos = sum(1 for p in protocols if p.get("ativo"))
    por_status: dict = {}
    for p in protocols:
        s = p.get("status", "DESCONHECIDO")
        por_status[s] = por_status.get(s, 0) + 1
    return {"total": total, "ativos": ativos, "inativos": total - ativos, "por_status": por_status}


def _run_tool(name: str, args: dict, sb: SupabaseClient):
    if name == "buscar_protocolos":
        return _buscar_protocolos(sb, **args)
    if name == "resumo_dashboard":
        return _resumo_dashboard(sb)
    return {"error": "Ferramenta desconhecida"}


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]


@router.post("/chat")
def chat(
    body: ChatRequest,
    sb: SupabaseClient = Depends(get_supabase),
    _: str = Depends(get_current_user),
):
    client = OpenAI(api_key=settings.openai_api_key)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages += [{"role": m.role, "content": m.content} for m in body.messages]

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        tools=TOOLS,
        tool_choice="auto",
    )

    msg = response.choices[0].message

    if msg.tool_calls:
        messages.append(msg)
        for tc in msg.tool_calls:
            result = _run_tool(tc.function.name, json.loads(tc.function.arguments), sb)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": json.dumps(result, ensure_ascii=False, default=str),
            })
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
        )
        msg = response.choices[0].message

    return {"reply": msg.content}
