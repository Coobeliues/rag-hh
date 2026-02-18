
from rag.pipeline import format_context, SYSTEM_PROMPT, RAG_PROMPT_TEMPLATE


class TestFormatContext:
    def _result(self, vid, name="Dev", employer="Co", area="Алматы", text="описание"):
        return {
            "vacancy_id": vid,
            "vacancy_name": name,
            "employer": employer,
            "area": area,
            "text": text,
            "score": 0.95,
        }

    def test_basic_formatting(self):
        results = [self._result("1", name="Python Dev", employer="TestCo")]
        ctx = format_context(results)
        assert "Python Dev" in ctx
        assert "TestCo" in ctx

    def test_deduplication(self):
        results = [
            self._result("1", text="chunk 1"),
            self._result("1", text="chunk 2"),  # same vacancy_id
            self._result("2", text="chunk 3"),
        ]
        ctx = format_context(results)
        # Should only have 2 vacancies, not 3
        assert ctx.count("[Вакансия:") == 2

    def test_max_chunks_limit(self):
        results = [self._result(str(i)) for i in range(20)]
        ctx = format_context(results, max_chunks=3)
        assert ctx.count("[Вакансия:") == 3

    def test_empty_results(self):
        ctx = format_context([])
        assert ctx == ""


class TestPromptTemplates:
    def test_system_prompt_in_russian(self):
        assert "hh.kz" in SYSTEM_PROMPT
        assert "русский" in SYSTEM_PROMPT

    def test_rag_template_has_placeholders(self):
        assert "{context}" in RAG_PROMPT_TEMPLATE
        assert "{question}" in RAG_PROMPT_TEMPLATE

    def test_rag_template_formats(self):
        filled = RAG_PROMPT_TEMPLATE.format(context="тест контекст", question="тест вопрос")
        assert "тест контекст" in filled
        assert "тест вопрос" in filled





