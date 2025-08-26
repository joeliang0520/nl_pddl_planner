# Class to interact with the LLM
import openai
from pddl_planner.logic.formula import Substitution
from pddl_planner.logic.nl_formula import NLPredicate
from pddl_planner.logic.operation import Operations
from typing import List, Dict, Tuple, Optional
import json
import copy
import time
import random

class LLM:
    """
    A class to intilize and interact with the LLM for various task in the regression planner.
    """
    
    def __init__(self, model_name: str, api_key: str, cache_path: str|None ='cache.json', verbose: bool = True):
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
        self._operations = Operations()
        self._verbose = verbose

    def replace_predicate_name(self, target_predicate: NLPredicate, entailed_predicate: NLPredicate) -> NLPredicate:
        """
        Replace the name of the target predicate with the name of the entailed predicate,
        while keeping all terms the same as the original target predicate.
        
        Args:
            target_predicate (NLPredicate): The target predicate whose name will be replaced.
            entailed_predicate (NLPredicate): The entailed predicate whose name will be used.
            
        Returns:
            NLPredicate: A new predicate with the entailed predicate's name but target predicate's terms.
        """
        # Create a deep copy of the target predicate to avoid modifying the original
        target_copy = copy.deepcopy(target_predicate)
        entailed_predicate_copy = copy.deepcopy(entailed_predicate)
        # Get the original string representation
        original_str_rep = str(target_copy)
        
        # Replace the target predicate name with the entailed predicate name in the string representation
        # This handles cases where the name might appear multiple times or in different contexts
        updated_str_rep = original_str_rep.replace(target_copy.name, entailed_predicate.name)

        #perform substitution on the entailed_predicate
        substitution = self._operations.unify_with_different_name(target_copy, entailed_predicate_copy, Substitution())
        if substitution is not None:
            entailed_predicate_copy = entailed_predicate_copy.substitute(substitution)
        
        # Create a new NLPredicate with the entailed predicate's name but target predicate's terms
        new_predicate = NLPredicate(
            entailed_predicate_copy.name,
            updated_str_rep,
            target_copy._is_neg,
            *target_copy.terms,
            term_type_dict=entailed_predicate_copy.term_type_dict,
            entailed_by=entailed_predicate_copy
        )
        
        return new_predicate

    def entailment(self, predicate: NLPredicate, predicates: List[NLPredicate]) -> NLPredicate|None:
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
            if entailed_predicate is not None:
                print(f"[Success] Predicate {predicate.nl_description} is entailed by {entailed_predicate.nl_description} from cache") if self._verbose else None
                # Replace the target predicate's name with the entailed predicate's name
                predicate.entailed = entailed_predicate
                return predicate
            else:
                print(f"[No Entailment] Predicate {predicate.nl_description} is not entailed by any of the predicates based on the cache") if self._verbose else None
            return None
        
        # if the cache is not loaded, or the predicate is not in the cache, or none of input predicates matches the entailed predicates in the cache
        # check if the predicate can be entailed by any of the predicates
        print(f'[Not Found] Failed to find the predicate "{predicate.nl_description}" in the cache, checking via LLM') if self._verbose else None
        entailed_preds = []
        for pred in predicates:
            # Create deep copies to prevent modifications to original objects
            predicate_copy = copy.deepcopy(predicate)
            pred_copy = copy.deepcopy(pred)

            # Find proper substitution between the target predicate and the current predicate
            # Use unify_with_different_name for entailment tasks to allow different predicate names
            substitution = self._operations.unify_with_different_name(predicate_copy, pred_copy, Substitution())
            if substitution is None:
                continue

            print(f'[Substitution] Existing substitution: {substitution} between "{str(predicate_copy)}" and "{str(pred_copy)}"') if self._verbose else None
            # Apply substitution to both predicates to get their substituted string representations
            substituted_target = predicate_copy.substitute(substitution)
            substituted_pred = pred_copy.substitute(substitution)

            # Conduct entailment between the substituted string representations
            target_str = substituted_target.nl_description
            pred_str = substituted_pred.nl_description

            if predicate_copy._is_neg:
                # reverse the entailment check for negative predicates
                entailment_result = self._entailment_check(pred_str, target_str)
            else:
                # conduct entailment check
                entailment_result = self._entailment_check(target_str, pred_str)

            if entailment_result:
                # if the predicate is entailed, update the cache
                print(f"[Success] Predicate {str(predicate)} is entailed by {pred.name} from LLM") if self._verbose else None
                entailed_preds.append(pred)
        if len(entailed_preds) == 1:
            # if there is only one entailed predicate, overwrite the original predicate's entailment with the entailed predicate
            predicate.entailed = entailed_preds[0]
            self._update_cache_entailment(predicate, entailed_preds[0])
            return predicate
        elif len(entailed_preds) > 1:
            # if there are multiple entailed predicates, return the list of entailed predicates
            predicate.entailed = entailed_preds
            self._update_cache_entailment(predicate, entailed_preds)
            return predicate
        else:
            # if there are no entailed predicates, return None
            print(f"[No Entailment] Failed: Predicate {predicate.nl_description} is not entailed by any of the predicates") if self._verbose else None
            self._update_cache_entailment(predicate, None)
            return None

    def _entailment_check(self, target_str: str, pred_str: str) -> bool:
        # Professional prompt for entailment checking
        prompt = f"""Task: Determine if two predicates are logically equivalent or if one entails the other.

                Predicate 1: "{target_str}"
                Predicate 2: "{pred_str}"

                Instructions:
                - Analyze if Predicate 1 is logically entailed by Predicate 2
                - Consider semantic meaning, logical structure, and variable mappings
                - Respond with exactly "YES" if Predicate 1 is entailed by Predicate 2
                - Respond with exactly "NO" if Predicate 1 is not entailed by Predicate 2

                Response:"""

        decision = self._call_llm_with_retries(prompt)
        if decision is not None:
            print(f'[LLM Response] predicate "{target_str}" is entailed by "{pred_str}" ?:  {decision}') if self._verbose else None
            return decision

        # Last attempt: ask for a strictly formatted answer if parsing failed
        print('[Strict Response]: Failed to parse the response, asking for a strictly formatted answer') if self._verbose else None
        strict_prompt = (
            prompt
            + "\n\nAnswer strictly with ONLY YES or NO, no punctuation, no explanation."
        )
        decision = self._call_llm_with_retries(strict_prompt)
        print(f'[LLM Response] predicate "{target_str}" is entailed by "{pred_str}" ?:  {decision}') if self._verbose else None

        # Default to False if still ambiguous
        return bool(decision) if decision is not None else False

    def _parse_yes_no_response(self, text: str) -> Optional[bool]:
        """
        Parse a free-form model response and extract a YES/NO decision.

        Returns True for YES, False for NO, or None if undecidable.
        """
        if text is None:
            return None
        normalized = text.strip().upper()
        if not normalized:
            return None
        # Check the first token/word primarily
        first_token = normalized.split()[0].strip().strip(":,.!;()[]{}\n\t")
        if first_token == 'YES':
            return True
        if first_token == 'NO':
            return False
        # Fallback: substring search if first token parsing fails
        if 'YES' in normalized and 'NO' not in normalized:
            return True
        if 'NO' in normalized and 'YES' not in normalized:
            return False
        raise ValueError(f"Invalid response: {text}")

    def _call_llm_with_retries(self, prompt: str, max_retries: int = 3, timeout: float = 30.0) -> str:
        """
        Call the chat completion API with retries, exponential backoff, and jitter.
        """
        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                client = self.client.with_options(timeout=timeout)
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                )
                return self._parse_yes_no_response(response.choices[0].message.content.strip())
            except Exception as err:  # Broad catch to keep planner robust
                last_error = err
                wait_seconds = (2 ** attempt) + random.uniform(0, 0.5)
                print(f"[Retry] LLM call failed (attempt {attempt + 1}/{max_retries}): {err}. Waiting {wait_seconds:.2f}s") if self._verbose else None
                time.sleep(wait_seconds)
        # After retries, surface a best-effort empty string to be handled by parser
        print(f"[Error] LLM call failed after {max_retries} attempts: {last_error}") if self._verbose else None
        return None
    
    def _load_cache(self) -> Dict[str, str]:
        """
        Load the cache from the file.

        Returns:
            Dict[str, str]: The cache of previous entailments.
        """
        if self._cache_path is not None:
            # if the cache path is provided, load the cache from the file
            try:
                with open(self._cache_path, 'r') as f:
                    self._cache = json.load(f)
            except FileNotFoundError:
                self._cache = {}
                self._cache_path = 'cache.json'
                self._save_cache()
        else:
            # if the cache path is not provided, create a new cache
            self._cache = {}
            self._cache_path = 'cache.json'
            self._save_cache()
        return self._cache
        

    def _load_cache_entailment(self, predicate: NLPredicate, predicates: List[NLPredicate]) -> Tuple[bool, NLPredicate|None]:
        """
        Cache the entailment of the predicate by the predicates.
        """
        #check if cache is loaded
        if self._cache is not None:
            # check if the predicate string representation is in the cache of previous entailments
            predicate_str = predicate.nl_description
            if predicate_str in self._cache:
                print(f'found the predicate "{predicate_str}" in the cache') if self._verbose else None
                # obtained the name of the entailed predicate from the cache
                entailed_pred_name = self._cache[predicate_str]
                if entailed_pred_name is None:
                    # if no entailment is found in the cache, return True and None
                    return True, None
                if isinstance(entailed_pred_name, list):
                    entailed_preds = []
                    for entailed_pred in entailed_pred_name:
                        for pred in predicates:
                            if pred.name == entailed_pred:
                                entailed_preds.append(copy.deepcopy(pred))
                    return True, entailed_preds
                else:
                    for pred in predicates:
                        if pred.name == entailed_pred_name:
                            return True, copy.deepcopy(pred)
        # if the cache is not loaded, return False and None
        return False, None

    def _update_cache_entailment(self, target_predicate: NLPredicate, entailed_predicate: NLPredicate|List[NLPredicate]|None) -> None:
        """
        Update the cache with the entailment of the target predicate by the entailed predicate.

        Args:
            target_predicate (Predicate): The target predicate to be updated in the cache.
            entailed_predicate (Predicate): The entailed predicate that is used to update the cache.
        """
        target_str = target_predicate.nl_description
        entailed_name = entailed_predicate.name if entailed_predicate is not None else None
        self._cache[target_str] = entailed_name
        self._save_cache()
    
    def _save_cache(self) -> None:
        """
        Save the cache to the file based on the provided cache path.
        """
        with open(self._cache_path, 'w') as f:
            json.dump(self._cache, f)

    