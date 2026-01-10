(define (domain heaven-hell)
  (:requirements :strips :typing :conditional-effects)

  (:types location priest door)

  (:predicates
    (k-has-answer ?p - priest)
    (k-not-has-answer ?p - priest)
    (u-has-answer ?p - priest)

    (k-is-heaven ?d - door)
    (k-not-is-heaven ?d - door)
    (u-is-heaven ?d - door)

    (k-is-hell ?d - door)
    (k-not-is-hell ?d - door)
    (u-is-hell ?d - door)       

    (k-in-heaven)
    (k-not-in-heaven)
    (u-in-heaven)

    (k-door-at ?d - door ?loc - location)
    (k-not-door-at ?d - door ?loc - location)
    (u-door-at ?d - door ?loc - location)

    (k-priest-at ?p - priest ?loc - location)
    (k-not-priest-at ?p - priest ?loc - location)
    (u-priest-at ?p - priest ?loc - location)

    (k-at-location ?loc - location)
    (k-not-at-location ?loc - location)
    (u-at-location ?loc - location)
  )

  (:action goto-location
    :parameters (?loc1 - location ?loc2 - location)
    :precondition (and
      (k-at-location ?loc1)
    )
    :effect (and
      (k-not-at-location ?loc1)
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
      (k-in-heaven)
    )
  )

  (:action ask-priest-heaven
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


  (:action ask-preist-knows-true
    :parameters (?p - priest ?loc - location)
    :precondition (and
        (k-at-location ?loc)
        (k-priest-at ?p ?loc)
        (u-has-answer ?p)
    )
    :effect (and 
        (k-has-answer ?p)
    )
  )


)
