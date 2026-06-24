import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from datetime import datetime
import pandas as pd
import plotly.express as px

# Переменная для проверки статуса базы
db = None

# ==========================================
# ИНИЦИАЛИЗАЦИЯ НАПРЯМУЮ ИЗ TOML SECRETS С ДИАГНОСТИКОЙ
# ==========================================
if not firebase_admin._apps:
    try:
        # Проверяем, заполнил ли ты Secrets вообще
        if not st.secrets:
            st.error("⚠️ Внимание: Панель Secrets в Streamlit Cloud абсолютно пустая!")
        else:
            # Проверяем наличие главного поля
            if "private_key" not in st.secrets:
                st.error("⚠️ В Secrets нет поля 'private_key'! Проверь правильность названий.")

            # Собираем словарь из Secrets
            firebase_config = {
                "type": st.secrets.get("type", "service_account"),
                "project_id": st.secrets.get("project_id", ""),
                "private_key_id": st.secrets.get("private_key_id", ""),
                "private_key": st.secrets.get("private_key", ""),
                "client_email": st.secrets.get("client_email", ""),
                "client_id": st.secrets.get("client_id", ""),
                "auth_uri": st.secrets.get("auth_uri", "https://accounts.google.com/o/oauth2/auth"),
                "token_uri": st.secrets.get("token_uri", "https://oauth2.googleapis.com/token"),
                "auth_provider_x509_cert_url": st.secrets.get("auth_provider_x509_cert_url", ""),
                "client_x509_cert_url": st.secrets.get("client_x509_cert_url", ""),
                "universe_domain": st.secrets.get("universe_domain", "googleapis.com")
            }

            # Попытка авторизации
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
            db = firestore.client()

    except Exception as e:
        st.error(f"❌ Ошибка внутри блока инициализации: {e}")
        st.info("Это означает, что формат твоего private_key в Secrets не нравится библиотеке криптографии.")
else:
    db = firestore.client()

# ==========================================
# КОНФИГУРАЦИЯ СТРАНИЦЫ
# ==========================================
st.set_page_config(
    page_title="Исследование: Облачные заметки",
    layout="wide",
    page_icon="📝",
)

st.title("📝 Исследование: Экосистема облачных заметок")
st.markdown("Уважаемый участник! Пожалуйста, ответьте на 7 вопросов исследования.")

col_form, col_dash = st.columns([1, 1])

# ==========================================
# ЛЕВАЯ КОЛОНКА: АНКЕТА
# ==========================================
with col_form:
    st.subheader("📋 Анкета респондента")

    with st.form("survey_form", clear_on_submit=True):

        q1_city = st.text_input(
            "1. Укажите ваш город (Обязательно):", placeholder="Казань"
        ).strip()

        q2_primary_app = st.selectbox(
            "2. Какое приложение для заметок у вас основное?",
            ["Notion", "Google Keep", "Apple Notes", "Obsidian", "Яндекс Заметки", "Microsoft OneNote", "Другое"],
        )

        q3_experience = st.radio(
            "3. Как долго вы пользуетесь облачными заметками?",
            ["Меньше года", "1–2 года", "Более 3 лет"],
        )

        q4_devices = st.slider(
            "4. На скольких устройствах у вас настроены заметки?",
            1, 5, 2,
        )

        q5_sync_speed = st.slider(
            "5. Оцените скорость синхронизации (1 — медленно, 10 — мгновенно):",
            1, 10, 8,
        )

        q6_trust_level = st.slider(
            "6. Насколько вы доверяете облачному провайдеру? (1-10):",
            1, 10, 7,
        )

        q7_feedback = st.text_area(
            "7. Опишите главный плюс или минус вашего сервиса заметок:"
        )

        submit_btn = st.form_submit_button("🔥 Отправить анкету")

        if submit_btn:
            if not q1_city:
                st.warning("Пожалуйста, заполните вопрос №1 (Укажите ваш город)!")
            else:
                record = {
                    "city": q1_city,
                    "primary_app": q2_primary_app,
                    "experience": q3_experience,
                    "devices": int(q4_devices),
                    "sync_speed": int(q5_sync_speed),
                    "trust_level": int(q6_trust_level),
                    "feedback": q7_feedback,
                    "submitted_at": datetime.utcnow(),
                }
                try:
                    db.collection("cloud_notes_survey").add(record)
                    st.success("Ура! Ответы успешно сохранены в базе данных! 🎉")
                except Exception as e:
                    import traceback

                    st.error(f"Ошибка сохранения: {e}")
                    st.code(traceback.format_exc())

# ==========================================
# ПРАВАЯ КОЛОНКА: ДАШБОРД
# ==========================================
with col_dash:
    st.subheader("📊 Аналитика (Dashboard)")
    enable_dashboard = st.checkbox("Активировать аналитику реального времени")

    if enable_dashboard:
        raw_data = []
        try:
            docs = db.collection("cloud_notes_survey").stream()
            raw_data = [doc.to_dict() for doc in docs]
        except Exception as e:
            st.error(f"Ошибка загрузки данных: {e}")

        if raw_data:
            df = pd.DataFrame(raw_data)

            st.metric(label="📊 Всего анкет в базе:", value=len(df))

            with st.expander("👀 Таблица ответов (первые 5 строк)"):
                st.dataframe(df.head(5), use_container_width=True)

            st.markdown("### 📈 Графики")

            st.markdown("**Популярность приложений для заметок:**")
            fig1 = px.bar(df, x="primary_app", color="primary_app",
                          title="Какими приложениями пользуются")
            st.plotly_chart(fig1, use_container_width=True)

            st.markdown("**Уровень доверия облаку:**")
            fig2 = px.histogram(df, x="trust_level", nbins=10,
                                color_discrete_sequence=["#059669"],
                                labels={"trust_level": "Оценка доверия"})
            fig2.update_layout(bargap=0.1)
            st.plotly_chart(fig2, use_container_width=True)

            st.markdown("**Скорость синхронизации по приложениям:**")
            fig3 = px.box(df, x="primary_app", y="sync_speed",
                          color="primary_app",
                          title="Оценка синхронизации по сервисам")
            st.plotly_chart(fig3, use_container_width=True)

            st.markdown("**Опыт использования:**")
            fig4 = px.pie(df, names="experience", hole=0.4,
                          color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig4, use_container_width=True)

        else:
            st.info("База данных пока пуста. Заполните анкету слева!")