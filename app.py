import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from datetime import datetime

# ==========================================
# ИНИЦИАЛИЗАЦИЯ FIREBASE (ИСПРАВЛЕННЫЙ ВАРИАНТ)
# ==========================================
if not firebase_admin._apps:
    firebase_config = {
        "type": st.secrets["firebase"]["type"],
        "project_id": st.secrets["firebase"]["project_id"],
        "private_key_id": st.secrets["firebase"]["private_key_id"],
        # Очистка экранирования для исключения ошибки Invalid JWT Signature
        "private_key": st.secrets["firebase"]["private_key"].replace("\\n", "\n"),
        "client_email": st.secrets["firebase"]["client_email"],
        "client_id": st.secrets["firebase"]["client_id"],
        "auth_uri": st.secrets["firebase"]["auth_uri"],
        "token_uri": st.secrets["firebase"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
        "universe_domain": st.secrets["firebase"]["universe_domain"]
    }

    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ==========================================
# НАСТРОЙКА ИНТЕРФЕЙСА
# ==========================================
st.set_page_config(page_title="Большой опросник", page_icon="📝", layout="centered")

st.title("📝 Тестирование / Анкета из 22 вопросов")
st.write("Пожалуйста, ответьте на все вопросы честно и внимательно.")

if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())

# ==========================================
# ПОЛЯ ПРОФИЛЯ
# ==========================================
st.subheader("📋 Личные данные")
name = st.text_input("Как вас зовут?", key="user_name")
age = st.number_input("Сколько вам лет?", min_value=1, max_value=120, value=18, key="user_age")

st.markdown("---")

# ==========================================
# ПОЛНЫЙ БЛОК ИЗ 22 ВОПРОСОВ
# ==========================================
st.subheader("❓ Вопросы")

q1 = st.radio("1. Какой ваш любимый цвет?", ["Красный", "Синий", "Зеленый", "Другой"], key="q1")
q2 = st.selectbox("2. Какое ваше любимое время года?", ["Весна", "Лето", "Осень", "Зима"], key="q2")
q3 = st.multiselect("3. Что вы предпочитаете на завтрак?", ["Кофе", "Чай", "Яичница", "Каша", "Фрукты"], key="q3")
q4 = st.slider("4. Оцените ваш уровень энергии сегодня (от 1 до 10)", 1, 10, 5, key="q4")
q5 = st.radio("5. Какой тип отдыха вы предпочитаете?",
              ["Активный (спорт, походы)", "Пассивный (пляж, книги)", "Культурный (музеи, театры)"], key="q5")
q6 = st.selectbox("6. Какая операционная система вам ближе?", ["Android", "iOS", "Windows", "Linux / macOS"], key="q6")
q7 = st.radio("7. Любите ли вы программирование?", ["Да, очень", "Только учусь", "Это просто работа / учеба", "Нет"],
              key="q7")
q8 = st.slider("8. Сколько часов в день вы проводите за компьютером?", 1, 24, 8, key="q8")
q9 = st.selectbox("9. Какой жанр кино вам нравится больше всего?",
                  ["Фантастика / Экшен", "Драма / Мелодрама", "Комедия", "Ужасы / Триллер"], key="q9")
q10 = st.radio("10. Как вы относитесь к командной работе?",
               ["Предпочитаю работать один", "Комфортно в небольшой команде", "Люблю большие проекты"], key="q10")
q11 = st.text_input("11. Опишите кратко ваш идеальный день:", key="q11")
q12 = st.radio("12. Что для вас важнее в работе?",
               ["Интересные задачи", "Высокая зарплата", "Гибкий график / удаленка", "Хороший коллектив"], key="q12")
q13 = st.selectbox("13. Как часто вы занимаетесь спортом или физической активностью?",
                   ["Каждый день", "2-3 раза в неделю", "Раз в неделю", "Редко / Не занимаюсь"], key="q13")
q14 = st.slider("14. Оцените ваш уровень стресса за последнюю неделю (от 1 до 10)", 1, 10, 5, key="q14")
q15 = st.radio("15. Какую музыку вы предпочитаете во время работы/учебы?",
               ["Поп / Рок", "Лоу-фай / Инструментальная", "Фоновый шум / Тишина", "Электронная"], key="q15")
q16 = st.selectbox("16. Какой ваш основной язык программирования на данный момент?",
                   ["Python", "C++", "Java", "JavaScript / Другой"], key="q16")
q17 = st.radio("17. Хотели бы вы в будущем сменить место жительства / переехать?",
               ["Да, определенно", "Пока не думал(а) об этом", "Нет, меня всё устраивает"], key="q17")
q18 = st.slider("18. Насколько вы довольны своей текущей успеваемостью или продуктивностью? (от 1 до 10)", 1, 10, 7,
                key="q18")
q19 = st.text_input("19. Какая ваша главная профессиональная цель на этот год?", key="q19")
q20 = st.radio("20. Вы предпочитаете бумажные книги или электронные/аудиоформаты?",
               ["Бумажные", "Электронные", "Аудиокниги", "Редко читаю книги"], key="q20")
q21 = st.selectbox("21. Какой формат обучения вам кажется наиболее эффективным?",
                   ["Очные лекции и практика", "Онлайн-курсы в записи", "Самостоятельное чтение документации"],
                   key="q21")
q22 = st.text_area("22. Ваши пожелания или дополнительные комментарии к анкете:", key="q22")

st.markdown("---")

# ==========================================
# ОТПРАВКА В БАЗУ ДАННЫХ
# ==========================================
if st.button("Отправить анкету"):
    if name.strip() == "":
        st.warning("Пожалуйста, заполните поле с вашим именем перед отправкой.")
    else:
        with st.spinner("Сохранение анкеты в Firebase..."):
            try:
                # Формируем полный пакет из 22 ответов
                responses_data = {
                    "user_id": st.session_state["user_id"],
                    "name": name,
                    "age": age,
                    "git add app.pytimestamp": datetime.utcnow(),
                    "q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5,
                    "q6": q6, "q7": q7, "q8": q8, "q9": q9, "q10": q10,
                    "q11": q11, "q12": q12, "q13": q13, "q14": q14, "q15": q15,
                    "q16": q16, "q17": q17, "q18": q18, "q19": q19, "q20": q20,
                    "q21": q21, "q22": q22
                }

                # Запись в Firebase Firestore
                db.collection("responses").document(st.session_state["user_id"]).set(responses_data)
                st.success("🎉 Ура! Все 22 вопроса и профиль успешно сохранены в Firebase!")

            except Exception as e:
                st.error(f"❌ Произошла ошибка отправки: {e}")