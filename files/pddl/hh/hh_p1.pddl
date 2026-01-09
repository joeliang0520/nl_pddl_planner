(define (problem hh-p1)
  (:domain heaven-hell)

  (:objects
    loc-start loc-priest loc-door1 loc-door2 - location
    d-heaven d-hell - door
    p1 - priest
  )

  (:init
    (k-at-location loc-start)
    (k-door-at d-heaven loc-door1)
    (k-door-at d-hell loc-door2)
    (k-priest-at p1 loc-priest)

    (k-is-heaven d-heaven)
    (k-is-hell d-hell)

    (k-has-answer p1)
  )

  (:goal (and
    ;(k-at-location loc-priest)
    (k-in-heaven)
  ))
)
