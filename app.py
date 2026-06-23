import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import json
import uuid
from datetime import datetime

# ==========================================
# БЕЗОПАСНАЯ ИНИЦИАЛИЗАЦИЯ ИЗ RAW JSON СТРОКИ
# ==========================================
if not firebase_admin._apps:
    try:
        # Достаем текст из секретов
        raw_json = st.secrets["FIREBASE_JSON_RAW"]
        firebase_config = json.loads(raw_json)

        # Принудительно чиним экранированные переносы строк для PEM-валидатора
        if "private_key" in firebase_config:
            firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")

        cred = credentials.Certificate(firebase_config)
        firebase_admin.initialize_app(cred)
    except Exception as e:
        st.error(f"Критическая ошибка конфигурации Firebase: {e}")

db = firestore.client()

# 2. Конфигурация страницы Streamlit
st.set_page_config(
    page_title="Большое исследование: Облачные заметки",
    layout="wide",
    page_icon="📝",
)

st.title("📝 Комплексное исследование: Экосистема облачных заметок")
st.markdown(
    "Уважаемый участник! Пожалуйста, ответьте на вопросы масштабного исследования. "
    "Анкета содержит 22 вопроса и детально изучает метрики синхронизации, совместной работы и безопасности."
)

# Разделяем интерфейс: Слева — огромная анкета, Справа — мощный Дашборд
col_form, col_dash = st.columns([1, 1])

# --- ЛЕВАЯ КОЛОНКА: АНКЕТА (22 ВОПРОСА) ---
with col_form:
    st.subheader("📋 Анкета респондента")

    with st.form("mega_survey_form", clear_on_submit=True):

        # === БЛОК 1: ДЕМОГРАФИЯ И ОБЩИЕ ДАННЫЕ (Вопросы 1-5) ===
        st.markdown("### 👤 Часть 1: Профиль пользователя")
        q1_city = st.text_input(
            "1. Укажите ваш город (Обязательно):", placeholder="Казань"
        ).strip()
        q2_age = st.number_input(
            "2. Укажите ваш возраст:", min_value=14, max_value=100, value=20
        )
        q3_occupation = st.selectbox(
            "3. Ваш основной род деятельности:",
            ["Студент", "Работаю в IT", "Работаю в другой сфере", "Фрилансер"],
        )
        q4_primary_app = st.selectbox(
            "4. Какое приложение для заметок у вас основное?",
            [
                "Notion",
                "Google Keep",
                "Apple Notes",
                "Obsidian",
                "Яндекс Заметки",
                "Microsoft OneNote",
                "Другое",
            ],
        )
        q5_experience = st.radio(
            "5. Как долго вы пользуетесь облачными заметками?",
            ["Меньше года", "1–2 года", "Более 3 лет"],
        )

        st.markdown("---")

        # === БЛОК 2: МЕТРИКА «СИНХРОНИЗАЦИЯ И ДОСТУПНОСТЬ» (Вопросы 6-11) ===
        st.markdown("### 🔄 Часть 2: Метрика «Синхронизация»")
        q6_frequency = st.select_slider(
            "6. Как часто вы открываете заметки?",
            options=[
                "Редко (раз в месяц)",
                "Пару раз в неделю",
                "Каждый день",
                "Несколько раз в день",
            ],
        )
        q7_devices = st.slider(
            "7. На скольких устройствах у вас настроены заметки? (кол-во)",
            1,
            5,
            2,
        )
        q8_offline = st.radio(
            "8. Нужен ли вам доступ к заметкам без интернета (офлайн)?",
            ["Да, это критично", "Иногда нужен", "Нет, интернет есть всегда"],
        )
        q9_sync_speed = st.slider(
            "9. Оцените скорость синхронизации в вашем приложении (1 — очень медленно, 10 — мгновенно):",
            1,
            10,
            8,
        )
        q10_sync_errors = st.radio(
            "10. Сталкивались ли вы с потерей данных из-за ошибок синхронизации?",
            ["Ни разу", "Редко (1-2 раза было)", "Да, регулярно"],
        )
        q11_web_version = st.radio(
            "11. Пользуетесь ли вы веб-версией заметок через браузер?",
            ["Да", "Нет, только приложениями"],
        )

        st.markdown("---")

        # === БЛОК 3: МЕТРИКА «СОВМЕСТНАЯ РАБОТА» (Вопросы 12-16) ===
        st.markdown("### 👥 Часть 3: Метрика «Совместная работа»")
        q12_collab_frequency = st.radio(
            "12. Как часто вы делитесь заметками с другими людьми?",
            ["Никогда", "Редко (для личных нужд)", "Постоянно по учебе/работе"],
        )
        q13_features = st.multiselect(
            "13. Какие командные функции вы реально используете? (Можно несколько):",
            [
                "Общие папки / блокноты",
                "Одновременный онлайн-формат редактирования",
                "Теги и упоминания (@пользователь)",
                "Оставление комментариев к тексту",
            ],
        )
        # Если ничего не выбрано, запишем дефолт
        if not q13_features:
            q13_features = ["Не использую"]

        q14_export = st.radio(
            "14. Важен ли для вас экспорт заметок в PDF, Markdown или DOCX?",
            ["Очень важен", "Иногда полезен", "Вообще не нужен"],
        )
        q15_comments_needed = st.radio(
            "15. Раздражает ли вас, когда другие меняют структуру вашей заметки?",
            ["Да", "Нейтрально", "Мы работаем слаженно"],
        )
        q16_links = st.radio(
            "16. Создаете ли вы публичные веб-ссылки на свои заметки?",
            ["Часто делюсь ссылками", "Редко", "Никогда"],
        )

        st.markdown("---")

        # === БЛОК 4: МЕТРИКА «БЕЗОПАСНОСТЬ И ХРАНЕНИЕ» (Вопросы 17-22) ===
        st.markdown("### 🛡️ Часть 4: Метрика «Безопасность»")
        q17_trust_level = st.slider(
            "17. Насколько вы доверяете облачному провайдеру хранение личных мыслей? (1-10):",
            1,
            10,
            7,
        )
        q18_sensitive_data = st.radio(
            "18. Храните ли вы в заметках пароли, пин-коды или сканы документов?",
            [
                "Нет, никогда",
                "Храню под паролем/биометрией внутри приложения",
                "Да, храню в открытом виде",
            ],
        )
        q19_2fa = st.radio(
            "19. Включена ли у вас двухфакторная аутентификация (2FA) на аккаунте заметок?",
            ["Да", "Нет", "Не знаю, что это"],
        )
        q20_backup = st.radio(
            "20. Делаете ли вы резервные копии (бэкапы) заметок на флешку или ПК?",
            ["Делаю регулярно", "Редко", "Никогда, доверяю облаку"],
        )
        q21_login_method = st.selectbox(
            "21. Как вы обычно входите в приложение на телефоне?",
            ["По биометрии (FaceID/Fingerprint)", "По ПИН-коду", "Без пароля"],
        )
        q22_feedback = st.text_area(
            "22. Опишите главный плюс или минус вашего текущего сервиса заметок (свободный ответ):"
        )

        submit_btn = st.form_submit_button("🔥 Отправить масштабную анкету")

        if submit_btn:
            if not q1_city:
                st.warning("Пожалуйста, заполните вопрос №1 (Укажите ваш город)!")
            else:
                # Упаковываем все 22 ответа в один словарь для Firestore
                mega_record = {
                    "city": q1_city,
                    "age": int(q2_age),
                    "occupation": q3_occupation,
                    "primary_app": q4_primary_app,
                    "experience": q5_experience,
                    "frequency": q6_frequency,
                    "devices": int(q7_devices),
                    "offline_need": q8_offline,
                    "sync_speed": int(q9_sync_speed),
                    "sync_errors": q10_sync_errors,
                    "web_version": q11_web_version,
                    "collab_frequency": q12_collab_frequency,
                    "features": q13_features,
                    "export_importance": q14_export,
                    "structure_irritation": q15_comments_needed,
                    "public_links": q16_links,
                    "trust_level": int(q17_trust_level),
                    "sensitive_data": q18_sensitive_data,
                    "two_factor": q19_2fa,
                    "backup_policy": q20_backup,
                    "login_method": q21_login_method,
                    "feedback": q22_feedback,
                    "submitted_at": datetime.utcnow(),
                }

                try:
                    # Сохраняем в Firebase в новую коллекцию для больших опросов
                    db.collection("mega_cloud_notes").add(mega_record)
                    st.success(
                        "Ура! Все 22 ответа успешно улетели в базу данных Firestore! 🎉"
                    )
                except Exception as e:
                    st.error(f"Ошибка сохранения: {e}")

# --- ПРАВАЯ КОЛОНКА: ПРОДВИНУТЫЙ ДАШБОРД ---
with col_dash:
    st.subheader("📊 Аналитическая система (Instructor Dashboard)")
    enable_dashboard = st.checkbox("Активировать аналитику реального времени")

    if enable_dashboard:
        # Тянем данные из Firebase
        docs = db.collection("mega_cloud_notes").stream()
        raw_data = [doc.to_dict() for doc in docs]

        if raw_data:
            df = pd.DataFrame(raw_data)

            # Общие метрики
            st.metric(label="📊 Всего заполнено анкет в БД:", value=len(df))

            # Табличный просмотр сырых ответов
            with st.expander("👀 Посмотреть сырую таблицу ответов (первые 5 строк)"):
                st.dataframe(df.head(5), use_container_width=True)

            st.markdown("### 📈 Анализ ключевых метрик темы")

            # График 1: Популярность приложений (Демография)
            st.markdown("**Какими приложениями чаще всего пользуются:**")
            fig1 = px.bar(
                df,
                x="primary_app",
                color="primary_app",
                title="Популярность сервисов заметок",
            )
            st.plotly_chart(fig1, use_container_width=True)

            # График 2: Доверие и Безопасность (Метрика Безопасность)
            st.markdown("**Уровень доверия облаку (Вопрос №17):**")
            fig2 = px.histogram(
                df,
                x="trust_level",
                nbins=10,
                color_discrete_sequence=["#059669"],
                labels={"trust_level": "Оценка доверия"},
            )
            fig2.update_layout(bargap=0.1)
            st.plotly_chart(fig2, use_container_width=True)

            # График 3: Скорость синхронизации (Метрика Синхронизация)
            st.markdown(
                "**Связь возраста и оценки скорости синхронизации (Scatter Plot):**"
            )
            fig3 = px.scatter(
                df,
                x="age",
                y="sync_speed",
                size="devices",
                color="primary_app",
                hover_data=["city"],
            )
            st.plotly_chart(fig3, use_container_width=True)

            # График 4: Использование совместной работы
            st.markdown("**Частота шеринга заметок (Вопрос №12):**")
            fig4 = px.pie(
                df,
                names="collab_frequency",
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            st.plotly_chart(fig4, use_container_width=True)

        else:
            st.info(
                "База данных пока пуста. Заполните и отправьте анкету слева, чтобы графики построились! 😎"
            )