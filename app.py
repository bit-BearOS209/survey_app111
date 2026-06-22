import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from datetime import datetime

# ==========================================
# ИНИЦИАЛИЗАЦИЯ FIREBASE (ИСПРАВЛЕННАЯ LOGIC)
# ==========================================
if not firebase_admin._apps:
    # Собираем конфигурацию из отдельных секретов Streamlit
    firebase_config = {
        "type": st.secrets["firebase"]["type"],
        "project_id": st.secrets["firebase"]["project_id"],
        "private_key_id": st.secrets["firebase"]["private_key_id"],
        # Важно: принудительно заменяем текстовые \\n на реальные переносы строк для криптографии
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
# НАСТРОЙКА СТРАНИЦЫ И СТИЛЕЙ
# ==========================================
st.set_page_config(page_title="Анкета", page_icon="📝", layout="centered")

st.markdown("""
    <style>
    .stApp {
        background-color: #0e1117;
        color: #ffffff;
    }
    div.stButton > button:first-child {
        background-color: #ff4b4b;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        font-weight: bold;
    }
    div.stButton > button:first-child:hover {
        background-color: #ff3333;
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📝 Анкета")

# Инициализация уникального ID сессии, чтобы ответы не сбрасывались
if "user_id" not in st.session_state:
    st.session_state["user_id"] = str(uuid.uuid4())

# ==========================================
# БЛОК ВОПРОСОВ (БЕЗ ИЗМЕНЕНИЙ)
# ==========================================
name = st.text_input("Как вас зовут?")
age = st.number_input("Сколько вам лет?", min_value=1, max_value=100, value=18)

q1 = st.radio("1. Какой ваш любимый цвет?", ["Красный", "Синий", "Зеленый", "Другой"])
q2 = st.selectbox("2. Какое ваше любимое время года?", ["Весна", "Лето", "Осень", "Зима"])
q3 = st.multiselect("3. Что вы предпочитаете на завтрак?", ["Кофе", "Чай", "Яичница", "Каша", "Фрукты"])
q4 = st.slider("4. Оцените ваш уровень энергии сегодня (от 1 до 10)", 1, 10, 5)

# ==========================================
# СОХРАНЕНИЕ ДАННЫХ В FIREBASE
# ==========================================
if st.button("Отправить ответы"):
    if name.strip() == "":
        st.warning("Пожалуйста, введите ваше имя перед отправкой.")
    else:
        with st.spinner("Сохранение ваших ответов..."):
            try:
                # Структурируем данные для Firestore
                data = {
                    "user_id": st.session_state["user_id"],
                    "name": name,
                    "age": age,
                    "q1": q1,
                    "q2": q2,
                    "q3": q3,
                    "q4": q4,
                    "timestamp": datetime.utcnow()  # Время отправки
                }

                # Записываем в коллекцию 'responses'
                db.collection("responses").document(st.session_state["user_id"]).set(data)
                st.success("🎉 Данные успешно сохранены в Firebase!")

            except Exception as e:
                st.error(f"❌ Ошибка при сохранении данных: {e}")