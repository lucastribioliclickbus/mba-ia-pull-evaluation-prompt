"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header

load_dotenv()

PROMPT_KEY = "bug_to_user_story_v2"
PROMPT_FILE = Path(__file__).resolve().parent.parent / "prompts" / f"{PROMPT_KEY}.yml"
INPUT_VARIABLE = "bug_report"


def build_chat_prompt(prompt_data: dict) -> ChatPromptTemplate:
    """
    Monta o ChatPromptTemplate que será publicado no Hub.

    Args:
        prompt_data: Dados do prompt lidos do YAML

    Returns:
        ChatPromptTemplate com mensagem de sistema e mensagem de usuário
    """
    return ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("human", prompt_data["user_prompt"]),
    ])


def build_readme(prompt_data: dict) -> str:
    """
    Monta o README publicado junto do prompt no Hub.

    Args:
        prompt_data: Dados do prompt lidos do YAML

    Returns:
        Texto em markdown com descrição, técnicas e variáveis de entrada
    """
    techniques = "\n".join(f"- {technique}" for technique in prompt_data["techniques_applied"])

    return (
        f"# {PROMPT_KEY}\n\n"
        f"{prompt_data['description'].strip()}\n\n"
        f"## Técnicas de Prompt Engineering aplicadas\n\n{techniques}\n\n"
        f"## Variável de entrada\n\n- `{INPUT_VARIABLE}`: relato de bug em texto livre\n\n"
        f"## Versão\n\n{prompt_data['version']} — publicado em {prompt_data['created_at']}\n"
    )


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    errors = []

    for field in ("description", "system_prompt", "user_prompt", "version"):
        if not str(prompt_data.get(field, "")).strip():
            errors.append(f"Campo obrigatório vazio ou ausente: {field}")

    system_prompt = str(prompt_data.get("system_prompt", ""))
    user_prompt = str(prompt_data.get("user_prompt", ""))

    if "TODO" in system_prompt or "TODO" in user_prompt:
        errors.append("O prompt ainda contém TODO")

    placeholder = "{" + INPUT_VARIABLE + "}"
    if placeholder not in user_prompt:
        errors.append(f"user_prompt precisa conter {placeholder}")

    if placeholder in system_prompt:
        errors.append(f"system_prompt não deve repetir {placeholder} — ele pertence ao user_prompt")

    techniques = prompt_data.get("techniques_applied", [])
    if len(techniques) < 2:
        errors.append(f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}")

    return (len(errors) == 0, errors)


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    print(f"Publicando: {prompt_name}")

    try:
        url = hub.push(
            prompt_name,
            build_chat_prompt(prompt_data),
            new_repo_is_public=True,
            new_repo_description=" ".join(prompt_data["description"].split()),
            readme=build_readme(prompt_data),
            tags=list(prompt_data.get("tags", [])),
        )
    except Exception as e:
        print(f"❌ Erro ao publicar o prompt: {e}")
        print("\nVerifique:")
        print("- LANGSMITH_API_KEY está configurada e tem permissão de escrita")
        print("- USERNAME_LANGSMITH_HUB corresponde ao seu handle do LangSmith Hub")
        return False

    print(f"   ✓ Técnicas: {', '.join(prompt_data['techniques_applied'])}")
    print(f"   ✓ Tags: {', '.join(prompt_data.get('tags', []))}")
    print(f"   ✓ Publicado em: {url}")
    print("\n⚠️  Se o prompt já existia como privado, torne-o público no dashboard —")
    print("   a visibilidade só é definida na criação do repositório.")
    return True


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS OTIMIZADOS PARA O LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    prompts = load_yaml(str(PROMPT_FILE))
    if not prompts or PROMPT_KEY not in prompts:
        print(f"❌ Prompt '{PROMPT_KEY}' não encontrado em {PROMPT_FILE}")
        return 1

    prompt_data = prompts[PROMPT_KEY]

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1

    print(f"   ✓ Prompt válido ({len(prompt_data['system_prompt'])} caracteres no system prompt)\n")

    username = os.getenv("USERNAME_LANGSMITH_HUB", "").strip()

    if not push_prompt_to_langsmith(f"{username}/{PROMPT_KEY}", prompt_data):
        return 1

    print("\n✅ Push concluído.")
    print("\nPróximo passo:")
    print("   python src/evaluate.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
