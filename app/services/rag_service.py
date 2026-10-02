import chromadb

class RAGService:
    def __init__(self, collection_name="quiz_bank"):
# We store vectors locally in a folder inside our project, this is persistent storage that is
# even if the application is off , data is kept in the ram
        self.chroma_client = chromadb.PersistentClient(path="./chroma_storage")
        self.collection = self.chroma_client.get_or_create_collection(name=collection_name)

    def add_document_content(self, text: str):
        chunks = []
        chunk_size = 500
        overlap = 50
        start = 0
        
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append(text[start:end].strip())
            start += (chunk_size - overlap)
            
        doc_ids = [f"chunk_{i}" for i in range(len(chunks))]
        self.collection.add(documents=chunks, ids=doc_ids)
        return len(chunks)

    def retrieve_grounded_context(self, topic: str):
        """
        Queries ChromaDB. Returns the text chunk and a validation status 
        confirming if the document matches well enough to avoid hallucinations.
        """
        results = self.collection.query(query_texts=[topic], n_results=1)
        
        documents = results.get('documents', [[]])
        distances = results.get('distances', [[]])
        
        if not documents or not documents[0]:
            return None, False
            
        context = documents[0][0]
        if distances[0]:
            distance = distances[0][0]
        else:
            distance = 0.0
        
        # If distance score is too wide, the source material does not support the topic
        if distance > 1.2:
            return context, False
            
        return context, True
