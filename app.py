import streamlit as st
import pickle
import requests
import pandas as pd
from functools import lru_cache

# ─── CONFIG ───────────────────────────────────────────────────
OMDB_API_KEY = "a70cf3c8"  # ← replace with your OMDb API key
MOVIES_PKL = "movies.pkl"
SIMILARITY_PKL = "G:\\Music Recommandation System\\similarity.pkl"

# ─── CACHING SETUP ────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def load_data():
    raw = pickle.load(open(MOVIES_PKL, 'rb'))
    similarity = pickle.load(open(SIMILARITY_PKL, 'rb'))
    movies_df = raw.copy() if isinstance(raw, pd.DataFrame) else pd.DataFrame(raw)
    return movies_df, similarity

@lru_cache(maxsize=512)
def fetch_poster_omdb(title: str, year: int = None) -> str:
    """Fetch poster from OMDb API, return URL or None."""
    if OMDB_API_KEY == "YOUR_OMDB_KEY":
        return None
    params = {"apikey": OMDB_API_KEY, "t": title}
    if year:
        params["y"] = str(year)
    try:
        resp = requests.get("https://www.omdbapi.com/", params=params, timeout=5).json()
        if resp.get("Response") == "True":
            poster = resp.get("Poster")
            return poster if poster and poster != "N/A" else None
    except requests.RequestException:
        return None
    return None

# ─── RECOMMENDATION FUNCTION ─────────────────────────────────
@st.cache_data(show_spinner=False)
def recommend(title: str, movies_df: pd.DataFrame, similarity: list, top_n: int = 5):
    idx = movies_df[movies_df['title'] == title].index[0]
    sims = sorted(enumerate(similarity[idx]), key=lambda x: x[1], reverse=True)[1: top_n + 1]
    recs = []
    for movie_idx, score in sims:
        row = movies_df.iloc[movie_idx]
        recs.append({
            'title': row['title'],
            'year': row.get('year', '----'),
            'poster': fetch_poster_omdb(row['title'], row.get('year')),
            'score': round(score, 2)
        })
    return recs

# ─── MAIN APP ─────────────────────────────────────────────────
st.set_page_config(page_title="Movie Recommender", layout="wide")

# Custom CSS theme with fixed poster height for alignment
st.markdown(
    """
    <style>
    .stApp {background: linear-gradient(135deg, #1f1c2c, #928dab); color: #FFFFFF;}
    .stButton>button {background-color: #FF6F61; color: #FFF; font-weight: bold; border-radius: 8px;}
    .stSelectbox>div>div>div>span {color: #000;}
    .stImage>img {
        border-radius: 12px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
        object-fit: cover;
        height: 350px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Warn if API key not set
title_container = st.container()
if OMDB_API_KEY == "YOUR_OMDB_KEY":
    title_container.warning(
        "🎯 **Reminder:** Set your `OMDB_API_KEY` in the config to fetch live posters!"
    )

movies_df, similarity = load_data()

st.title("🎥 Your Personalized Movie Recommender")
st.write(
    "Select a movie you love, and discover similar films with poster previews and similarity scores."
)

with st.sidebar:
    st.header("🔧 Settings")
    num_rec = st.slider(
        "Number of recommendations", min_value=3, max_value=10, value=5
    )
    search = st.text_input("🔍 Search movie title", "")

# Filter movie list
titles = movies_df['title'].tolist()
filtered = [t for t in titles if search.lower() in t.lower()] if search else titles
selected = st.selectbox("Choose or search a movie", filtered)

if st.button("Recommend 🎬"):
    with st.spinner("🍿 Fetching recommendations..."):
        recs = recommend(selected, movies_df, similarity, top_n=num_rec)

    cols = st.columns(len(recs))
    for col, rec in zip(cols, recs):
        with col:
            st.markdown(f"**{rec['title']} ({rec['year']})**")
            st.caption(f"Similarity: {rec['score']}")
            if rec['poster']:
                st.image(rec['poster'], use_container_width=True)
            else:
                st.image(
                    "https://via.placeholder.com/300x450?text=No+Poster",
                    caption="Poster not available",
                    use_container_width=True
                )

