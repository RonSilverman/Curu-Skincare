import streamlit as st
import json
from langchain_community.document_loaders import JSONLoader
from pathlib import Path
import os
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain.llms import OpenAI
import re
from langchain.chat_models import ChatOpenAI
from pymongo import MongoClient
import random
from textblob import TextBlob

def analyze_sentiment(review_text):
    analysis = TextBlob(review_text)
    return 'positive' if analysis.sentiment.polarity > 0 else 'negative'

def analyze_sentiment_2(review_text):
    analysis = TextBlob(review_text)
    return analysis.sentiment.polarity

# Set page configuration to wide mode
# st.set_page_config(layout="wide")
RIGHT_ARROW = "\u2192"  # Unicode for right arrow
# CSS for tooltips
tooltip_css = """
<style>
.tooltip {
  position: relative;
  display: inline-block;
  cursor: pointer;
}
.bordered-box {
    border: 1px solid #ddd;
    padding: 10px;
    border-radius: 5px;
}
.tooltip .tooltiptext {
  visibility: hidden;
  width: 700px;
  min-height: 200px;
  background-color: #555;
  color: #fff;
  text-align: left;
  border-radius: 6px;
  padding: 10px;
  position: absolute;
  z-index: 1;
  top: 150%;
  left: 50%;
  margin-left: -150px;
  opacity: 0;
  transition: opacity 0.3s;
}

.tooltip:hover .tooltiptext {
  visibility: visible;
  opacity: 1;
}
</style>
"""
BEAUTY_ICONS = [
    "\U0001f484",  # 💄 lipstick
    "\U0001f485",  # 💅 nail polish
    "\U0001f4a7",  # 💧 droplet
    "\U0001f9fc",  # 🧼 soap
    "\U0001f9f4",  # 🧴 lotion bottle
    "\U00002728",  # ✨ sparkles
    "\U0001f48e",  # 💎 gem stone
    "\U0001f3db",  # 🏛 classical building (can represent luxury)
    "\U0001f490",  # 💐 bouquet (for natural ingredients)
    "\U0001f33f",  # 🌿 herb (for natural ingredients)
]
LIGHT_BULB = "\U0001f4a1"
ROCKET = "\U0001f680"
SAVE_ICON = "\U0001f4be"
FILING_CABINET_ICON = "\U0001f5c4"  # 🗄️ Filing Cabinet

initial_prompt = ChatPromptTemplate.from_template("""
    You are an AI assistant tasked with analyzing product reviews. 
    Your goal is to identify the most frequently discussed aspects or features of the product based on the given context. 
    The product you are reviewing is a skin cleanser. Focus on aspects that are frequently mentioned that would help a new customer make an informed decision about purchasing the product. 
    Highlight features that are frequently mentioned and are crucial for making a buying decision. Make the reviews easier and colloquial for the customer to understand.

    <context>
    {context}
    </context>

    Please provide your response as a list of 5 aspects, each on a new line, without any additional explanation or formatting.
""")

second_prompt = ChatPromptTemplate.from_template("""
    You're a friendly AI assistant analyzing Amazon reviews for {input}. Based on the given context and key aspects, provide a summary that feels like a casual chat with a knowledgeable friend:

    For each key aspect:
    1. Count how many customers mention this aspect out of the total reviews.
    2. Break down positive and negative mentions, and those who would purchase again.
    3. Write a conversational summary of customer opinions, using phrases like "most users said" or "a few folks mentioned".
    4. Pick 4 quotes that really capture what people are saying.

    Key aspects to cover:
    {key_aspects}

    Your response should be a JSON object where each key is an aspect from the key_aspects list, containing:
    - total_reviews: integer (total number of reviews analyzed)
    - total_mentions: integer
    - positive_mentions: integer
    - negative_mentions: integer
    - would_purchase_again: integer
    - summary: string (conversational summary)
    - quotes: array of 4 strings

    <context>
    {context}
    </context>

    Make sure your response is a valid JSON object. Remember, we're aiming for a friendly, chatty tone in the summary!
""")

load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

# MongoDB setup
uri = "mongodb+srv://rachaeltbusiness:ux4HmvEKC2TtIc6U@curureviews.zedfv.mongodb.net/?retryWrites=true&w=majority&appName=CuruReviews"
# "mongodb+srv://msramasubramanya23:LtlHRUrtZcxUPVcf@cluster0.h7ohhbr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri)
# db = client["AI-Inference"]
# collection = db["Amazon-Cleanser"]
db = client["Curu"]
collection = db["AI-Inference-Data"]

def analyze_reviews_1(product_name):
    output = retrieval_chain.invoke(
        {
            "input": product_name,
        }
    )
    return output["answer"]


# Function to analyze reviews (update this in your code)
def analyze_reviews(product_name, key_aspects):
    key_aspects_str = "\n".join(f"- {aspect}" for aspect in key_aspects)

    output = retrieval_chain.invoke(
        {"input": product_name, "key_aspects": key_aspects_str}
    )

    return output["answer"]


def get_random_beauty_icon():
    return random.choice(BEAUTY_ICONS)


import streamlit as st

def display_review_summary(positive_reviews, negative_reviews):
    # CSS for styling tooltips
    tooltip_css_sentiment = """
    <style>
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: pointer;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 300px;
        background-color: #555;
        color: #fff;
        text-align: left;
        border-radius: 6px;
        padding: 10px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -150px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
    .review-count {
        font-size: 24px;
        font-weight: bold;
    }
    .positive { color: green; }
    .negative { color: red; }
    </style>
    """
    st.markdown(tooltip_css_sentiment, unsafe_allow_html=True)

    # Function to create tooltip content
    def create_tooltip_content(reviews):
        content = "<br>".join(f"• {review[:100]}..." for review, _ in reviews[:5])
        return content

    # Positive reviews tooltip
    positive_tooltip = create_tooltip_content(positive_reviews)
    st.markdown(f"""
    <div class="tooltip">
        Positive reviews: <span class="review-count positive">{len(positive_reviews)}</span>
        <span class="tooltiptext">
            <strong>Top 5 Positive Reviews:</strong><br>
            {positive_tooltip}
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Negative reviews tooltip
    negative_tooltip = create_tooltip_content(negative_reviews)
    st.markdown(f"""
    <div class="tooltip">
        Negative reviews: <span class="review-count negative">{len(negative_reviews)}</span>
        <span class="tooltiptext">
            <strong>Top 5 Negative Reviews:</strong><br>
            {negative_tooltip}
        </span>
    </div>
    """, unsafe_allow_html=True)

            

def display_results_from_mongo(result):
    st.markdown(tooltip_css, unsafe_allow_html=True)
    # product_from = result["result_from"]
    for key, value in result["analysis"].items():
        beauty_icon = get_random_beauty_icon()
        
        summary = value["summary"]
        quotes = "<br>".join(value["quotes"])
        total_reviews = value["total_reviews"]
        total_mentions = value["total_mentions"]
        positive_mentions = value["positive_mentions"]
        negative_mentions = value["negative_mentions"]
        would_purchase_again = value["would_purchase_again"]

        tooltip_text = f"""
        <strong style="color: yellow;">Summary:</strong> <span style="color: lightblue;">{summary}</span><br>
        <strong style="color: yellow;">Total Reviews:</strong> <span style="color: lightblue;">{total_reviews}</span><br>
        <strong style="color: yellow;">Mentions:</strong> <span style="color: lightblue;">{total_mentions}</span><br>
        <strong style="color: yellow;">Positive Mentions:</strong> <span style="color: lightgreen;">{positive_mentions}</span><br>
        <strong style="color: yellow;">Negative Mentions:</strong> <span style="color: lightcoral;">{negative_mentions}</span><br>
        <strong style="color: yellow;">Would Purchase Again:</strong> <span style="color: lightyellow;">{would_purchase_again}</span><br>
        <strong style="color: yellow;">Notable Quotes:</strong><br>
        <span style="color: lightgreen;">{quotes}</span>
        """
        aspect_text = f"""<h5>{beauty_icon} {key}</h5>"""

        st.markdown(
            f"""
        <div class="tooltip">{aspect_text}
        <span class="tooltiptext">{tooltip_text}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )


def display_results(result):
    st.markdown(tooltip_css, unsafe_allow_html=True)

    for key, value in result.items():
        beauty_icon = get_random_beauty_icon()
        summary = value["summary"]
        quotes = "<br>".join(value["quotes"])
        total_reviews = value["total_reviews"]
        total_mentions = value["total_mentions"]
        positive_mentions = value["positive_mentions"]
        negative_mentions = value["negative_mentions"]
        would_purchase_again = value["would_purchase_again"]

        tooltip_text = f"""
        <strong style="color: yellow;">Summary:</strong> <span style="color: lightblue;">{summary}</span><br>
        <strong style="color: yellow;">Total Reviews:</strong> <span style="color: lightblue;">{total_reviews}</span><br>
        <strong style="color: yellow;">Mentions:</strong> <span style="color: lightblue;">{total_mentions}</span><br>
        <strong style="color: yellow;">Positive Mentions:</strong> <span style="color: lightgreen;">{positive_mentions}</span><br>
        <strong style="color: yellow;">Negative Mentions:</strong> <span style="color: lightcoral;">{negative_mentions}</span><br>
        <strong style="color: yellow;">Would Purchase Again:</strong> <span style="color: lightyellow;">{would_purchase_again}</span><br>
        <strong style="color: yellow;">Notable Quotes:</strong><br>
        <span style="color: lightgreen;">{quotes}</span>
        """
        aspect_text = f"""<h5>{beauty_icon} {key}</h5>"""

        st.markdown(
            f"""
        <div class="tooltip">{aspect_text}
        <span class="tooltiptext">{tooltip_text}</span>
        </div>
        """,
            unsafe_allow_html=True,
        )


def format_output(json_str):
    try:
        data = json.loads(json_str)
        formatted_output = ""
        # existing_data['analysis'].items()
        for aspect, info in data.items():
            formatted_output += f"{aspect}\n"
            formatted_output += (
                f"{info['total_mentions']} customers mention '{aspect}'\n"
            )
            formatted_output += f"{info['positive_mentions']} positive {info['negative_mentions']} negative\n\n"
            formatted_output += f"{info['summary']}\n\n"
            for quote in info["quotes"]:
                formatted_output += f'"{quote}"\n'
            formatted_output += "\n"
        return formatted_output
    except json.JSONDecodeError:
        return "Error: The AI response was not in valid JSON format. Please try again."

skincare_steps = [
    "Cleanser",
    "Exfoliant",
    "Toner",
    "Serum",
    "Facial Oil",
    "Moisturiser",
    "Masks",
    "Eye Care",
    "Lip Care",
    "Sun Care",
    "Decollet"
]


# Determine the number of columns (you can adjust this as needed)
num_columns = 6

# Create columns
cols = st.columns(num_columns)

# Create checkboxes for each step
for index, step in enumerate(skincare_steps):
    with cols[index % num_columns]:
        if step == "Cleanser":
            st.checkbox(step, value=True)
        else:
            st.checkbox(step, value=False, disabled=True)
            
# List of companies
companies = ["Amazon", "Sephora", "Ulta"]

# Create a container for the radio buttons
radio_container = st.container()

# Create three columns within the container
col1, col2, col3 = radio_container.columns(3)

# Create a single radio input with options displayed in columns
data_source = radio_container.radio(
    "Select data source:",
    companies,
    horizontal=True,
    key="data_source"
)




# Function to load data based on selected source
def load_data(source):
    file_mapping = {
        "Amazon": "cleaned_cleanser_large_data.json",
        "Sephora": "cleaned_cleanser_sephora_reviews.json",
        "Ulta": "cleaned_cleanser_ulta_reviews.json",
    }
    file_path = file_mapping.get(source)
    if file_path:
        with open(file_path, "r") as file:
            return json.load(file)
    return None

# def display_review_summary(positive_reviews, negative_reviews):
#     # CSS for styling
#     st.markdown("""
#     <style>
#     .review-count {
#         font-size: 24px;
#         font-weight: bold;
#         cursor: pointer;
#     }
#     .positive { color: green; }
#     .negative { color: red; }
#     .review-list {
#         display: none;
#         background-color: #f0f0f0;
#         padding: 10px;
#         border-radius: 5px;
#         margin-top: 10px;
#     }
#     </style>
#     """, unsafe_allow_html=True)

#     # JavaScript for hover functionality
#     st.markdown("""
#     <script>
#     function showReviews(id) {
#         document.getElementById(id).style.display = 'block';
#     }
#     function hideReviews(id) {
#         document.getElementById(id).style.display = 'none';
#     }
#     </script>
#     """, unsafe_allow_html=True)

#     # Display review counts with hover functionality
#     st.markdown(f"""
#     <div onmouseover="showReviews('positive-reviews')" onmouseout="hideReviews('positive-reviews')">
#         Positive reviews: <span class="review-count positive">{len(positive_reviews)}</span>
#         <div id="positive-reviews" class="review-list">
#             {'<br>'.join(review for review, _ in positive_reviews)}
#         </div>
#     </div>
#     <div onmouseover="showReviews('negative-reviews')" onmouseout="hideReviews('negative-reviews')">
#         Negative reviews: <span class="review-count negative">{len(negative_reviews)}</span>
#         <div id="negative-reviews" class="review-list">
#             {'<br>'.join(review for review, _ in negative_reviews)}
#         </div>
#     </div>
#     """, unsafe_allow_html=True)
    
# @st.cache
def get_cleanser_reviews(data, cleanser_name):
    for cleanser in data:
        if cleanser_name in cleanser['text']:
            return cleanser['Reviewer_Details']
    return {}

# Load the JSON data based on selected source
data = load_data(data_source)

if data:
    # Extract all the text values for the dropdown
    text_values = [item["text"] for item in data]

selected_product = st.selectbox("Select a cleanser:", [""] + text_values)

if selected_product:
    # Check if the product details exist in MongoDB
    existing_data = collection.find_one({"product_name": selected_product})

    if existing_data:
        # st.write("Data already exists for this product.")
        st.success("Data already exists for this product", icon="✅")
        # existing_result = json.loads(existing_data)

        # Display the CSS
        st.markdown(tooltip_css, unsafe_allow_html=True)

        st.subheader(":mag_right: Search Result: ", divider="gray")
        # Display the product website
        st.subheader(f"Product Website: :point_right: {existing_data['product_from']}")
        # Display the product name
        st.subheader(f"Product Name: :point_right: {existing_data['product_name']}")
        # st.json(existing_data)
        # Iterate through the analysis object
        reviews = get_cleanser_reviews(data, selected_product)
        # Analyze Sentiments
        positive_count = 0
        negative_count = 0
        positive_reviews = []
        negative_reviews = []

        # Sort reviews by polarity
        positive_reviews.sort(key=lambda x: x[1], reverse=True)
        negative_reviews.sort(key=lambda x: x[1])

        for review_id, review_data in reviews.items():
            sentiment = analyze_sentiment(review_data['review'])
            if sentiment == 'positive':
                positive_count += 1
            else:
                negative_count += 1
                
        for review_id, review_data in reviews.items():
            polarity = analyze_sentiment_2(review_data['review'])
            if polarity > 0:
                positive_reviews.append((review_data['review'], polarity))
            else:
                negative_reviews.append((review_data['review'], polarity))

        # Sort reviews by polarity
        positive_reviews.sort(key=lambda x: x[1], reverse=True)
        negative_reviews.sort(key=lambda x: x[1])
        display_review_summary(positive_reviews, negative_reviews)
        display_results_from_mongo(existing_data)
        

        # # Display Results
        # st.write(f"Total Positive Reviews: {positive_count}")
        # st.write(f"Total Negative Reviews: {negative_count}")
        

        

        
        

        if st.button(f"{LIGHT_BULB} Generate new analysis?"):
            st.toast("Generating new analysis...", icon=ROCKET)
            # Proceed with the analysis
            jq_schema = (
                f'map(select(.text == "{selected_product}")) | .[].Reviewer_Details'
            )
            loader = JSONLoader(
                file_path="cleaned_cleanser_large_data.json",
                jq_schema=jq_schema,
                text_content=False,
            )
            JSON_documents = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            )
            documents = text_splitter.split_documents(JSON_documents)

            db = Chroma.from_documents(documents, OpenAIEmbeddings())

            llm = ChatOpenAI(temperature=0.7, model_name="gpt-4")

            document_chain_1 = create_stuff_documents_chain(llm, initial_prompt)
            retriever_1 = db.as_retriever()
            retrieval_chain = create_retrieval_chain(retriever_1, document_chain_1)

            result = analyze_reviews_1(selected_product)
            result_as_list = result.splitlines()
            result_as_list = [line[3:] for line in result_as_list]

            document_chain_2 = create_stuff_documents_chain(llm, second_prompt)
            retriever_2 = db.as_retriever()
            retrieval_chain = create_retrieval_chain(retriever_2, document_chain_2)

            result_json = analyze_reviews(selected_product, result_as_list)
            # st.json(result_json)

            result = json.loads(result_json)

            st.markdown(tooltip_css, unsafe_allow_html=True)

            display_results(result)
            
            with col1:
                st.markdown(f"<h3 style='color: green;'>Positive reviews: {len(positive_reviews)}</h3>", unsafe_allow_html=True)
                with st.expander("Show Positive Reviews"):
                    for review, _ in positive_reviews:
                        st.write(review)
                        st.markdown("---")
        
            with col2:
                st.markdown(f"<h3 style='color: red;'>Negative reviews: {len(negative_reviews)}</h3>", unsafe_allow_html=True)
                with st.expander("Show Negative Reviews"):
                    for review, _ in negative_reviews:
                        st.write(review)
                        st.markdown("---")
            
            if st.button("Save new analysis?"):
                collection.update_one(
                    {"product_from": data_source},
                    {"product_name": selected_product},
                    {"$set": {"analysis": result}},
                    upsert=True,
                )
                st.write("New analysis saved to MongoDB.")

    else:
        st.write("No existing data found. Generating new analysis...")
        file_mapping = {
            "Amazon": "cleaned_cleanser_large_data.json",
            "Sephora": "cleaned_cleanser_sephora_reviews.json",
            "Ulta": "cleaned_cleanser_ulta_reviews.json",
        }
        file_path = file_mapping.get(data_source)

        if file_path:
            # Proceed with the analysis
            jq_schema = (
                f'map(select(.text == "{selected_product}")) | .[].Reviewer_Details'
            )
            loader = JSONLoader(
                file_path=file_path,
                jq_schema=jq_schema,
                text_content=False,
            )
            JSON_documents = loader.load()

            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, chunk_overlap=200
            )
            documents = text_splitter.split_documents(JSON_documents)

            db = Chroma.from_documents(documents, OpenAIEmbeddings())

            llm = ChatOpenAI(temperature=0.7, model_name="gpt-4")

            document_chain_1 = create_stuff_documents_chain(llm, initial_prompt)
            retriever_1 = db.as_retriever()
            retrieval_chain = create_retrieval_chain(retriever_1, document_chain_1)

            result = analyze_reviews_1(selected_product)
            result_as_list = result.splitlines()
            result_as_list = [line[3:] for line in result_as_list]

            document_chain_2 = create_stuff_documents_chain(llm, second_prompt)
            retriever_2 = db.as_retriever()
            retrieval_chain = create_retrieval_chain(retriever_2, document_chain_2)

            result_json = analyze_reviews(selected_product, result_as_list)
            # st.json(result_json)

            result = json.loads(result_json)
            display_results(result)

            if st.button(f"{SAVE_ICON} Save analysis to MongoDB?"):
                st.toast("Saving analysis to MongoDB...", icon=FILING_CABINET_ICON)
                collection.insert_one(
                    {
                        "product_from": data_source,
                        "product_name": selected_product,
                        "analysis": result,
                    }
                )
                st.write("Analysis saved to MongoDB.")
                st.toast("Analysis saved to MongoDB.", icon="✅")

else:
    st.write("Please select a product to see reviews.")
