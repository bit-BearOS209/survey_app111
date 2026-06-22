import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import pandas as pd
import plotly.express as px
import streamlit as st

# =====================================================================
# 1. ИСПРАВЛЕННАЯ ИНИЦИАЛИЗАЦИЯ FIREBASE (Работает и дома, и в облаке)
# =====================================================================
if not firebase_admin._apps:
    # Вариант А: Если приложение запущено на сервере Streamlit Cloud
    if "firebase" in st.secrets:
        # Превращаем TOML-секреты обратно в словарь (JSON) в памяти
        firebase_config = dict(st.secrets["firebase"])

        # КРИТИЧЕСКИЙ МОМЕНТ: чиним символы переноса строки в приватном ключе
        if "private_key" in firebase_config:
            firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")

        # Передаем конфигурацию напрямую из памяти, без создания файлов на диске
        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)

    # Вариант Б: Если ты запускаешь проект локально на компьютере в PyCharm
    elif os.path.exists("serviceAccountKey.json"):
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)

    # Вариант В: Забыли прописать секреты и файла тоже нет
    else:
        st.error("Ошибка: Конфигурация Firebase не найдена ни в Secrets, ни в локальном JSON-файле.")
        st.stop()

db = firestore.client()
# =====================================================================


# 2. Настройка конфигурации страницы
st.set_page_config(
    page_title="Опрос: Облачные заметки", layout="wide", page_icon="📝"
)

st.title("📝 Исследование: Использование заметок в облаке")
st.markdown(
    "Пройдите масштабный опрос о том, как вы взаимодействуете с облачными сервисами заметок. "
    "Все данные сохраняются в облачную базу данных Firestore в реальном времени."
)

# Разделяем страницу на две колонки для визуального баланса
col1, col2 = st.columns([1, 1])

# 3. Форма опросника (Все 22 вопроса)
with col1:
    st.subheader("Заполните анкету")
    with st.form("survey_form", clear_on_submit=True):

        # === БЛОК 1: ПРОФИЛЬ ПОЛЬЗОВАТЕЛЯ ===
        st.markdown("### 👤 Часть 1: Профиль пользователя")
        city = st.text_input(
            "1. Укажите ваш город (Обязательно):", placeholder="Казань"
        ).strip()
        age = st.number_input(
            "2. Укажите ваш возраст:", min_value=14, max_value=100, value=20
        )
        occupation = st.selectbox(
            "3. Ваш основной род деятельности:",
            ["Студент", "Работаю", "Фрилансер"],
        )
        primary_app = st.selectbox(
            "4. Какое приложение для заметок у вас основное?",
            [
                "Notion",
                "Google Keep",
                "Apple Notes",
                "Яндекс Заметки",
                "Obsidian",
                "Microsoft OneNote",
                "Другое",
            ],
        )
        experience = st.radio(
            "5. Как долго вы пользуетесь облачными заметками?",
            ["Меньше года", "1–2 года", "Более 3 лет"],
        )

        # === БЛОК 2: МЕТРИКА «СИНХРОНИЗАЦИЯ» ===
        st.markdown("### 🔄 Часть 2: Метрика «Синхронизация»")
        usage_frequency = st.select_slider(
            "6. Как часто вы открываете заметки?",
            options=[
                "Редко",
                "Пару раз в неделю",
                "Каждый день",
                "Несколько раз в день",
            ],
        )
        devices = st.slider(
            "7. На скольких устройствах у вас настроены заметки? (кол-во)",
            1,
            5,
            2,
        )
        offline_need = st.radio(
            "8. Нужен ли вам доступ к заметкам без интернета (офлайн)?",
            ["Да, это критично", "Иногда нужен", "Нет, интернет есть всегда"],
        )
        sync_speed = st.slider(
            "9. Оцените скорость синхронизации в вашем приложении (1-10):",
            1,
            10,
            8,
        )
        sync_errors = st.radio(
            "10. Сталкивались ли вы с потерей данных из-за ошибок синхронизации?",
            ["Ни разу", "Редко (1-2 раза было)", "Да, регулярно"],
        )
        web_version = st.radio(
            "11. Пользуетесь ли вы веб-версией заметок через браузер?",
            ["Да", "Нет, только приложениями"],
        )

        # === БЛОК 3: МЕТРИКА «СОВМЕСТНАЯ РАБОТА» ===
        st.markdown("### 👥 Часть 3: Метрика «Совместная работа»")
        collab_frequency = st.radio(
            "12. Как часто вы делитесь заметками с другими людьми?",
            ["Никогда", "Редко (для личных нужд)", "Постоянно по учебе/работе"],
        )
        features = st.multiselect(
            "13. Какие командные функции вы используете? (Можно несколько):",
            [
                "Общие папки / блокноты",
                "Одновременный онлайн-формат редактирования",
                "Теги и упоминания (@пользователь)",
                "Оставление комментариев к тексту",
            ],
        )
        export_importance = st.radio(
            "14. Важен ли для вас экспорт заметок в PDF, Markdown или DOCX?",
            ["Очень важен", "Иногда полезен", "Вообще не нужен"],
        )
        structure_irritation = st.radio(
            "15. Раздражает ли вас, когда другие меняют структуру вашей заметки?",
            ["Да", "Нейтрально", "Мы работаем слаженно"],
        )
        public_links = st.radio(
            "16. Создаете ли вы публичные веб-ссылки на свои заметки?",
            ["Часто делюсь ссылками", "Редко", "Никогда"],
        )

        # === БЛОК 4: МЕТРИКА «БЕЗОПАСНОСТЬ» ===
        st.markdown("### 🛡️ Часть 4: Метрика «Безопасность»")
        confidence = st.slider(
            "17. Насколько вы уверены в безопасности своих данных в облаке? (1-10):",
            1,
            10,
            7,
        )
        sensitive_data = st.radio(
            "18. Храните ли вы в заметках пароли, пин-коды или сканы документов?",
            [
                "Нет, никогда",
                "Храню под паролем/биометрией внутри приложения",
                "Да, храню в открытом виде",
            ],
        )
        two_factor = st.radio(
            "19. Включена ли у вас двухфакторная аутентификация (2FA) на аккаунте заметок?",
            ["Да", "Нет", "Не знаю, что это"],
        )
        backup_policy = st.radio(
            "20. Делаете ли вы резервные копии (бэкапы) заметок на флешку или ПК?",
            ["Делаю регулярно", "Редко", "Никогда, доверяю облаку"],
        )
        login_method = st.selectbox(
            "21. Как вы обычно входите в приложение на телефоне?",
            ["По биометрии (FaceID/Fingerprint)", "По ПИН-коду", "Без пароля"],
        )
        comment = st.text_area(
            "22. Опишите главный плюс или минус вашего текущего сервиса заметок (свободный ответ):"
        )

        submit = st.form_submit_button("Отправить ответы")

        if submit:
            if not city:
                st.warning("Пожалуйста, заполните обязательное поле 'Город'!")
            else:
                # Формируем структуру документа для Firebase (все 22 поля)
                record = {
                    "city": city,
                    "age": int(age),
                    "occupation": occupation,
                    "primary_app": primary_app,
                    "experience": experience,
                    "usage_frequency": usage_frequency,
                    "devices": int(devices),
                    "offline_need": offline_need,
                    "sync_speed": int(sync_speed),
                    "sync_errors": sync_errors,
                    "web_version": web_version,
                    "collab_frequency": collab_frequency,
                    "features": features,
                    "export_importance": export_importance,
                    "structure_irritation": structure_irritation,
                    "public_links": public_links,
                    "confidence": int(confidence),
                    "sensitive_data": sensitive_data,
                    "two_factor": two_factor,
                    "backup_policy": backup_policy,
                    "login_method": login_method,
                    "comment": comment,
                    "time": datetime.utcnow(),
                }

                try:
                    # Добавление записи в коллекцию cloud_notes_survey
                    db.collection("cloud_notes_survey").add(record)
                    st.success(
                        "Успешно! Все 22 ответа сохранены в Firebase Firestore. 🎉"
                    )
                except Exception as e:
                    st.error(f"Ошибка при сохранении данных: {e}")

# 4. Аналитический Дашборд
with col2:
    st.subheader("📊 Аналитика результатов")
    show_analytics = st.checkbox("Показать Dashboard (Instructor View)")

    if show_analytics:
        # Извлекаем поток документов из нашей коллекции в Firebase
        docs = db.collection("cloud_notes_survey").stream()
        data = [doc.to_dict() for doc in docs]

        if data:
            df = pd.DataFrame(data)
            df["time"] = pd.to_datetime(df["time"])

            # Отображаем общее количество ответов
            st.metric(label="Всего собрано анкет", value=len(df))

            # Таблица со всеми ответами
            st.markdown("**Последние записи в БД:**")
            st.dataframe(df.head(10), use_container_width=True)

            st.markdown("---")

            # График 1: Распределение оценок доверия (Метрика Безопасность)
            st.markdown(
                "**Распределение уровня уверенности в безопасности (Вопрос №17):**"
            )
            fig_hist = px.histogram(
                df,
                x="confidence",
                nbins=10,
                labels={"confidence": "Уровень доверия"},
                color_discrete_sequence=["#4F46E5"],
            )
            fig_hist.update_layout(bargap=0.1)
            st.plotly_chart(fig_hist, use_container_width=True)

            # График 2: Частота использования (Метрика Синхронизация)
            st.markdown(
                "**Как часто пользователи заглядывают в заметки (Вопрос №6):**"
            )
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