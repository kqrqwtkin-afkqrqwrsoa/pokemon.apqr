# pip install streamlit requests
# streamlit run app.py

# -*- coding: utf-8 -*-
"""
Веб-приложение "Покедекс" на Streamlit + PokeAPI (https://pokeapi.co).

Установка и запуск:
    pip install streamlit requests
    streamlit run app.py

Возможности:
  - Ввод имени или ID покемона
  - По кнопке показывает: имя и ID, типы (на русском), рост и вес,
    среду обитания (на русском), питание / held items (ягоды отдельно)
  - Красивое оформление, обработка ошибок (не найден, проблемы с сетью)
"""

from typing import Dict, List, Optional, Tuple

import requests
import streamlit as st


BASE_URL = "https://pokeapi.co/api/v2"

# Перевод типов на русский
TYPE_TRANSLATION = {
    "normal": "Обычный",
    "fire": "Огненный",
    "water": "Водный",
    "electric": "Электрический",
    "grass": "Травяной",
    "ice": "Ледяной",
    "fighting": "Боевой",
    "poison": "Ядовитый",
    "ground": "Земляной",
    "flying": "Летающий",
    "psychic": "Психический",
    "bug": "Насекомый",
    "rock": "Каменный",
    "ghost": "Призрачный",
    "dragon": "Драконий",
    "dark": "Тёмный",
    "steel": "Стальной",
    "fairy": "Волшебный",
    "stellar": "Звёздный",
    "unknown": "Неизвестный",
    "shadow": "Теневой",
}

# Перевод среды обитания (habitat) на русский
HABITAT_TRANSLATION = {
    "cave": "Пещера",
    "forest": "Лес",
    "grassland": "Луг / степь",
    "mountain": "Горы",
    "rare": "Редкая местность",
    "rough-terrain": "Пересечённая местность",
    "sea": "Море",
    "urban": "Город",
    "waters-edge": "Берег водоёма",
}

# Эмодзи для типов (для красивого оформления)
TYPE_EMOJI = {
    "normal": "⚪",
    "fire": "🔥",
    "water": "💧",
    "electric": "⚡",
    "grass": "🌿",
    "ice": "❄️",
    "fighting": "🥊",
    "poison": "☠️",
    "ground": "🌍",
    "flying": "🕊️",
    "psychic": "🔮",
    "bug": "🐛",
    "rock": "🪨",
    "ghost": "👻",
    "dragon": "🐉",
    "dark": "🌑",
    "steel": "⚙️",
    "fairy": "✨",
    "stellar": "🌟",
    "unknown": "❓",
    "shadow": "🌘",
}


def fetch_json(url: str) -> dict:
    """GET-запрос с понятными исключениями для Streamlit-обработки."""
    try:
        response = requests.get(url, timeout=10)
    except requests.exceptions.ConnectionError:
        raise ConnectionError("Нет соединения с интернетом или API недоступен.")
    except requests.exceptions.Timeout:
        raise TimeoutError("Превышено время ожидания ответа от PokeAPI.")
    except requests.exceptions.RequestException as exc:
        raise ConnectionError(f"Сетевая ошибка: {exc}")

    if response.status_code == 404:
        raise ValueError("Покемон не найден. Проверьте имя или ID.")
    if not response.ok:
        raise ConnectionError(f"Ошибка API: HTTP {response.status_code}.")

    return response.json()


@st.cache_data(show_spinner=False, ttl=3600)
def get_pokemon(name_or_id: str) -> dict:
    """Основные данные покемона из /pokemon/. Кэшируется на час."""
    url = f"{BASE_URL}/pokemon/{str(name_or_id).lower().strip()}"
    return fetch_json(url)


@st.cache_data(show_spinner=False, ttl=3600)
def get_species(poke_id: int) -> dict:
    """Данные о виде из /pokemon-species/ (отсюда берём habitat)."""
    url = f"{BASE_URL}/pokemon-species/{poke_id}"
    return fetch_json(url)


def translate_type(type_name: str) -> str:
    """Перевод английского типа на русский."""
    return TYPE_TRANSLATION.get(type_name.lower(), type_name)


def translate_habitat(habitat_name: Optional[str]) -> str:
    """Перевод habitat на русский."""
    if not habitat_name:
        return "Неизвестна (в API нет данных)"
    return HABITAT_TRANSLATION.get(habitat_name.lower(), habitat_name)


def split_held_items(held_items: list) -> Tuple[List[str], List[str]]:
    """Делит held_items на ягоды и прочие предметы.

    В PokeAPI ягоды обычно заканчиваются на '-berry':
    'oran-berry', 'sitrus-berry' и т.д.
    """
    berries: List[str] = []
    others: List[str] = []
    for entry in held_items:
        item_name = entry.get("item", {}).get("name", "неизвестно")
        if "berry" in item_name.lower():
            berries.append(item_name)
        else:
            others.append(item_name)
    return berries, others


def get_ru_species_name(species: dict, fallback: str) -> str:
    """Пытается достать русское имя из species['names'], иначе — fallback."""
    for entry in species.get("names", []):
        lang = entry.get("language", {}).get("name")
        if lang == "ru" and entry.get("name"):
            return entry["name"]
    return fallback.capitalize()


def get_sprite(pokemon: dict) -> Optional[str]:
    """Возвращает URL лучшего доступного спрайта."""
    sprites = pokemon.get("sprites", {}) or {}
    other = sprites.get("other") or {}
    artwork = (other.get("official-artwork") or {}).get("front_default")
    if artwork:
        return artwork
    if sprites.get("front_default"):
        return sprites["front_default"]
    return None


# ------------------------- Интерфейс -------------------------

st.set_page_config(
    page_title="Покедекс — поиск покемона",
    page_icon="🐾",
    layout="centered",
)

st.title("🐾 Покедекс")
st.markdown(
    "Веб-приложение на **Streamlit** + [PokeAPI](https://pokeapi.co).  \n"
    "Введите имя (на английском, например `pikachu`) или ID (например `25`) "
    "и нажмите кнопку **«Найти покемона»**."
)

# Примеры для быстрого старта
with st.expander("💡 Примеры для проверки", expanded=False):
    st.markdown(
        "- `pikachu` / `25` — есть картинка, типы, habitat `forest`\n"
        "- `bulbasaur` / `1` — травяной + ядовитый\n"
        "- `charizard` / `6` — огненный + летающий\n"
        "- `mewtwo` / `150` — без habitat в API (проверка «Неизвестна»)\n"
        "- `xyz123` — проверка ошибки «не найден»"
    )

query = st.text_input(
    "Имя или ID покемона",
    placeholder="Например: pikachu или 25",
    help="Имя вводится на английском строчными буквами. ID — число от 1 до ~1025.",
)

search = st.button("🔍 Найти покемона", type="primary", use_container_width=True)

if search:
    name_or_id = (query or "").strip()

    if not name_or_id:
        st.warning("⚠️ Вы ничего не ввели. Укажите имя или ID покемона.")
    else:
        try:
            with st.spinner(f"Ищем покемона «{name_or_id}»..."):
                pokemon = get_pokemon(name_or_id)
                species = get_species(pokemon.get("id"))

            # --- разбор данных ---
            poke_id = pokemon.get("id", "?")
            name_en = pokemon.get("name", "неизвестно")
            name_ru = get_ru_species_name(species, name_en)

            types_en = [t["type"]["name"] for t in pokemon.get("types", [])]
            types_ru = [translate_type(t) for t in types_en]

            height_dm = pokemon.get("height", 0)
            weight_hg = pokemon.get("weight", 0)
            height_m = height_dm / 10
            weight_kg = weight_hg / 10

            habitat_obj = species.get("habitat")
            habitat_en = habitat_obj["name"] if habitat_obj else None
            habitat_ru = translate_habitat(habitat_en)

            held_items = pokemon.get("held_items", [])
            berries, others = split_held_items(held_items)
            sprite_url = get_sprite(pokemon)

            # --- красивый вывод ---
            st.success(f"Найден покемон: **{name_ru}** (ID: {poke_id})")
            st.divider()

            col_img, col_info = st.columns([1, 2])

            with col_img:
                if sprite_url:
                    st.image(sprite_url, caption=f"{name_ru} #{poke_id}", use_container_width=True)
                else:
                    st.info("😶 Нет изображения в API")

            with col_info:
                st.subheader(f"📛 {name_ru}  ·  🔢 ID {poke_id}")
                st.caption(f"Оригинальное имя в API: `{name_en}`")

                if types_ru:
                    chips = "  ".join(
                        f"{TYPE_EMOJI.get(en, '🏷️')} **{ru}**"
                        for en, ru in zip(types_en, types_ru)
                    )
                    st.markdown(f"🏷️ **Типы:** {chips}")
                    st.caption(f"(оригинал: {', '.join(types_en)})")
                else:
                    st.markdown("🏷️ **Типы:** нет данных")

            m1, m2, m3 = st.columns(3)
            m1.metric("📏 Рост", f"{height_m:.1f} м", f"{height_dm} дм")
            m2.metric("⚖️ Вес", f"{weight_kg:.1f} кг", f"{weight_hg} гектограмм")
            m3.metric("🌍 Habitat", habitat_ru)

            if habitat_en:
                st.caption(f"Оригинальное habitat в API: `{habitat_en}`")
            else:
                st.caption("В API для этого покемона habitat не указан.")

            st.divider()
            st.subheader("🍒 Питание / предметы (held items)")
            st.markdown(
                "_Это предметы, которые покемон держит в дикой природе. "
                "Чаще всего это ягоды — ими покемон может питаться._"
            )

            if not held_items:
                st.info(
                    "ℹ️ У этого покемона нет held items в API. "
                    "Возможно, в дикой природе он ничего не держит."
                )
            else:
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**🫐 Ягоды ({len(berries)})**")
                    if berries:
                        for b in berries:
                            st.markdown(f"- `{b}`")
                    else:
                        st.markdown("_Ягод нет_")
                with c2:
                    st.markdown(f"**🎒 Прочие предметы ({len(others)})**")
                    if others:
                        for o in others:
                            st.markdown(f"- `{o}`")
                    else:
                        st.markdown("_Прочих предметов нет_")

                if not berries and others:
                    st.info("ℹ️ Ягод среди held items нет, только прочие предметы.")

            with st.expander("🔧 Сырые данные API (для любопытных)"):
                st.json({"pokemon": {"name": name_en, "id": poke_id}, "habitat": habitat_en})

        except ValueError as exc:
            # Покемон не найден (HTTP 404)
            st.error(f"❌ {exc}")
            st.info("Проверьте написание. Имя вводится на английском, например: `pikachu`, `bulbasaur`, `charizard`.")
        except (ConnectionError, TimeoutError) as exc:
            # Проблемы с сетью
            st.error(f"❌ Ошибка сети: {exc}")
            st.info("Проверьте подключение к интернету и попробуйте ещё раз.")
        except Exception as exc:  # noqa: BLE001 — показать любую непредвиденную ошибку красиво
            st.error(f"❌ Непредвиденная ошибка: {exc}")

else:
    st.info("👆 Введите имя или ID выше и нажмите кнопку поиска.")

st.divider()
st.caption("Данные: https://pokeapi.co · Рост в API — в дециметрах, вес — в гектограммах.")
