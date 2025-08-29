# Class to interact with the LLM
import openai
from pddl_planner.pddl_core.action import Action
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
        self._n_iter = 3 # number of iterations for the entailment check for self consistency check
        self._operations = Operations()
        self._verbose = verbose

    def entailment(self, predicate: NLPredicate, predicates: List[NLPredicate], background_predicates: Tuple[Action, List[NLPredicate]] = (None, [])) -> NLPredicate|None:
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
        print(f'[Info] Checking entailment via cache/LLM for "{predicate.nl_description}"') if self._verbose else None
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

            # Before substitution, extend substitution by unifying with all action clauses (if any)
            extended_substitution = substitution
            try:
                if isinstance(background_predicates, tuple) and len(background_predicates) == 2:
                    action_ctx, _ = background_predicates
                    if action_ctx is not None:
                        # Unify with preconditions
                        for clause in getattr(action_ctx.preconditions, 'clauses', []):
                            if isinstance(clause, NLPredicate):
                                tmp = self._operations.unify_with_different_name(predicate_copy, clause, copy.deepcopy(extended_substitution))
                                if tmp is not None:
                                    extended_substitution = tmp
                                tmp = self._operations.unify_with_different_name(pred_copy, clause, copy.deepcopy(extended_substitution))
                                if tmp is not None:
                                    extended_substitution = tmp
                        # Unify with effects
                        for clause in getattr(action_ctx.effects, 'clauses', []):
                            if isinstance(clause, NLPredicate):
                                tmp = self._operations.unify_with_different_name(predicate_copy, clause, copy.deepcopy(extended_substitution))
                                if tmp is not None:
                                    extended_substitution = tmp
                                tmp = self._operations.unify_with_different_name(pred_copy, clause, copy.deepcopy(extended_substitution))
                                if tmp is not None:
                                    extended_substitution = tmp
            except Exception:
                pass
            # Apply extended substitution to both predicates to get their substituted string representations
            substituted_target = predicate_copy.substitute(extended_substitution)
            substituted_pred = pred_copy.substitute(extended_substitution)

            # Apply the same substitution to the background action (if provided)
            substituted_background = background_predicates
            try:
                if isinstance(background_predicates, tuple) and len(background_predicates) == 2:
                    action_ctx, bg_preds_ctx = background_predicates
                    if action_ctx is not None:
                        action_ctx_copy = copy.deepcopy(action_ctx)
                        action_ctx_copy = action_ctx_copy.substitute(extended_substitution)
                        substituted_background = (action_ctx_copy, bg_preds_ctx)
            except Exception:
                substituted_background = background_predicates

            
            # Conduct entailment between the substituted string representations
            target_str = substituted_target.nl_description
            pred_str = substituted_pred.nl_description

            if predicate_copy._is_neg:
                # reverse the entailment check for negative predicates
                entailment_result, response_text = self._entailment_check(pred_str, target_str, substituted_background)
            else:
                # conduct entailment check
                entailment_result, response_text = self._entailment_check(target_str, pred_str, substituted_background)

            if entailment_result:
                # if the predicate is entailed, update the cache
                print(f"[Success] Predicate {str(predicate)} is entailed by {pred.name} from LLM") if self._verbose else None
                entailed_preds.append(pred)
        if len(entailed_preds) == 1:
            # if there is only one entailed predicate, overwrite the original predicate's entailment with the entailed predicate
            predicate.entailed = entailed_preds[0]
            return predicate
        elif len(entailed_preds) > 1:
            # if there are multiple entailed predicates, return the list of entailed predicates
            predicate.entailed = entailed_preds
            return predicate
        else:
            # if there are no entailed predicates, return None
            print(f"[No Entailment] Failed: Predicate {predicate.nl_description} is not entailed by any of the predicates") if self._verbose else None
            return None

    def _entailment_check(self, target_str: str, pred_str: str, background_predicates: Tuple[Action, List[NLPredicate]] = (None, [])) -> Tuple[bool, str]:
        """
        Check if the target predicate is entailed by the candidate predicate.

        Args:
            target_str (str): The target predicate string representation.
            pred_str (str): The candidate predicate string representation.

        Returns:
            Tuple[bool, str]: The decision and the raw text from the LLM.
        """

        # Check cache first, then complete to n_iter with LLM calls and decide by self-consistency

        # 1) Parse cached responses (if any), then complete to n_iter using LLM, then decide
        cached_texts = self._get_cached_llm_responses(target_str, pred_str) or []
        normal_results: List[Tuple[Optional[bool], str]] = []
        # Parse existing cached responses (up to n_iter)
        for t in cached_texts[: self._n_iter]:
            decision, _ = self._parse_yes_no_response(t)
            normal_results.append((decision, t))
        # If we have fewer than n_iter cached, complete by querying LLM and updating cache
        missing = max(0, self._n_iter - len(cached_texts))
        last_text = ""
        for _ in range(missing):
            decision, text = self._get_llm_responses(target_str, pred_str, background_predicates)
            if text is not None:
                self._update_cache_llm_response(target_str, pred_str, text)
                last_text = text or last_text
            normal_results.append((decision, text or ""))
        print(f'[LLM Response] is "{target_str}" entailed by "{pred_str}" ?: {[result[0] for result in normal_results]}') if self._verbose else None
        majority_decision, majority_text = self._self_consistent_decision(normal_results)
        if majority_decision is not None:
            return bool(majority_decision), (majority_text or last_text)

        # Default to False if still ambiguous
        return False, last_text

    def _self_consistent_decision(self, results: List[Tuple[Optional[bool], str]]) -> Tuple[Optional[bool], str]:
        """
        Given a list of parsed (decision, text) tuples, return the majority decision and
        a representative text. Does not perform cache or LLM calls.

        Args:
            results (List[Tuple[Optional[bool], str]]): The list of parsed (decision, text) tuples.

        Returns:
            Tuple[Optional[bool], str]: The majority decision and a representative text.
        """
        yes_count = 0
        no_count = 0
        text_yes: Optional[str] = None
        text_no: Optional[str] = None
        last_text = ""
        for decision, text in results:
            if text:
                last_text = text
            if decision is None:
                continue
            if decision:
                yes_count += 1
                if text:
                    text_yes = text
            else:
                no_count += 1
                if text:
                    text_no = text
        if yes_count > no_count:
            return True, (text_yes or last_text)
        if no_count > yes_count:
            return False, (text_no or last_text)
        return None, last_text

    def _get_llm_responses(self, target_str: str, pred_str: str, background_predicates: Tuple[Action, List[NLPredicate]] = (None, []),
                            max_retries: int = 3, timeout: float = 30.0) -> Tuple[Optional[bool], str]:
        """
        Build the entailment prompt and call the chat API with retries.
        Returns (decision, raw_text).

        Args:
            target_str (str): The target predicate string representation.
            pred_str (str): The candidate predicate string representation.
            background_predicates (Tuple[Action, List[NLPredicate]]): The background predicates and action.
            max_retries (int): The maximum number of retries.
            timeout (float): The timeout for the LLM call.

        Returns:
            Tuple[Optional[bool], str]: The decision and the raw text from the LLM.
        """
        
        background_predicates_str = "\n ".join([f"- {pred.nl_description}" for pred in background_predicates[1]])
        if background_predicates[0] is not None:
            action = background_predicates[0]
            action_description = f"""
                {action.name} 
                with the following preconditions: {[clause.nl_description for clause in action.preconditions.clauses if isinstance(clause, NLPredicate)]}
                and the following effects: {[clause.nl_description for clause in action.effects.clauses if isinstance(clause, NLPredicate)]}
                """
        else:
            action_description = ""
        prompt = f"""
                You are a everyday agent that currently doing the following action: 
                {action_description}

                Task: 
                 - Think step by step and determine according to everyday commonsense does an object being Predicate 2 imply Predicate 1 when doing the action.

                Instructions:
                - Use the definition of the predicates to determine if Predicate 2 implies Predicate 1.
                - Predicate 1: "{target_str}"
                - Predicate 2: "{pred_str}"
                - Here are some background predicates that you can use to determine if Predicate 2 implies Predicate 1, 
                use these predicates to determine the type of the specific object Predicate 1 and Predicate 2 are referring to.
                {background_predicates_str}
                - When determing the entailment, consider the meaning of the Predicate 1 and Predicate 2 with the type of the specific object each referring to in the context of the action.
                
                Output format (STRICT):
                - Line 1: exactly YES or NO.
                - Line 2: Reason.

                Example of entailment:
                - The agent possesses POTATO implies the agent holds POTATO
                - POTATO is in the sink implies POTATO is in the sink
                - POTATO is baked implies POTATO is cooked

                Response:"""
        last_error: Optional[Exception] = None
        for attempt in range(max_retries):
            try:
                client = self.client.with_options(timeout=timeout)
                response = client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                )
                return self._parse_yes_no_response(response.choices[0].message.content.strip())
            except Exception as err:
                last_error = err
                wait_seconds = (2 ** attempt) + random.uniform(0, 0.5)
                print(f"[Retry] LLM call failed (attempt {attempt + 1}/{max_retries}): {err}. Waiting {wait_seconds:.2f}s") if self._verbose else None
                time.sleep(wait_seconds)
        print(f"[Error] LLM call failed after {max_retries} attempts: {last_error}") if self._verbose else None
        return None, ""

    def _get_cached_llm_responses(self, target_str: str, candidate_pred_nl: str) -> Optional[List[str]]:
        """
        Retrieve cached raw LLM response texts (list) for the given NL pair if available.

        Args:
            target_str (str): The target predicate string representation.
            candidate_pred_nl (str): The candidate predicate string representation.

        Returns:
            Optional[List[str]]: The cached raw LLM response texts.
        """
        # load the current cache to up to date version
        self._cache = self._load_cache()
        if target_str in self._cache and isinstance(self._cache[target_str], dict):
            val = self._cache[target_str].get(candidate_pred_nl)
            if isinstance(val, list):
                return val
            if isinstance(val, str):
                # Backward-compat: single string stored before switch to list
                return [val]
        return None
    
    def _load_cache(self) -> Dict[str, str]:
        """
        Load the cache from the file.

        Args:
            target_str (str): The target predicate string representation.
            candidate_pred_nl (str): The candidate predicate string representation.

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
        

    def _load_cache_entailment(self, predicate: NLPredicate, predicates: List[NLPredicate]) -> Tuple[bool, NLPredicate|List[NLPredicate]|None]:
        """
        (Legacy) Cache the entailment of the predicate by the predicates.
        """
        #check if cache is loaded
        if self._cache is not None:
            # check if the predicate string representation is in the cache of previous entailments
            predicate_str = predicate.nl_description
            if predicate_str in self._cache:
                print(f'found the predicate "{predicate_str}" in the cache') if self._verbose else None
                cached_value = self._cache[predicate_str]
                # New schema: dict of pred_name -> raw_response_text
                if isinstance(cached_value, dict):
                    entailed_preds: List[NLPredicate] = []
                    for pred in predicates:
                        if pred.name in cached_value:
                            decision, _ = self._parse_yes_no_response(cached_value[pred.name])
                            if decision is True:
                                entailed_preds.append(copy.deepcopy(pred))
                    if len(entailed_preds) == 1:
                        return True, entailed_preds[0]
                    if len(entailed_preds) > 1:
                        return True, entailed_preds
                    # We have cached responses but none entailed
                    return True, None
                # Backward compatibility: old schema
                entailed_pred_name = cached_value
                if entailed_pred_name is None:
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

    def _update_cache_llm_response(self, target_str: str, candidate_pred_nl: str, response_text: str) -> None:
        """
        Update cache with raw LLM response for a specific target and candidate predicate pair.
        Cache schema: cache[target_str][candidate_pred_nl] = List[str]

        Args:
            target_str (str): The target predicate string representation.
            candidate_pred_nl (str): The candidate predicate string representation.
            response_text (str): The raw LLM response text.
        """
        # Initialize mapping for target_str if absent or not a dict
        if target_str not in self._cache or not isinstance(self._cache[target_str], dict):
            self._cache[target_str] = {}
        if candidate_pred_nl not in self._cache[target_str] or not isinstance(self._cache[target_str][candidate_pred_nl], list):
            self._cache[target_str][candidate_pred_nl] = []
        self._cache[target_str][candidate_pred_nl].append(response_text)
        self._save_cache()


    def _parse_yes_no_response(self, text: str) -> Tuple[Optional[bool], str]:
        """
        Parse a chain-of-thought style response and extract a YES/NO decision.

        Strategy:
        - Prefer the last explicit 'Response:' line if present.
        - Then check the last non-empty sentence/line.
        - Then check the first non-empty sentence/line.
        - Finally, fallback to whole-text heuristic if unambiguous.

        Returns (decision, original_text) where decision is True/False or None if undecidable.
        """
        if text is None:
            return None, ""
        original_text = text
        normalized_all = text.strip()
        if not normalized_all:
            return None, original_text

        def to_upper_clean(s: str) -> str:
            return s.strip().upper().strip(":,.!;()[]{}\n\t ")

        lines = [ln for ln in (ln.strip() for ln in normalized_all.splitlines()) if ln]

        # 1) Prefer explicit 'Response:' lines
        for ln in reversed(lines):
            if ln.upper().startswith("RESPONSE:"):
                answer_raw = ln.split(":", 1)[1] if ":" in ln else ln[9:]
                answer = to_upper_clean(answer_raw)
                if answer.startswith("YES"):
                    return True, original_text
                if answer.startswith("NO"):
                    return False, original_text

        # Helper to split into sentences conservatively
        def split_sentences(block: str) -> List[str]:
            parts: List[str] = []
            buf = ""
            for ch in block:
                buf += ch
                if ch in ".!?\n":
                    if buf.strip():
                        parts.append(buf.strip())
                    buf = ""
            if buf.strip():
                parts.append(buf.strip())
            return parts

        sentences = split_sentences(normalized_all)
        last_sentence = to_upper_clean(sentences[-1]) if sentences else ""
        first_sentence = to_upper_clean(sentences[0]) if sentences else ""

        # 2) Check last sentence
        if last_sentence.startswith("YES"):
            return True, original_text
        if last_sentence.startswith("NO"):
            return False, original_text

        # 3) Check first sentence
        if first_sentence.startswith("YES"):
            return True, original_text
        if first_sentence.startswith("NO"):
            return False, original_text

        # 4) Fallback heuristic on full text only if unambiguous
        upper_all = normalized_all.upper()
        has_yes = "YES" in upper_all
        has_no = "NO" in upper_all
        if has_yes and not has_no:
            return True, original_text
        if has_no and not has_yes:
            return False, original_text

        return None, original_text
    
    def _save_cache(self) -> None:
        """
        Save the cache to the file based on the provided cache path.
        """
        with open(self._cache_path, 'w') as f:
            json.dump(self._cache, f, indent=2)

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