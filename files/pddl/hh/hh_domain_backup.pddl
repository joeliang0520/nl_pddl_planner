
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
        (k-at-location ?loc1)
    )
    :effect (and 
        (not (k-at-location ?loc1)) 
        (k-at-location ?loc2)
    )
  )
  (:action open-door-heaven
    :parameters (?door - door ?loc - location)
    :precondition (and
        (k-at-location ?loc)
        (k-door-at ?door ?loc)
        (k-is-heaven ?door)
    )
    :effect (and 
        (in-heaven)
    )
  )

  (:action open-door-hell
    :parameters (?door - door ?loc - location)
    :precondition (and
        (k-at-location ?loc)
        (k-door-at ?door ?loc)
        (k-is-hell ?door)
    )
    :effect (and 
        (in-hell)
    )
  )

  (:action ask-preist-knows-true
    :parameters (?p - priest ?loc - location)
    :precondition (and
        (k-at-location ?loc)
        (k-priest-at ?p ?loc)
    )
    :effect (and 
        (k-has-answer ?p)
    )
  )

  (:action ask-preist-knows-false
    :parameters (?p - priest ?loc - location)
    :precondition (and
        (k-at-location ?loc)
        (k-priest-at ?p ?loc)
    )
    :effect (and 
        (not (k-has-answer ?p))
    )
  )

  (:action ask-preist-heaven
    :parameters (?p - priest ?d - door ?loc - location)
    :precondition (and
        (k-at-location ?loc)
        (k-priest-at ?p ?loc)
        (k-has-answer ?p)
    )
    :effect (and 
        (k-is-heaven ?d)
    )
  )
 

)
