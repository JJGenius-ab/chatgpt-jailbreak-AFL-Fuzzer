# from sentence_transformers import SentenceTransformer, util
from sentence_transformers import SentenceTransformer

class CosineDriftClassifier:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", drift_threshold: float = 0.25):
        self.model = SentenceTransformer(model_name)
        self.drift_threshold = drift_threshold

    def get_similarity(self, s1: str, s2: str) -> float:
        embeddings = self.model.encode([s1, s2], convert_to_tensor=True)
        return util.cos_sim(embeddings[0], embeddings[1]).item()

    def has_significant_drift(self, orig_resp: str, parent_resp: str, mutated_resp: str) -> tuple[bool, float, float]:
        """
        Returns (is_drifted, sim_vs_seed, sim_vs_parent)
        Drift occurs only if response is significantly different from BOTH seed and parent.
        """
        sim_vs_seed = self.get_similarity(orig_resp, mutated_resp)
        sim_vs_parent = self.get_similarity(parent_resp, mutated_resp)

        drift_vs_seed = (1 - sim_vs_seed) > self.drift_threshold
        drift_vs_parent = (1 - sim_vs_parent) > self.drift_threshold

        return (drift_vs_seed and drift_vs_parent), sim_vs_seed, sim_vs_parent
