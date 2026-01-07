(define (problem hh-p1)
  (:domain heaven-hell)

  (:objects
    loc-start loc-priest loc-door1 loc-door2 - location
    d-heaven d-hell - door
    p1 - priest
  )

  (:init
    (at-location loc-start)
    (door-at d-heaven loc-door1)
    (door-at d-hell loc-door2)
    (priest-at p1 loc-priest)
    (is-heaven d-heaven)
    (is-hell d-hell)
    (has-answer p1)
  )

  (:goal (and
    (in-heaven)
  ))
)
