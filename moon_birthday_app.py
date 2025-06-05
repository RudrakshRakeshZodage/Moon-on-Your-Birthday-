import streamlit as st
from skyfield.api import load
import numpy as np
import matplotlib.pyplot as plt
from datetime import date
from io import BytesIO
import requests

# === IMPORTANT: set_page_config MUST be the first Streamlit command ===
st.set_page_config(page_title="Moon on Your Birthday 🌙", layout="wide", page_icon="🌙")

# Put your NASA API key here directly
NASA_API_KEY = "YkYieTxhf3sAlQo1ZsReCZE1VVJ7jmfi4Gqbahzy"

# Custom CSS styles
st.markdown(
    """
    <style>
    .main > div {
        padding: 2rem 4rem 4rem 4rem;
        max-width: 900px;
        margin: auto;
    }
    .stButton>button {
        background-color: #4B8BBE;
        color: white;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: bold;
        transition: background-color 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #306998;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("🌙 Moon on Your Birthday")

birth_date = st.date_input("Select your birthdate", min_value=date(1900, 1, 1), max_value=date(2100, 12, 31))


def get_moon_phase_name(angle):
    if angle < 22.5 or angle > 337.5:
        return "🌑 New Moon"
    elif angle <= 67.5:
        return "🌒 Waxing Crescent"
    elif angle <= 112.5:
        return "🌓 First Quarter"
    elif angle <= 157.5:
        return "🌔 Waxing Gibbous"
    elif angle <= 202.5:
        return "🌕 Full Moon"
    elif angle <= 247.5:
        return "🌖 Waning Gibbous"
    elif angle <= 292.5:
        return "🌗 Last Quarter"
    else:
        return "🌘 Waning Crescent"


if birth_date:
    # Load ephemeris and timescale
    ts = load.timescale()
    eph = load('de421.bsp')
    earth, moon, sun = eph['earth'], eph['moon'], eph['sun']
    t = ts.utc(birth_date.year, birth_date.month, birth_date.day)

    # Calculate moon and sun ecliptic longitudes
    astrometric = earth.at(t).observe(moon).apparent()
    _, slon, _ = earth.at(t).observe(sun).apparent().ecliptic_latlon()
    _, mlon, _ = astrometric.ecliptic_latlon()

    # Calculate phase angle and illumination
    phase_angle = (mlon.degrees - slon.degrees) % 360
    illumination = (1 + np.cos(np.radians(phase_angle))) / 2 * 100
    moon_phase_name = get_moon_phase_name(phase_angle)

    # Display info line
    st.markdown(
        f"<p style='font-size:18px; font-weight:bold;'>"
        f"📅 Date: {birth_date.strftime('%B %d, %Y')} &nbsp;&nbsp; | &nbsp;&nbsp; "
        f"🌙 Moon Phase: {moon_phase_name} &nbsp;&nbsp; | &nbsp;&nbsp; "
        f"💡 Illumination: {illumination:.2f}%"
        f"</p>",
        unsafe_allow_html=True,
    )

    # Two columns for moon image & NASA APOD
    col1, col2 = st.columns(2, gap="large")

    with col1:
        # Create simulated moon phase image
        fig, ax = plt.subplots(figsize=(4, 4))
        ax.set_aspect('equal')
        ax.axis('off')
        moon_circle = plt.Circle((0.5, 0.5), 0.4, color='gray')
        ax.add_artist(moon_circle)

        # Shadow position depending on phase angle
        if phase_angle <= 180:
            shadow_center_x = 0.5 - 0.4 * np.cos(np.radians(phase_angle))
        else:
            shadow_center_x = 0.5 + 0.4 * np.cos(np.radians(360 - phase_angle))
        shadow = plt.Circle((shadow_center_x, 0.5), 0.4, color='black')
        ax.add_artist(shadow)

        plt.title("Simulated Moon Phase", fontsize=14)
        buf = BytesIO()
        plt.savefig(buf, format="png", bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        st.image(buf, use_column_width=True)

        # Download button
        st.download_button(
            "📥 Download Moon Image",
            data=buf.getvalue(),
            file_name=f"moon_{birth_date}.png",
            mime="image/png"
        )

    with col2:
        st.subheader("🌌 NASA Astronomy Picture of the Day")

        nasa_url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}&date={birth_date.isoformat()}"
        try:
            response = requests.get(nasa_url, timeout=10)
            if response.status_code == 429:
                st.error("NASA API rate limit exceeded. Please try again later.")
            elif response.status_code != 200:
                data = response.json()
                st.error(f"NASA API Error: {data.get('msg', 'Unknown error')}")
            else:
                data = response.json()
                if data.get("media_type") == "image":
                    st.image(data["url"], use_column_width=True)
                    explanation = data.get("explanation", "No description provided.")
                    short_exp = explanation[:200].rsplit('.', 1)[0] + '.' if len(explanation) > 200 else explanation
                    st.markdown(f"<p style='font-size:14px'>{short_exp}</p>", unsafe_allow_html=True)
                else:
                    st.warning("NASA did not provide an image for this date.")
            
            # Optionally show rate limits
            st.write(f"Rate limit: {response.headers.get('X-RateLimit-Limit')}")
            st.write(f"Requests remaining: {response.headers.get('X-RateLimit-Remaining')}")
        except Exception as e:
            st.error(f"Error fetching NASA image: {e}")
