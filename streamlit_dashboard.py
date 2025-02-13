import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine, text

# Database connection setup
db_credentials = {
    "username": "root",
    "password": "Guvi%40003",
    "host": "localhost",
    "database": "imdb_db"
}

def get_data_from_sql(query, params=None):
    """Fetch data from MySQL using SQLAlchemy with parameterized queries."""
    engine = create_engine(f"mysql+pymysql://{db_credentials['username']}:{db_credentials['password']}@{db_credentials['host']}/{db_credentials['database']}")
    with engine.connect() as connection:
        return pd.read_sql(text(query), connection, params=params)

# Custom IMDb Background Styling
st.markdown(
    """
    <style>
        .stApp {
            background: url('https://wallpaperaccess.com/full/11037496.jpg');
            background-size: cover;
            color: white;
        }
        .block-container {
            padding: 2rem;
            background: rgba(0, 0, 0, 0.7);
            border-radius: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Streamlit UI setup
st.title("🎬 IMDb Movie Analysis")
st.markdown("Explore and analyze IMDb movie data interactively.")

# Filtering Options
with st.sidebar:
    st.header("🔍 Filters")
    duration_filter = st.slider("Duration (Minutes)", min_value=0, max_value=260, value=(0, 260))
    rating_filter = st.slider("Ratings", min_value=0.0, max_value=10.0, value=(0.0, 10.0))
    voting_filter = st.number_input("Minimum Voting Count", min_value=0, value=0)
    genre_options = ["All", "Action", "Adventure", "Fantasy", "Biography", "Animation"]
    genre_filter = st.selectbox("Genre", genre_options)

# Constructing SQL query using parameterized queries
query = """
    SELECT Movie_Name, Genre, Duration, Ratings, Voting_Counts 
    FROM movies
    WHERE Duration BETWEEN :min_duration AND :max_duration
    AND Ratings BETWEEN :min_rating AND :max_rating
    AND Voting_Counts >= :min_votes
"""

params = {
    "min_duration": duration_filter[0],
    "max_duration": duration_filter[1],
    "min_rating": rating_filter[0],
    "max_rating": rating_filter[1],
    "min_votes": voting_filter
}

if genre_filter != "All":  
    query += " AND Genre = :genre_filter"
    params["genre_filter"] = genre_filter  

# Fetch filtered data only for the dynamic table
filtered_data = get_data_from_sql(query, params)
st.subheader("📋 Filtered Movies Data")
st.dataframe(filtered_data, height=300)

# Fetching all records for visualizations
all_data = get_data_from_sql("SELECT Movie_Name, Genre, Duration, Ratings, Voting_Counts FROM movies")

# 🔥 Top 10 Movies by Rating and Voting Counts (Updated to Horizontal Bar Chart)
st.subheader("🏆 Top 10 Movies by Rating and Voting Counts")

# Filter movies with significant votes (e.g., > 1000 votes)
significant_movies = all_data[all_data["Voting_Counts"] > 1000]

# Take the top 10 based on Ratings and Voting Counts
top_movies = significant_movies.nlargest(10, ['Ratings', 'Voting_Counts'])

fig, ax = plt.subplots(figsize=(8, 5))

# Horizontal Bar Chart
sns.barplot(y=top_movies["Movie_Name"], x=top_movies["Ratings"], palette="coolwarm", ax=ax)

# Ensure the x-axis includes only 4,5,6,7,8,9
ax.set_xticks([4, 5, 6, 7, 8, 9])

# Adjust the x-axis limits to fit within this range
ax.set_xlim(4, 9)

ax.set_xlabel("Ratings", fontsize=10)
ax.set_ylabel("Movie Names", fontsize=10)
ax.set_title("Top Rated Movies with High Votes", fontsize=12)

# Annotate Voting Counts inside bars with dynamic text color and centered positioning
def get_text_color(rgb):
    return 'black' if (rgb[0]*0.299 + rgb[1]*0.587 + rgb[2]*0.114) > 186 else 'white'

for index, (rating, votes) in enumerate(zip(top_movies["Ratings"], top_movies["Voting_Counts"])):
    bar_color = sns.color_palette("coolwarm", len(top_movies))[index]
    text_color = get_text_color(bar_color)
    ax.text(rating / 2, index, f'{votes} Votes', fontsize=10, color=text_color, ha='center', va='center', fontweight='bold')

st.pyplot(fig)




# 🎭 Genre Distribution
st.subheader("🎭 Genre Distribution")
fig, ax = plt.subplots(figsize=(8, 5))
sns.countplot(y='Genre', data=all_data, palette='viridis', ax=ax)
ax.set_title("Genre Distribution")
st.pyplot(fig)

# ⏳ Average Duration & Voting Trends by Genre
st.subheader("⏳ Average Duration & Voting Trends by Genre")
col1, col2 = st.columns(2)

with col1:
    avg_duration = all_data.groupby("Genre")["Duration"].mean().reset_index()
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(x="Duration", y="Genre", data=avg_duration, palette='magma', ax=ax)
    ax.set_title("Avg Duration by Genre")
    st.pyplot(fig)

with col2:
    avg_votes = all_data.groupby("Genre")["Voting_Counts"].mean().reset_index()
    fig, ax = plt.subplots(figsize=(6, 4))
    sns.barplot(x="Voting_Counts", y="Genre", data=avg_votes, palette='inferno', ax=ax)
    ax.set_title("Avg Votes by Genre")
    st.pyplot(fig)

# 📈 Rating Distribution
st.subheader("📈 Rating Distribution")
fig, ax = plt.subplots(figsize=(8, 5))
sns.histplot(all_data['Ratings'], bins=20, kde=True, color='skyblue', ax=ax)
ax.set_title("Distribution of Ratings")
st.pyplot(fig)

# 📌 Genre-Based Rating Leaders
st.subheader("🏅 Genre-Based Rating Leaders")
top_rated_movies = all_data.loc[all_data.groupby("Genre")["Ratings"].idxmax()][["Genre", "Movie_Name", "Ratings"]]
st.dataframe(top_rated_movies)

# 🥇 Most Popular Genres by Voting
st.subheader("📊 Most Popular Genres by Voting")
genre_votes = all_data.groupby("Genre")["Voting_Counts"].sum()
fig, ax = plt.subplots()
ax.pie(genre_votes, labels=genre_votes.index, autopct='%1.1f%%', colors=sns.color_palette("pastel"))
st.pyplot(fig)

# ⏳ Duration Extremes
st.subheader("⏳ Duration Extremes")
shortest_movie = all_data.nsmallest(1, "Duration")[["Movie_Name", "Duration"]]
longest_movie = all_data.nlargest(1, "Duration")[["Movie_Name", "Duration"]]
st.write("Shortest Movie:")
st.dataframe(shortest_movie)
st.write("Longest Movie:")
st.dataframe(longest_movie)

# 🌡 Ratings by Genre Heatmap
st.subheader("🌡 Ratings by Genre")
rating_heatmap = all_data.pivot_table(index="Genre", values="Ratings", aggfunc="mean")
fig, ax = plt.subplots(figsize=(8, 5))
sns.heatmap(rating_heatmap, annot=True, cmap="coolwarm", linewidths=0.5, ax=ax)
st.pyplot(fig)

# 📌 Correlation Analysis
st.subheader("📌 Correlation Analysis")
fig, ax = plt.subplots(figsize=(7, 5))
sns.scatterplot(x='Ratings', y='Voting_Counts', data=all_data, color='coral', alpha=0.6, ax=ax)
ax.set_title("Ratings vs. Votes")
st.pyplot(fig)

st.success("🎬 Movie Trends Unveiled!")
