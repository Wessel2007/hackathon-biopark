import json
from typing import List

from fastapi import APIRouter, Depends
from openai import OpenAI
from pydantic import BaseModel

from app.config import settings
from app.routers.deps import get_current_user
from app.services.email_service import enviar_alerta
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
            "name": "buscar_protocolo_por_numero",
            "description": "Busca um protocolo específico pelo número do protocolo (ex: 2025/001). Use antes de atualizar para confirmar que o protocolo existe.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero": {"type": "string", "description": "Número do protocolo (campo 'protocolo'), ex: 2025/001"},
                },
                "required": ["numero"],
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
    {
        "type": "function",
        "function": {
            "name": "criar_protocolo",
            "description": "Cria um novo protocolo na plataforma. Use quando o usuário pedir para cadastrar ou criar um protocolo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "projeto":               {"type": "string", "description": "Nome do projeto"},
                    "protocolo":             {"type": "string", "description": "Número ou código do protocolo"},
                    "atividade":             {"type": "string", "description": "Descrição da atividade"},
                    "orgao_site_consultado": {"type": "string", "description": "Órgão ou site a ser consultado"},
                    "status": {
                        "type": "string",
                        "enum": ["EM ANDAMENTO", "PENDENTE", "APROVADO", "CANCELADO", "REPROVADO"],
                        "description": "Status inicial do protocolo (padrão: PENDENTE)",
                    },
                    "data_abertura":    {"type": "string", "description": "Data de abertura no formato YYYY-MM-DD"},
                    "atribuido_a":      {"type": "string", "description": "Nome do responsável pelo protocolo"},
                    "situacao":         {"type": "string", "description": "Descrição da situação atual"},
                    "url_consulta":     {"type": "string", "description": "URL para consulta do protocolo"},
                    "data_finalizacao": {"type": "string", "description": "Data de finalização no formato YYYY-MM-DD (opcional)"},
                },
                "required": ["projeto", "protocolo", "atividade", "orgao_site_consultado", "data_abertura"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "atualizar_protocolo",
            "description": "Atualiza campos de um protocolo existente pelo número do protocolo. Use quando o usuário pedir para mudar status, situação, responsável ou qualquer outro campo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "numero": {"type": "string", "description": "Número do protocolo a ser atualizado (campo 'protocolo'), ex: 2025/001"},
                    "status": {
                        "type": "string",
                        "enum": ["EM ANDAMENTO", "PENDENTE", "APROVADO", "CANCELADO", "REPROVADO"],
                        "description": "Novo status do protocolo",
                    },
                    "situacao":         {"type": "string", "description": "Nova descrição da situação"},
                    "atribuido_a":      {"type": "string", "description": "Novo responsável"},
                    "data_finalizacao": {"type": "string", "description": "Data de finalização no formato YYYY-MM-DD"},
                    "ativo":            {"type": "boolean", "description": "true = ativo, false = inativo"},
                },
                "required": ["numero"],
            },
        },
    },
]

SYSTEM_PROMPT = (
    "Você é um assistente especializado na plataforma Biopark de gestão de protocolos públicos. "
    "Você pode consultar, criar e atualizar protocolos usando as ferramentas disponíveis. "
    "Responda sempre em português brasileiro de forma clara, direta e objetiva. "
    "Quando precisar de dados reais, use as ferramentas antes de responder. "
    "Para ações de escrita (criar/atualizar): confirme os dados com o usuário ANTES de executar, "
    "a menos que ele já tenha fornecido todos os detalhes claramente. "
    "Após criar ou atualizar, informe o resultado com os dados do registro. "
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


def _buscar_protocolo_por_numero(sb: SupabaseClient, numero: str):
    result = sb.table("protocols").select(
        "id,projeto,protocolo,atividade,status,situacao,orgao_site_consultado,atribuido_a,data_abertura,data_finalizacao,ativo"
    ).ilike("protocolo", numero).execute()
    if not result.data:
        return {"error": f"Nenhum protocolo encontrado com o número '{numero}'"}
    return result.data


def _resumo_dashboard(sb: SupabaseClient):
    protocols = sb.table("protocols").select("status,ativo").execute().data
    total = len(protocols)
    ativos = sum(1 for p in protocols if p.get("ativo"))
    por_status: dict = {}
    for p in protocols:
        s = p.get("status", "DESCONHECIDO")
        por_status[s] = por_status.get(s, 0) + 1
    return {"total": total, "ativos": ativos, "inativos": total - ativos, "por_status": por_status}


def _criar_protocolo(sb: SupabaseClient, user_email: str = "", **kwargs):
    payload = {
        "status":                kwargs.get("status", "PENDENTE"),
        "projeto":               kwargs["projeto"],
        "protocolo":             kwargs["protocolo"],
        "atividade":             kwargs["atividade"],
        "orgao_site_consultado": kwargs["orgao_site_consultado"],
        "data_abertura":         kwargs["data_abertura"],
        "atribuido_a":           kwargs.get("atribuido_a"),
        "situacao":              kwargs.get("situacao"),
        "url_consulta":          kwargs.get("url_consulta"),
        "data_finalizacao":      kwargs.get("data_finalizacao"),
        "ativo":                 True,
    }
    existing = sb.table("protocols").select("id").eq("projeto", payload["projeto"]).eq("protocolo", payload["protocolo"]).execute()
    if existing.data:
        return {"error": "Já existe um protocolo com esse número para este projeto."}
    result = sb.table("protocols").insert(payload).execute()
    if not result.data:
        return {"error": "Erro ao criar protocolo no banco de dados."}
    protocolo_criado = result.data[0]
    enviar_alerta(
        protocolo_criado,
        [f"Protocolo {protocolo_criado['protocolo']} do projeto {protocolo_criado['projeto']} foi criado com status {protocolo_criado['status']}."],
        user_email,
    )
    return {"sucesso": True, "protocolo": protocolo_criado}


def _atualizar_protocolo(sb: SupabaseClient, numero: str, user_email: str = "", **kwargs):
    existing = sb.table("protocols").select("id,projeto,protocolo,status,orgao_site_consultado,atribuido_a").ilike("protocolo", numero).execute()
    if not existing.data:
        return {"error": f"Nenhum protocolo encontrado com o número '{numero}'."}
    if len(existing.data) > 1:
        nomes = [f"ID {p['id']} — {p['projeto']}" for p in existing.data]
        return {"error": f"Mais de um protocolo encontrado com esse número. Especifique o projeto: {', '.join(nomes)}"}

    antes = existing.data[0]
    protocol_id = antes["id"]
    campos_permitidos = ["status", "situacao", "atribuido_a", "data_finalizacao", "ativo",
                         "projeto", "atividade", "orgao_site_consultado", "url_consulta"]
    payload = {k: v for k, v in kwargs.items() if k in campos_permitidos and v is not None}

    if not payload:
        return {"error": "Nenhum campo válido para atualizar foi fornecido."}

    result = sb.table("protocols").update(payload).eq("id", protocol_id).execute()
    if not result.data:
        return {"error": "Erro ao atualizar protocolo."}

    depois = result.data[0]
    mudancas = []
    for campo, label in [("status", "Status"), ("situacao", "Situação"), ("atribuido_a", "Responsável")]:
        v_antes = antes.get(campo)
        v_depois = depois.get(campo)
        if v_antes != v_depois and v_depois is not None:
            mudancas.append(f"{label} alterado de '{v_antes or '—'}' para '{v_depois}'.")
    if not mudancas:
        mudancas = [f"Protocolo {depois['protocolo']} atualizado via assistente."]

    enviar_alerta(depois, mudancas, user_email)
    return {"sucesso": True, "protocolo": depois}


def _run_tool(name: str, args: dict, sb: SupabaseClient, user_email: str = ""):
    if name == "buscar_protocolos":
        return _buscar_protocolos(sb, **args)
    if name == "buscar_protocolo_por_numero":
        return _buscar_protocolo_por_numero(sb, **args)
    if name == "resumo_dashboard":
        return _resumo_dashboard(sb)
    if name == "criar_protocolo":
        return _criar_protocolo(sb, user_email=user_email, **args)
    if name == "atualizar_protocolo":
        return _atualizar_protocolo(sb, user_email=user_email, **args)
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
    current_user: str = Depends(get_current_user),
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
            result = _run_tool(tc.function.name, json.loads(tc.function.arguments), sb, current_user)
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
