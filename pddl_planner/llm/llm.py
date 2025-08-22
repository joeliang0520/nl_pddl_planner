# Class to interact with the LLM
import openai
from pddl_planner.logic.formula import Predicate
from typing import List, Dict, Tuple
import json
import copy

class LLM:
    """
    A class to intilize and interact with the LLM for various task in the regression planner.
    """
    
    def __init__(self, model_name: str, api_key: str, cache_path: str|None = None):
        """
        Initialize the LLM.

        Args:
            model_name (str): The name of the model to use.
            api_key (str): The API key to use.
            cache_path (str|None): The path to the cache file.
        """
        self.model_name = model_name
        self._api_key = api_key
        self._cache_path = cache_path
        self._cache = self._load_cache()
        self.client = openai.OpenAI(api_key=api_key)

    def entailment(self, predicate: Predicate, predicates: List[Predicate]) -> Predicate|None:
        """
        Check if the predicate can be entailed as a one of the list of predicates.

        Args:
            predicate (Predicate): The predicate to check for possible entailment.
            predicates (List[Predicate]): The list of predicates that are available for entailment.

        Returns:
            Predicate: The predicate that can be entailed as a one of the list of predicates.
            None: If the predicate cannot be entailed as a one of the list of predicates.
        """
        # update current cache
        self._cache = self._load_cache()
        # check if the predicate is in the cache of previous entailments
        status, entailed_predicate = self._load_cache_entailment(predicate, predicates)
        if status:
            # if the predicate is in the cache, return the entailed predicate
            print(f"Success: Predicate {predicate} is entailed by {entailed_predicate.name} from cache")
            return entailed_predicate
        # if the cache is not loaded, or the predicate is not in the cache, or non of input predicates matches the enitaled predicates in the cache
        # check if the predicate can be entailed by any of the predicates
        for pred in predicates:
            pred_name = pred.name
            # currently this is a very simple prompt, but we can improve it by using a more complex prompt or rating
            prompt = f"is the predicate {predicate} entailed or share the same meaning as the {pred_name}? return 'yes' if it is, 'no' if it is not."
            response = self.client.chat.completions.create(model=self.model_name, messages=[{"role": "user", "content": prompt}])
            print(f'predicate {predicate} is entailed by {pred_name}? {response.choices[0].message.content}')
            if response.choices[0].message.content == 'yes':
                # if the predicate is entailed, update the cache
                print(f"Success: Predicate {predicate} is entailed by {pred_name} from LLM")
                self._update_cache_entailment(predicate, pred)
                return copy.deepcopy(pred)
        # if the predicate is not entailed by any of the predicates, and not in the cache, return None  
        print(f"Failed: Predicate {predicate} is not entailed by any of the predicates")
        self._update_cache_entailment(predicate, None)
        return None
    
    def _load_cache(self) -> Dict[str, str]:
        """
        Load the cache from the file.

        Returns:
            Dict[str, str]: The cache of previous entailments.
        """
        if self._cache_path is not None:
            try:
                with open(self._cache_path, 'r') as f:
                    self._cache = json.load(f)
            except FileNotFoundError:
                print(f"Cache file not found at {self._cache_path}, creating new cache")
                self._cache = {}
                self._cache_path = 'cache.json'
                self._save_cache()
        else:
            self._cache = {}
            self._cache_path = 'cache.json'
            self._save_cache()
        return self._cache

    def _load_cache_entailment(self, predicate: Predicate, predicates: List[Predicate]) -> Tuple[bool, Predicate|None]:
        """
        Cache the entailment of the predicate by the predicates.
        """
        #check if cache is loaded
        if self._cache is not None:
            # check if the predicate is in the cache of previous entailments
            if predicate.name in self._cache:
                # obtained the name of the entailed predicate from the cache
                entailed_pred = self._cache[predicate.name]
                if entailed_pred is None:
                    # if no entailment is found in the cache, return True and None
                    return True, None 
                for pred in predicates:
                    # check the entailed predicate name with input list of predicates and return the predicate if it is found
                    if pred.name == entailed_pred:
                        # if the entailment is found, return True and the entailed predicate
                        return True, copy.deepcopy(pred)
        # if the cache is not loaded, return False and None
        return False, None

    def _update_cache_entailment(self, target_predicate: Predicate, entailed_predicate: Predicate|None) -> None:
        """
        Update the cache with the entailment of the target predicate by the entailed predicate.

        Args:
            target_predicate (Predicate): The target predicate to be updated in the cache.
            entailed_predicate (Predicate): The entailed predicate that is used to update the cache.
        """
        self._cache[target_predicate.name] = entailed_predicate.name if entailed_predicate is not None else None
        self._save_cache()
    
    def _save_cache(self) -> None:
        """
        Save the cache to the file based on the provided cache path.
        """
        with open(self._cache_path, 'w') as f:
            json.dump(self._cache, f)

