import asyncio

try:
    from sentence_transformers import SentenceTransformer, util
except ImportError:
    SentenceTransformer = None
    util = None

class CosineDriftClassifier:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2", drift_threshold: float = 0.25):
        self.model_name = model_name
        self.model = None
        self.drift_threshold = drift_threshold

    def _get_model(self):
        if SentenceTransformer is None or util is None:
            raise RuntimeError(
                "sentence-transformers and torch are required for drift detection. "
                "Install dependencies from requirements.txt."
            )
        if self.model is None:
            self.model = SentenceTransformer(self.model_name)
        return self.model

    def get_similarity(self, s1: str, s2: str) -> float:
        model = self._get_model()
        embeddings = model.encode([s1 or "", s2 or ""], convert_to_tensor=True)
        return util.cos_sim(embeddings[0], embeddings[1]).item()

    def is_drifted(self, original_response: str, mutated_response: str) -> tuple[bool, float]:
        similarity = self.get_similarity(original_response, mutated_response)
        return (1 - similarity) > self.drift_threshold, similarity

    async def async_is_drifted(self, original_response: str, mutated_response: str) -> tuple[bool, float]:
        return await asyncio.to_thread(self.is_drifted, original_response, mutated_response)

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
