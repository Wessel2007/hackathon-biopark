"""Script para apagar todos os protocolos do Supabase."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

import httpx

SUPABASE_URL = os.environ['SUPABASE_URL']
SUPABASE_ANON_KEY = os.environ['SUPABASE_ANON_KEY']

HEADERS = {
    "apikey": SUPABASE_ANON_KEY,
    "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal",
}

REST_URL = f"{SUPABASE_URL.rstrip('/')}/rest/v1"


def clear_all():
    with httpx.Client(timeout=30) as client:
        r = client.delete(f"{REST_URL}/query_history", headers=HEADERS, params={"id": "gte.1"})
        if r.is_success or r.status_code == 204:
            print("query_history: apagado com sucesso")
        else:
            print(f"query_history erro {r.status_code}: {r.text}")

        r = client.delete(f"{REST_URL}/protocols", headers=HEADERS, params={"id": "gte.1"})
        if r.is_success or r.status_code == 204:
            print("protocols: apagado com sucesso")
        else:
            print(f"protocols erro {r.status_code}: {r.text}")
            return

    print("\nTodos os dados foram apagados. Importe a planilha de carga inicial.")


if __name__ == "__main__":
    confirm = input("Tem certeza que deseja apagar TODOS os protocolos? (s/N): ")
    if confirm.strip().lower() == 's':
        clear_all()
    else:
        print("Operacao cancelada.")
