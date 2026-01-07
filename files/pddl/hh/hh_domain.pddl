
(define (domain heaven-hell)
  (:requirements
    :strips
    :typing
    :conditional-effects
    :disjunctive-preconditions
    :derived-predicates
  )

  (:types location priest door)

  (:predicates
    ; world fluents       
    (has-answer ?p - priest)
    (is-heaven ?d - door)
    (is-hell ?d - door)         
    (in-heaven)                      
    (in-hell)
    (agent-at ?loc - location)
    (door-at ?d - door ?loc - location)
    (priest-at ?p - priest ?loc - location)
    (at-location ?loc -location)
    ; knowledge fluents   
    (k-has-answer ?p - priest)
    (k-is-heaven ?d - door)
    (k-is-hell ?d - door)         
    (k-in-heaven)                      
    (k-in-hell)
    (k-agent-at ?loc - location)
    (k-door-at ?d - door ?loc - location)
    (k-priest-at ?p - priest ?loc - location)
    (k-at-location ?loc -location)
  )
  ; world actions
  (:action goto-location
    :parameters (?loc1 - location ?loc2 - location)
    :precondition (and
        (at-location ?loc1)
        (not (at-location ?loc2))
    )
    :effect (and 
        (not (at-location ?loc1)) 
        (at-location ?loc2)
    )
  )
  (:action open-door-heaven
    :parameters (?door - door ?loc - location)
    :precondition (and
        (at-location ?loc)
        (door-at ?door ?loc)
        (is-heaven ?door)
        (k-is-heaven ?door)
    )
    :effect (and 
        (in-heaven)
    )
  )

  (:action open-door-hell
    :parameters (?door - door ?loc - location)
    :precondition (and
        (at-location ?loc)
        (door-at ?door ?loc)
        (is-hell ?door)
        (k-is-hell ?door)
    )
    :effect (and 
        (in-hell)
    )
  )

  (:action ask-preist-heaven
    :parameters (?p - priest ?d - door ?loc - location)
    :precondition (and
        (at-location ?loc)
        (priest-at ?p ?loc)
        (has-answer ?p)
        (is-heaven ?d)
    )
    :effect (and 
        (k-is-heaven ?d)
    )
  )

  (:action ask-preist-hell
    :parameters (?p - priest ?d - door ?loc - location)
    :precondition (and
        (at-location ?loc)
        (priest-at ?p ?loc)
        (has-answer ?p)
        (is-hell ?d)
    )
    :effect (and 
        (k-is-hell ?d)
    )
  )
 

)
