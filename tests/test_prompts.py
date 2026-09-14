"""
Testes automatizados para validação de prompts.
"""
import pytest
import re
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_KEY = "bug_to_user_story_v2"
PROMPT_FILE = Path(__file__).parent.parent / "prompts" / f"{PROMPT_KEY}.yml"
ROLE_MARKERS = ("você é um", "você é uma", "atue como", "assuma o papel")
FORMAT_MARKERS = ("como <persona>", "eu quero", "para que", "critérios de aceitação")
GIVEN_WHEN_THEN = ("dado que", "quando", "então")

def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

@pytest.fixture(scope="module")
def prompt():
    """Prompt otimizado carregado do YAML."""
    prompts = load_prompts(str(PROMPT_FILE))
    assert PROMPT_KEY in prompts, f"Prompt '{PROMPT_KEY}' ausente em {PROMPT_FILE}"
    return prompts[PROMPT_KEY]

class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt, "Campo 'system_prompt' ausente"
        assert prompt["system_prompt"].strip(), "Campo 'system_prompt' está vazio"

    def test_prompt_has_role_definition(self, prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        system_prompt = prompt["system_prompt"].lower()
        assert any(marker in system_prompt for marker in ROLE_MARKERS), (
            "O system_prompt não define uma persona para o modelo"
        )

    def test_prompt_mentions_format(self, prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt["system_prompt"].lower()

        for marker in FORMAT_MARKERS:
            assert marker in system_prompt, f"O prompt não exige o formato esperado: {marker!r}"

        for marker in GIVEN_WHEN_THEN:
            assert marker in system_prompt, (
                f"O prompt não pede critérios no padrão Dado/Quando/Então: {marker!r}"
            )

    def test_prompt_has_few_shot_examples(self, prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        system_prompt = prompt["system_prompt"]

        inputs = len(re.findall(r"^\s*Relato:\s*$", system_prompt, re.MULTILINE))
        outputs = len(re.findall(r"^\s*Resposta:\s*$", system_prompt, re.MULTILINE))

        assert inputs >= 2, f"Few-shot exige ao menos 2 exemplos de entrada, encontrados: {inputs}"
        assert outputs >= 2, f"Few-shot exige ao menos 2 exemplos de saída, encontrados: {outputs}"
        assert inputs == outputs, "Cada exemplo de entrada precisa ter a saída correspondente"

    def test_prompt_no_todos(self, prompt):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        for field, value in prompt.items():
            if isinstance(value, str):
                assert "TODO" not in value, f"Campo '{field}' ainda contém TODO"
                assert "[TODO]" not in value, f"Campo '{field}' ainda contém [TODO]"

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = prompt.get("techniques_applied", [])

        assert len(techniques) >= 2, f"Mínimo de 2 técnicas, encontradas: {len(techniques)}"
        assert any("few-shot" in technique.lower() for technique in techniques), (
            "Few-shot Learning é obrigatório no desafio"
        )

    def test_prompt_structure_is_valid(self, prompt):
        """Verifica a estrutura do prompt com o validador do projeto."""
        is_valid, errors = validate_prompt_structure(prompt)
        assert is_valid, f"Estrutura inválida: {errors}"

    def test_bug_report_variable_belongs_to_the_user_prompt(self, prompt):
        """Garante que a variável de entrada não está duplicada no system prompt."""
        assert "{bug_report}" in prompt["user_prompt"], "user_prompt precisa conter {bug_report}"
        assert "{bug_report}" not in prompt["system_prompt"], (
            "system_prompt não deve repetir {bug_report} — era o defeito da v1"
        )

    def test_prompt_handles_edge_cases(self, prompt):
        """Verifica se o prompt trata casos de borda explicitamente."""
        system_prompt = prompt["system_prompt"].lower()
        assert "edge case" in system_prompt or "casos de borda" in system_prompt, (
            "O prompt não documenta tratamento de edge cases"
        )

    def test_prompt_compiles_as_chat_template(self, prompt):
        """Garante que o prompt publicado renderiza com a variável do dataset."""
        from langchain_core.prompts import ChatPromptTemplate

        template = ChatPromptTemplate.from_messages([
            ("system", prompt["system_prompt"]),
            ("human", prompt["user_prompt"]),
        ])

        assert template.input_variables == ["bug_report"]

        messages = template.format_messages(bug_report="Botão de salvar não responde.")
        assert len(messages) == 2
        assert "Botão de salvar não responde." in messages[-1].content

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
