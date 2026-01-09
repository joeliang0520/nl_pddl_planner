
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
    ;(has-answer ?p - priest)
    ;(is-heaven ?d - door)
    ;(is-hell ?d - door)         
    ;(in-heaven)                      
    ;(in-hell)
    ;(door-at ?d - door ?loc - location)
    ;(priest-at ?p - priest ?loc - location)
    ;(at-location ?loc -location)
    ; knowledge fluents   
    (k-has-answer ?p - priest)
    (k-not-has-answer ?p - priest)
    (k-is-heaven ?d - door)
    (k-not-is-heaven ?d - door)
    ;(k-is-hell ?d - door)         
    (k-in-heaven)
    (k-not-in-heaven) 
    ;(k-in-hell)
    (k-door-at ?d - door ?loc - location)
    (k-not-door-at ?d - door ?loc - location)
    (k-priest-at ?p - priest ?loc - location)
    (k-not-priest-at ?p - priest ?loc - location)
    (k-at-location ?loc -location)
    (k-not-at-location ?loc -location)
  )
  ; world actions
  (:action goto-location
    :parameters (?loc1 - location ?loc2 - location)
    :precondition (and
        (k-not-at-location ?loc2)
        (k-at-location ?loc1)
    )
    :effect (and 
        (k-not-at-location ?loc1) 
        (k-at-location ?loc2)
    )
  )



 

)
