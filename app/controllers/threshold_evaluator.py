"""
This  file contains the applications API
authors: Erin Hwang
"""
import numpy as np
import argparse
import json
import os
import pprint
from pathlib import Path
import requests
import warnings

from dotenv import load_dotenv

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances, manhattan_distances
from app.utils.logger import LoggerConfig

TRANSFORMER_MODEL = os.getenv("TRANSFORMER_MODEL")

def soft_cosine_similarity(embedding1, embedding2):
    """
    Calculate the Soft Cosine Similarity between two embeddings.

    Parameters:
        embedding1 (array-like): First sentence embedding.
        embedding2 (array-like): Second sentence embedding.
        similarity_matrix (2D array, optional): Precomputed feature similarity matrix.
            If None, default to identity matrix (no feature similarity).

    Returns:
        float: Soft Cosine Similarity score.
    """
    combined_embeddings = np.vstack([embedding1, embedding2])

    feature_vectors = combined_embeddings.T
    similarity_matrix = cosine_similarity(feature_vectors)

    # Convert inputs to numpy arrays for matrix operations
    e1 = np.array(embedding1).flatten()
    e2 = np.array(embedding2).flatten()

    # Compute the numerator: e1.T * S * e2
    numerator = np.dot(np.dot(e1, similarity_matrix), e2)

    # Compute the denominator: sqrt(e1.T * S * e1) * sqrt(e2.T * S * e2)
    denominator = (
        np.sqrt(np.dot(np.dot(e1, similarity_matrix), e1)) *
        np.sqrt(np.dot(np.dot(e2, similarity_matrix), e2))
    )


    # Return the similarity score (handle edge case for zero denominator)
    return numerator / denominator if denominator != 0 else 0

class SemanticSimilarityEvaluator:
    #TODO: add docstrings
    def __init__(
        self,
        transformer_model: str = TRANSFORMER_MODEL,

    ):
        self.logger = LoggerConfig().get_logger(__name__)

        # load transformer model
        self.sentence_transformer = SentenceTransformer(transformer_model)



    def semantic_search(self, resume_str:str, job_str:str):
        """
        Performs semantic search based on cosine similarity of embeddings.
        """

        # encode the sql query or NL representation of the query
        resume_embedding = self.sentence_transformer.encode([resume_str])
        job_embedding = self.sentence_transformer.encode([job_str])

        # calculate cosine sim
        # TODO: possibly explore other similarity metrics (L1, L2, jaccard)
        self.logger.info("Calculating cosine similarity...")
        cos_score = cosine_similarity(resume_embedding, job_embedding).flatten()[0]
        # euc_score = euclidean_distances(resume_embedding, job_embedding).flatten()[0]
        # man_score = manhattan_distances(resume_embedding, job_embedding).flatten()[0]
        soft_cos_score = soft_cosine_similarity(resume_embedding, job_embedding)

        return {
            "cosine_similarity": cos_score,
            "soft_cosine_similarity": soft_cos_score,
            # "euclidean_norm": normalized_euc_score,
            # "manhattan_norm": normalized_man_score
            }

    def process(self, resume_str: str, job_str: str, ):
        """
        Main method to run the semantic search either using given SQL query or its natural
        language equivalent using granite-code-instruct
        """
        # turn list of CHG descriptions to embeddings
        ss_response = self.semantic_search(resume_str, job_str)
        self.logger.info("Semantic similarity completed: cosine similarity score is:%s", ss_response)
        return ss_response


