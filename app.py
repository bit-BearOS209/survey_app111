import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import plotly.express as px
import streamlit as st

# 1. Инициализация Firebase (выполняется один раз за сессию)
KEY_PATH = os.getenv("FIREBASE_KEY", "serviceAccountKey.json")

if not firebase_admin._apps:
    if not os.path.exists(KEY_PATH):
        st.error(
            "Ошибка: Файл serviceAccountKey.json не найден в корневой директории."
        )
        st.stop()
    cred = credentials.Certificate(KEY_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# 2. Настройка конфигурации страницы
st.set_page_config(
    page_title="Опрос: Облачные заметки", layout="wide", page_icon="📝"
)

st.title("📝 Исследование: Использование заметок в облаке")
st.markdown(
    "Пройдите короткий опрос о том, как вы взаимодействуете с облачными сервисами заметок. "
    "Все данные сохраняются в облачную базу данных Firestore в реальном времени."
)

# Разделяем страницу на две колонки для визуального баланса
col1, col2 = st.columns([1, 1])

# 3. Форма опросника (Тема 41)
with col1:
    st.subheader("Заполните анкету")
    with st.form("survey_form", clear_on_submit=True):
        city = st.text_input("Укажите ваш город (обязательно):").strip()

        education = st.radio(
            "Ваш уровень образования:",
            ["Среднее", "Среднее профессиональное", "Высшее", "Другое"],
        )

        st.markdown("---")

        # Метрика: Синхронизация и частота использования
        usage_frequency = st.select_slider(
            "Как часто вы используете облачные заметки?",
            options=[
                "Редко",
                "Несколько раз в месяц",
                "Раз в неделю",
                "Каждый день",
            ],
            value="Раз в неделю",
        )

        # Метрика: Совместная работа (выбор нескольких вариантов)
        features = st.multiselect(
            "Какие функции для совместной работы вы используете?",
            [
                "Общие блокноты / папки",
                "Одновременное редактирование текста",
                "Оставление комментариев / тегов",
                "Поделиться ссылкой на просмотр",
                "Ничего из перечисленного",
            ],
        )

        # Метрика: Безопасность и доверие (Оценка от 1 до 10)
        confidence = st.slider(
            "Насколько вы уверены в безопасности своих данных в облаке? (1-10)",
            1,
            10,
            5,
        )

        comment = st.text_area(
            "Каким приложением для заметок вы чаще всего пользуетесь и почему?"
        )

        submit = st.form_submit_button("Отправить ответы")

        if submit:
            if not city:
                st.warning("Пожалуйста, заполните обязательное поле 'Город'!")
            else:
                # Формируем структуру документа для Firebase
                record = {
                    "city": city,
                    "education": education,
                    "usage_frequency": usage_frequency,
                    "features": features,
                    "confidence": int(confidence),
                    "comment": comment,
                    "time": datetime.utcnow(),  # временная метка для аналитики
                }

                try:
                    # Добавление записи в коллекцию cloud_notes_survey
                    db.collection("cloud_notes_survey").add(record)
                    st.success(
                        "Успешно! Ваши ответы сохранены в Firebase Firestore."
                    )
                except Exception as e:
                    st.error(f"Ошибка при сохранении данных: {e}")

# 4. Аналитический Дашборд (Панель преподавателя / исследователя)
with col2:
    st.subheader("📊 Аналитика результатов")
    show_analytics = st.checkbox("Показать Dashboard (Instructor View)")

    if show_analytics:
        # Извлекаем поток документов из нашей коллекции в Firebase
        docs = db.collection("cloud_notes_survey").stream()
        data = [doc.to_dict() for doc in docs]

        if data:
            # Превращаем сырой массив словарей в структурированный DataFrame
            df = pd.DataFrame(data)

            # Приведение времени к формату pandas datetime для корректного отображения
            df["time"] = pd.to_datetime(df["time"])

            # Отображаем общее количество ответов
            st.metric(label="Всего собрано анкет", value=len(df))

            # Таблица с последними ответами (первые 5 строк)
            st.markdown("**Последние 5 записей в БД:**")
            st.dataframe(df.head(5), use_container_width=True)

            st.markdown("---")

            # График 1: Распределение оценок доверия (Безопасность)
            st.markdown("**Распределение уровня доверия безопасности (1-10):**")
            fig_hist = px.histogram(
                df,
                x="confidence",
                nbins=10,
                labels={"confidence": "Уровень доверия"},
                color_discrete_sequence=["#4F46E5"],
            )
            fig_hist.update_layout(bargap=0.1)
            st.plotly_chart(fig_hist, use_container_width=True)

            # График 2: Частота использования (Синхронизация)
            st.markdown("**Как часто пользователи заглядывают в заметки:**")
            fig_pie = px.pie(
                df,
                names="usage_frequency",
                color_discrete_sequence=px.colors.sequential.RdBu,
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        else:
            st.info(
                "В базе данных пока нет ответов. Заполните форму слева, чтобы появились графики!"
            )