"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
import yaml
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from langchain import hub
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()


def represent_multiline_string(dumper, data):
    """
    Grava strings de várias linhas como bloco literal, mantendo o YAML legível.

    Args:
        dumper: Dumper do PyYAML em uso
        data: String a ser serializada

    Returns:
        Nó escalar YAML
    """
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


yaml.add_representer(str, represent_multiline_string)

SOURCE_PROMPT = "leonanluppi/bug_to_user_story_v1"
OUTPUT_FILE = Path(__file__).resolve().parent.parent / "prompts" / "bug_to_user_story_v1.yml"


def extract_templates(prompt) -> tuple[str, str]:
    """
    Separa o template de sistema do template de usuário de um ChatPromptTemplate.

    Args:
        prompt: ChatPromptTemplate retornado pelo Hub

    Returns:
        (system_prompt, user_prompt) - Tupla com os dois templates
    """
    system_parts = []
    user_parts = []

    for message in getattr(prompt, "messages", []):
        template = getattr(getattr(message, "prompt", None), "template", "")
        if not template:
            continue

        role = type(message).__name__
        if role.startswith("System"):
            system_parts.append(template)
        elif role.startswith("Human"):
            user_parts.append(template)

    return ("\n".join(system_parts), "\n".join(user_parts))


def build_prompt_data(prompt, prompt_key: str) -> dict:
    """
    Monta o dicionário que será gravado no YAML local.

    Args:
        prompt: ChatPromptTemplate retornado pelo Hub
        prompt_key: Chave raiz do YAML (nome do prompt sem o owner)

    Returns:
        Dicionário no formato esperado por prompts/*.yml
    """
    system_prompt, user_prompt = extract_templates(prompt)

    return {
        prompt_key: {
            "description": "Prompt para converter relatos de bugs em User Stories",
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "version": "v1",
            "created_at": date.today().isoformat(),
            "tags": ["bug-analysis", "user-story", "product-management"],
            "source": SOURCE_PROMPT,
            "input_variables": list(getattr(prompt, "input_variables", [])),
        }
    }


def pull_prompts_from_langsmith() -> bool:
    """
    Faz pull do prompt inicial do Hub e salva em prompts/bug_to_user_story_v1.yml.

    Returns:
        True se o prompt foi salvo, False caso contrário
    """
    prompt_key = SOURCE_PROMPT.split("/")[-1]

    print(f"Puxando prompt do LangSmith Hub: {SOURCE_PROMPT}")

    try:
        api_key = os.getenv("LANGSMITH_API_KEY") or None
        prompt = hub.pull(SOURCE_PROMPT, api_key=api_key)
    except Exception as e:
        print(f"❌ Erro ao puxar o prompt '{SOURCE_PROMPT}': {e}")
        print("\nVerifique:")
        print("- LANGSMITH_API_KEY está configurada corretamente no .env")
        print("- O prompt existe e está público em https://smith.langchain.com/hub")
        return False

    prompt_data = build_prompt_data(prompt, prompt_key)
    system_prompt = prompt_data[prompt_key]["system_prompt"]

    if not system_prompt.strip():
        print("❌ O prompt puxado não possui system prompt — nada a salvar.")
        return False

    print(f"   ✓ Prompt carregado ({len(system_prompt)} caracteres no system prompt)")
    print(f"   ✓ Variáveis de entrada: {prompt_data[prompt_key]['input_variables']}")

    if not save_yaml(prompt_data, str(OUTPUT_FILE)):
        return False

    print(f"   ✓ Salvo em {OUTPUT_FILE.relative_to(Path.cwd()) if OUTPUT_FILE.is_relative_to(Path.cwd()) else OUTPUT_FILE}")
    return True


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        print("⚠️  Seguindo sem credencial: só funciona porque o prompt de origem é público.\n")

    if not pull_prompts_from_langsmith():
        return 1

    print("\n✅ Pull concluído.")
    print("\nPróximos passos:")
    print("1. Analise o prompt em prompts/bug_to_user_story_v1.yml")
    print("2. Escreva a versão otimizada em prompts/bug_to_user_story_v2.yml")
    print("3. Publique: python src/push_prompts.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
