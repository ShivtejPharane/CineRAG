from pathlib import Path
import json
from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_ollama import OllamaEmbeddings
DATA_SOURCE = Path("./tmdb")
CHROMADB_PATH = "./chromadb"

embedding_function = OllamaEmbeddings(model="nomic-embed-text")

chroma = Chroma(
    #collection name (similar to the table in RDBMS)
    collection_name="movies",
    #path of vector store
    persist_directory=CHROMADB_PATH,
    #embedding function is used to convert data into embeddings
    embedding_function=embedding_function
)

#function to create a movie document
def create_movie_document(data):
    movie = data['movie']

    title = movie['title']
    overview = movie['overview']
    status = movie['status']
    geners = ', '.join([genre['name'] for genre in movie.get("genres",[])])
    cast = ', '.join([actor["name"] for actor in data.get("cast",[])])
    keywords = ', '.join([keyword['name'] for keyword in data.get('keywords',[])])
    recommendations = ', '.join([recommendation['title'] for recommendation in data.get('recommendations',[])])
    #filter the director info
    directors=[]
    for member in data.get('crew',[]):
        if member['job'] == 'Director':
            directors.append(member['name'])
    # club all the extracted information to create a single document for every movie
    movie_document = f"""
        Title : {title}
        Overview : {overview}
        Status : {status}
        Geners : {geners}
        Cast : {cast}
        Keywords : {keywords}
        Recommendations : {recommendations}
        Directors : {', '.join(directors)}
    """
    # Add the meta data for movies 
    metadata = {
        "movie_id" : movie["id"],
        "title" : movie['title'],
        "language" : movie['original_language'],
        "director" : ','.join(directors),
        "poster" : movie["poster_path"]
    }
    #convert the movie document in Document format to get inserted into chromadb
    return Document(page_content=movie_document.strip(),
                    metadata = metadata)

#Read the files from the Data source
index = 1
documents = []
for document_path in DATA_SOURCE.glob("*.json"):
    print(f"opening and creating document no :{index}")
    with open(document_path,"r",encoding="utf-8") as file:
        data = json.load(file)
        movie_document = create_movie_document(data=data)
        documents.append(movie_document)
        chroma.add_documents([movie_document])

    index+=1

# Add the documents to chroma db

print("Knowledge base is ready......")