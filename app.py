#!/usr/bin/env python3


import streamlit as st
import pandas as pd
from collections import Counter
from rag.indexer import load_index, search
from rag.pipeline import rag_query


# --- Page config ---
st.set_page_config(
    page_title="RAG по вакансиям hh.kz",
    page_icon="🔍",
    layout="wide",
)

st.title("🔍 RAG по вакансиям hh.kz")
st.caption("Семантический поиск и анализ IT-вакансий Казахстана")


# --- Load index (cached) ---
@st.cache_resource
def get_index():


    return load_index()


try:
    index, model, chunks = get_index()
except Exception as e:
    st.error(f"Не удалось загрузить индекс: {e}")
    st.info("Сначала запустите: `python build_index.py`")
    st.stop()


# --- Precompute metadata for filters ---
@st.cache_data
def get_metadata(_chunks):
    cities = sorted(set(c.get("area", "") for c in _chunks if c.get("area")))
    companies = sorted(set(c.get("employer", "") for c in _chunks if c.get("employer")))
    unique_vacancies = len(set(c["vacancy_id"] for c in _chunks))


    return cities, companies, unique_vacancies


cities, companies, n_vacancies = get_metadata(chunks)


def _format_salary(r: dict) -> str:
    """Format salary for display."""
    parts = []
    if r.get("salary_from"):
        parts.append(f"от {r['salary_from']:,}")
    if r.get("salary_to"):
        parts.append(f"до {r['salary_to']:,}")
    s = " ".join(parts)
    if s and r.get("salary_currency"):
        s += f" {r['salary_currency']}"


    return s


# ======= SIDEBAR =========
st.sidebar.header("⚙️ Настройки поиска")

top_k = st.sidebar.slider("Количество результатов", 3, 30, 10)

# --- Filters ---
st.sidebar.subheader("Фильтры")

filter_city = st.sidebar.selectbox("Город", ["Все"] + cities)
filter_salary = st.sidebar.number_input(
    "Мин. зарплата (KZT)", min_value=0, max_value=5_000_000, value=0, step=50_000,
    help="Показывать только вакансии с указанной зарплатой не ниже этого значения"
)
filter_experience = st.sidebar.selectbox(
    "Опыт",
    ["Любой", "Нет опыта", "От 1 до 3 лет", "От 3 до 6 лет", "Более 6 лет"],
)

# Build filters dict
filters = {}
if filter_city != "Все":
    filters["city"] = filter_city
if filter_salary > 0:
    filters["salary_min"] = filter_salary
if filter_experience != "Любой":
    filters["experience"] = filter_experience

# --- LLM ---
st.sidebar.markdown("---")
st.sidebar.subheader("🤖 LLM")

llm_backend = st.sidebar.selectbox(
    "Backend",
    ["none", "ollama", "openai"],
    help="none = только поиск без генерации ответа",
)

llm_model = ""
api_key = ""
if llm_backend == "ollama":
    llm_model = st.sidebar.text_input("Ollama model", "qwen2.5:3b")
elif llm_backend == "openai":
    llm_model = st.sidebar.text_input("OpenAI model", "gpt-4o-mini")
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")

# --- Stats ---
st.sidebar.markdown("---")
st.sidebar.subheader("📊 База данных")
col1, col2 = st.sidebar.columns(2)
col1.metric("Вакансий", n_vacancies)
col2.metric("Компаний", len(companies))
st.sidebar.metric("Городов", len(cities))
st.sidebar.metric("Чанков в индексе", index.ntotal)


# ======== MAIN AREA ==========

# --- Tabs ---
tab_search, tab_analytics = st.tabs(["🔍 Поиск", "📊 Аналитика"])

# ========== TAB: SEARCH =========
with tab_search:
    # Example queries
    examples = [
        "Python-разработчик в Алматы",
        "Навыки для Data Science",
        "Backend с зарплатой от 500K",
        "Сравни требования ML-вакансий",
    ]
    cols = st.columns(len(examples))
    for col, ex in zip(cols, examples):
        if col.button(ex, use_container_width=True):
            st.session_state["query"] = ex

    query = st.text_input(
        "Задайте вопрос по вакансиям:",
        value=st.session_state.get("query", ""),
        placeholder="Например: Какие навыки чаще всего требуют для Backend?",
    )

    if query:
        with st.spinner("Ищу релевантные вакансии..."):
            results = search(query, index, model, chunks, top_k=top_k, filters=filters if filters else None)

        if not results:
            st.warning("Ничего не найдено. Попробуйте изменить фильтры или запрос.")
        else:
            # --- LLM answer ---
            if llm_backend != "none":
                with st.spinner("🤖 Генерирую ответ..."):
                    try:
                        kwargs = {}
                        if llm_backend == "openai" and api_key:
                            kwargs["api_key"] = api_key
                        response = rag_query(
                            query, index, model, chunks,
                            llm_backend=llm_backend,
                            llm_model=llm_model,
                            top_k=top_k,
                            **kwargs,
                        )
                        st.markdown("### 🤖 Ответ AI")
                        st.info(response["answer"])
                    except Exception as e:
                        st.error(f"Ошибка LLM: {e}")

            # --- Results header --
            # Deduplicate
            seen = set()
            unique_results = []
            for r in results:
                vid = r["vacancy_id"]
                if vid not in seen:
                    seen.add(vid)
                    unique_results.append(r)

            st.markdown(f"### Найдено: {len(unique_results)} вакансий")
            if filters:
                active = []
                if filters.get("city"):
                    active.append(f"город: {filters['city']}")
                if filters.get("salary_min"):
                    active.append(f"зарплата ≥ {filters['salary_min']:,} KZT")
                if filters.get("experience"):
                    active.append(f"опыт: {filters['experience']}")
                st.caption(f"Фильтры: {' | '.join(active)}")

            # --- Vacancy cards ---
            for r in unique_results:
                sal_str = _format_salary(r)
                score_pct = int(r["score"] * 100)

                with st.container(border=True):
                    c1, c2 = st.columns([4, 1])
                    with c1:
                        st.markdown(f"#### {r['vacancy_name']}")
                        st.markdown(f"🏢 **{r['employer']}** &nbsp;|&nbsp; 📍 {r['area']}"
                                    + (f" &nbsp;|&nbsp; 💰 {sal_str}" if sal_str else ""))
                    with c2:
                        st.metric("Релевантность", f"{score_pct}%")


                    with st.expander("Подробнее"):
                        st.markdown(r["text"])
                        url = r.get("url", "")
                        if url:
                            st.link_button("Открыть на hh.kz", url)


#========== TAB: ANALYTICS ========
with tab_analytics:
    st.markdown("### 📊 Аналитика по базе вакансий")

    # City distribution
    city_counts = Counter(c.get("area", "Не указан") for c in chunks if c.get("chunk_index", 0) == 0)
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Вакансии по городам**")
        st.bar_chart({k: v for k, v in city_counts.most_common(15)})

    # Companies with most vacancies
    company_counts = Counter(c.get("employer", "") for c in chunks if c.get("chunk_index", 0) == 0)
    with col_b:
        st.markdown("**Топ-15 компаний**")
        st.bar_chart({k: v for k, v in company_counts.most_common(15)})

    # Salary analysis
    st.markdown("---")
    st.markdown("**Анализ зарплат**")
    salaries = []
    for c in chunks:
        if c.get("chunk_index", 0) != 0:
            continue
        sal_from = c.get("salary_from") or 0
        sal_to = c.get("salary_to") or 0
        best = max(sal_from, sal_to)
        if best > 0:
            salaries.append({
                "vacancy": c.get("vacancy_name", ""),
                "company": c.get("employer", ""),
                "salary": best,
                "currency": c.get("salary_currency", ""),
            })

    if salaries:
        df_sal = pd.DataFrame(salaries)
        kzt = df_sal[df_sal["currency"] == "KZT"]
        if not kzt.empty:
            col_s1, col_s2, col_s3 = st.columns(3)
            col_s1.metric("Мин. зарплата (KZT)", f"{int(kzt['salary'].min()):,}")
            col_s2.metric("Медиана (KZT)", f"{int(kzt['salary'].median()):,}")
            col_s3.metric("Макс. зарплата (KZT)", f"{int(kzt['salary'].max()):,}")

            st.bar_chart(kzt["salary"].value_counts().sort_index())

        st.markdown(f"Вакансий с указанной зарплатой: **{len(salaries)}** из {n_vacancies} ({100 * len(salaries) // max(n_vacancies, 1)}%)")
    else:
        st.info("Нет вакансий с указанной зарплатой.")


    # Skills word cloud (text-based   
    st.markdown("---")
    st.markdown("**Топ навыков (key_skills)**")
    all_skills = []
    for c in chunks:
        text = c.get("text", "")
        try:
            if "Ключевые навыки:" in text:
                skills_line = text.split("Ключевые навыки:")[1].split("\n")[0].strip()
                for skill in skills_line.split(","):
                    s = skill.strip()
                    if s:
                        all_skills.append(s)
        except (IndexError, ValueError):
            continue

    if all_skills:
        skill_counts = Counter(all_skills)
        df_skills = pd.DataFrame(skill_counts.most_common(25), columns=["Навык", "Кол-во"])
        st.dataframe(df_skills, width="stretch", hide_index=True)
    else:
        st.info("Нет данных по навыкам.")
